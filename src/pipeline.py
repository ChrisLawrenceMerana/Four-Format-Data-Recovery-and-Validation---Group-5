
"""Pipeline for four-format data recovery and validation."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import numpy as np
import shutil
import tempfile

from src.readers import (
    read_csv_records,
    read_excel_records,
)

from src.json_parquet_reader import (
    read_country_json,
    read_country_parquet,
)

from src.validation import validate_and_dedupe

from src.analysis import (
    asia_selected_year,
    asia_pop,
    country_history,
    population_matrix,
    calc_verification
)

from src.exporter import (
    export_and_verify,
    compare_frames,
)

from src.audit import add_audit, save_audit
from src.validation_report import add_check, save_validation
from src.rejection_report import save_record_report

CANONICAL_COLUMNS = [
    "country",
    "continent",
    "year",
    "lifeExp",
    "pop",
    "gdpPercap",
]

def build_rules(manifest:dict) -> dict:
    """Create validation rules using the manifest"""

    return {
        "allowed_years": set(
            manifest["allowed_years"]
        ),
        "allowed_continents": set(
            manifest["allowed_continents"]
        ),
        "ranges": {
            "lifeExp": (0.0, 120.0),
            "pop": (1, float("inf")),
            "gdpPercap": (0.0, float("inf")),
        },
    }

def verify_hash(
    file_path: Path,
    expected_hash: str
) -> None:
    """Check the SHA-256 hash of an original input file."""

    actual_hash = hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()

    if actual_hash.lower() != expected_hash.lower():
        raise ValueError(
            f"SHA-256 mismatch: {file_path.name}"
        )

def read_source(
    file_path: Path,
    settings: dict
) -> pd.DataFrame:
    """Read one input file and map columns to canonical names."""

    format_name = settings["format"]
    mapping = settings["source_to_canonical"]

    if format_name == "csv":

        raw_df = read_csv_records(
            file_path,
            encoding=settings["encoding"],
            delimiter=settings["separator"],
            comment_lines=2,
            column_mapping=mapping,
            drop_columns=settings.get(
                "ignore_columns", []
            ),
        )

    elif format_name == "xlsx":

        raw_df = read_excel_records(
            file_path,
            sheet_name=settings["sheet_name"],
            column_mapping=mapping,
        )

    elif format_name == "json":

        nested_df = read_country_json(
            file_path,
            settings
        )

        # Flatten identity and measures objects.
        raw_df = pd.json_normalize(
            nested_df.to_dict(orient="records")
        )

        raw_df = raw_df.rename(
            columns=mapping
        )

    elif format_name == "parquet":

        raw_df = read_country_parquet(
            file_path,
            settings
        )

        raw_df = raw_df.rename(
            columns=mapping
        )

    else:
        raise ValueError(
            f"Unsupported format: {format_name}"
        )

    # Check the six required canonical columns.
    missing = (
        set(CANONICAL_COLUMNS)
        - set(raw_df.columns)
    )

    if missing:
        raise ValueError(
            f"{file_path.name} is missing columns: "
            f"{sorted(missing)}"
        )

    # Preserve the original source record number.
    if "source_record" not in raw_df.columns:
        raw_df["source_record"] = range(
            1,
            len(raw_df) + 1
        )

    if "source_file" not in raw_df.columns:
        raw_df["source_file"] = file_path.name

    return raw_df[
        CANONICAL_COLUMNS
        + ["source_record", "source_file"]
    ]

def publish_staging(
    staging_dir: Path, 
    output_dir: Path
) -> None:
    """Publish verified results, restoring previous files on error."""

    staging_dir = staging_dir.resolve()
    output_dir = output_dir.resolve()

    output_dir.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    backup_dir = output_dir.with_name(
        output_dir.name + ".backup"
    )

    if backup_dir.exists():
        raise RuntimeError(
            f"Backup already exists: {backup_dir}"
        )

    previous_output_exists = output_dir.exists()

    if previous_output_exists:
        output_dir.rename(backup_dir)

    try:
        staging_dir.rename(output_dir)

    except Exception:
        if previous_output_exists and backup_dir.exists():
            backup_dir.rename(output_dir)
        raise

    if previous_output_exists:
        shutil.rmtree(backup_dir)

def _run_pipeline(
    config: dict,
    validation_results: list[dict],
) -> None:
    """Load and verify the four input datasets."""

    audit_log = []

    data_dir = Path(config["data_dir"])
    output_dir = Path(config["output_dir"])

    with open(
        config["manifest"],
        encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    reporting_year = config.get(
        "reporting_year",
        2007
    )

    print("Data directory:", data_dir)
    print("Output directory:", output_dir)
    print("Reporting year:", reporting_year)
    print()

    # Prepare validation rules.
    rules = build_rules(manifest)

    # Store the four cleaned DataFrames.
    canonical_tables = []

    # Store invalid and duplicate records.
    all_quarantined = []
    all_duplicates = []

    for settings in manifest["files"]:

        file_path = (
            data_dir / settings["file"]
        )

        print(f"Reading: {file_path.name}")

        # 1. Verify the original file.
        verify_hash(
            file_path,
            settings["sha256"]
        )

        print("SHA-256: PASS")

        # 2. Read and map its columns.
        raw_df = read_source(
            file_path,
            settings
        )

        # 3. Check its raw record count.
        expected_rows = settings["raw_records"]

        if len(raw_df) != expected_rows:
            raise ValueError(
                f"{file_path.name}: expected "
                f"{expected_rows} records, "
                f"found {len(raw_df)}"
            )

        print(f"Rows loaded: {len(raw_df)}")
        add_audit(
            audit_log,
            step="reading",
            source_file=file_path.name,
            operation="read_and_map",
            rule="SHA-256 verified; canonical columns mapped",
            rows_before=len(raw_df),
            rows_after=len(raw_df),
        )
        print("Column mapping: PASS")
        print()

        
        # Validate and remove exact duplicates.
        clean_df, validation_run = validate_and_dedupe(
            raw_df,
            file_path.name,
            rules
        )

        # Count the results.
        rejected_count = len(
            validation_run.quarantined
        )

        duplicate_count = len(
            validation_run.duplicates
        )

        clean_count = len(clean_df)

        # Expected values from the manifest.
        expected = manifest["expected_per_file"]

        if rejected_count != expected["rejected_rows"]:
            raise ValueError(
                f"{file_path.name}: expected "
                f"{expected['rejected_rows']} rejected rows, "
                f"found {rejected_count}"
            )

        if duplicate_count != expected["exact_duplicates_removed"]:
            raise ValueError(
                f"{file_path.name}: expected "
                f"{expected['exact_duplicates_removed']} duplicates, "
                f"found {duplicate_count}"
            )

        if clean_count != expected["canonical_rows"]:
            raise ValueError(
                f"{file_path.name}: expected "
                f"{expected['canonical_rows']} clean rows, "
                f"found {clean_count}"
            )

        if (
            len(raw_df) - rejected_count
            != expected["valid_before_deduplication"]
        ):
            raise ValueError(
                f"{file_path.name}: valid row count mismatch"
            )

        if not validation_run.reconciles():
            raise ValueError(
                f"{file_path.name}: reconciliation failed"
            )

        print(f"Quarantined: {rejected_count}")
        print(f"Duplicates removed: {duplicate_count}")
        print(f"Clean records: {clean_count}")
        add_check(
            validation_results,
            f"{file_path.name}: raw rows",
            settings["raw_records"],
            len(raw_df),
        )

        add_check(
            validation_results,
            f"{file_path.name}: rejected rows",
            expected["rejected_rows"],
            rejected_count,
        )

        add_check(
            validation_results,
            f"{file_path.name}: duplicates",
            expected["exact_duplicates_removed"],
            duplicate_count,
        )

        add_check(
            validation_results,
            f"{file_path.name}: canonical rows",
            expected["canonical_rows"],
            clean_count,
        )

        add_check(
            validation_results,
            f"{file_path.name}: reconciliation",
            True,
            validation_run.reconciles(),
        )
        print("Validation: PASS")
        add_audit(
            audit_log,
            step="validation",
            source_file=file_path.name,
            operation="quarantine_invalid",
            rule="Manifest schema and domain rules",
            rows_before=len(raw_df),
            rows_after=len(raw_df) - rejected_count,
        )

        add_audit(
            audit_log,
            step="deduplication",
            source_file=file_path.name,
            operation="remove_exact_duplicates",
            rule="Exact duplicate records removed",
            rows_before=len(raw_df) - rejected_count,
            rows_after=clean_count,
        )
        print()

        # Save cleaned data and validation details.
        canonical_tables.append(clean_df)

        all_quarantined.extend(
            validation_run.quarantined
        )

        all_duplicates.extend(
            validation_run.duplicates
        )

    
    print("All four formats validated successfully!")
    print(f"Datasets validated: {len(canonical_tables)}")

    print(
        f"Total quarantined: {len(all_quarantined)}"
    )

    print(
        f"Total duplicates removed: {len(all_duplicates)}"
    )

    if len(all_quarantined) != 24:
        raise ValueError(
            "Expected 24 quarantined records overall"
        )

    if len(all_duplicates) != 8:
        raise ValueError(
            "Expected 8 exact duplicates overall"
        )

    add_check(
        validation_results,
        "Total quarantined records",
        24,
        len(all_quarantined),
    )

    add_check(
        validation_results,
        "Total exact duplicates removed",
        8,
        len(all_duplicates),
    )

    print("All validation counts: PASS")

    print ("\nStarting four-format comparison...")

    if len(canonical_tables) != 4:
        raise ValueError(
            f"Expected 4 cleaned datasets, "
            f"found {len(canonical_tables)}"
        )

    #Use CSV as the referene dataset.
    reference = canonical_tables[0]

    #Compare only the six canonical columns.
    reference = reference[CANONICAL_COLUMNS].copy()

    #Compare Excel, JSON, and Parquet against CSV.
    format_names = [
        "Excel",
        "JSON",
        "Parquet"
    ]

    for format_name, other_table in zip(
        format_names,
        canonical_tables[1:]
    ):

        other = other_table[
            CANONICAL_COLUMNS
        ].copy()

        try:
            compare_frames(
                reference,
                other
            )
            add_check(
                validation_results,
                f"CSV vs {format_name} agreement",
                True,
                True,
            )

        except AssertionError as error:
            raise AssertionError(
                f"{format_name} does not match CSV: "
                f"{error}"
            ) from error

        print(
            f"CSV vs {format_name}: PASS"
        )
    
    #Final canonical dataset
    canonical_df = reference.sort_values(
        by=["country", "year"]
    ).reset_index(drop=True)

    if len(canonical_df) != 1704:
        raise ValueError(
            f"Expected 1704 canonical records, "
            f"found {len(canonical_df)}"
        )

    if canonical_df.duplicated(
        subset=["country", "year"]
    ).any():
        raise ValueError(
            "Canonical dataset has duplicate "
        )

    add_check(
        validation_results,
        "Final canonical row count",
        manifest["expected_per_file"]["canonical_rows"],
        len(canonical_df),
    )

    add_check(
        validation_results,
        "Unique country-year keys",
        0,
        int(
            canonical_df.duplicated(
                subset=["country", "year"]
            ).sum()
        ),
    )

    add_check(
        validation_results,
        "Number of countries",
        manifest["controls"]["countries"],
        canonical_df["country"].nunique(),
    )

    add_check(
        validation_results,
        "Allowed continents",
        0,
        int(
            (~canonical_df["continent"].isin(
                manifest["allowed_continents"]
            )).sum()
        ),
    )

    add_check(
        validation_results,
        "Allowed years",
        0,
        int(
            (~canonical_df["year"].isin(
                manifest["allowed_years"]
            )).sum()
        ),
    )
    print("\nFour-format agreement: PASS")
    add_audit(
        audit_log,
        step="comparison",
        source_file="all_four_formats",
        operation="compare_canonical_records",
        rule="Match by country and year; float tolerance 1e-8",
        rows_before=len(canonical_df),
        rows_after=len(canonical_df),
    )
    print(
        f"Final canonical records: {len(canonical_df)}"
    )

    print("\nStarting analytical processing...")

    #1. Select Asian countries for the reporting year.
    asia_df = asia_selected_year(
        canonical_df,
        {"reporting_year": reporting_year}
    )

    print(
        f"Asia {reporting_year} records: {len(asia_df)}"
    )

    #2. Calculate the selected-year Asian population.
    asia_population = asia_pop(asia_df)

    print(
        f"Asia {reporting_year} population: "
        f"{asia_population:,}"
    )

    #3. Generate Philippines historical observations
    history_df = country_history(canonical_df)

    if len(history_df) != 12:
        raise ValueError(
            f"Expected 12 Philippines records, "
            f"found {len(history_df)}"
        )

    print(
        f"Philippines historical records: "
        f"{len(history_df)}"
    )

    #4. Generate the population index matrix
    matrix_df = population_matrix(canonical_df)

    if matrix_df.shape != (3,7):
        raise ValueError(
            f"Expected a 3x7 matrix table, "
            f"found {matrix_df.shape}"
        )

    expected_countries = [
        "Philippines",
        "Indonesia",
        "Thailand"
    ]

    expected_columns = [
        "country",
        "1982",
        "1987",
        "1992",
        "1997",
        "2002",
        "2007"
    ]

    if matrix_df["country"].tolist() != expected_countries:
        raise ValueError(
            "Population matrix countries do not match"
        )

    if list(matrix_df.columns) != expected_columns:
        raise ValueError(
            "Population matrix columns do not match"
        )

    #Every country's 1982 baseline should equal 100.
    if not np.allclose(
        matrix_df["1982"].to_numpy(dtype=float),
        100.0,
        rtol=0,
        atol=1e-8
    ):
        raise ValueError(
            "Population index baseline verification failed"
        )

    print("Population index matrix: PASS")

    #5. Verify the required 2007 population controls.
    verification = calc_verification(canonical_df)

    if not verification["asia_population_matches_benchmark"]:
        raise ValueError(
            "Asia 2007 population benchmark failed"
        )
    
    if not verification["ph_population_matches_benchmark"]:
        raise ValueError(
            "Philippines 2007 population benchmark failed"
        )

    print("Asia 2007 population benchmark: PASS")
    print("Philippines 2007 population benchmark: PASS")

    #6. Check the selected-year Asia result independently.
    numpy_asia_population = int(
        np.sum(asia_df["pop"].to_numpy(dtype=np.int64))
    )

    if asia_population != numpy_asia_population:
        raise ValueError(
            "Pandas and NumPy Asia population totals disagree"
        )

    print("Pandas and Numpy population agreement: PASS")
    add_check(
        validation_results,
        "Philippines historical rows",
        manifest["controls"]["philippines_rows"],
        len(history_df),
    )

    add_check(
        validation_results,
        "Asia 2007 population",
        manifest["controls"]["asia_2007_population"],
        int(
            canonical_df.loc[
                (canonical_df["continent"] == "Asia")
                & (canonical_df["year"] == 2007),
                "pop"
            ].sum()
        ),
    )

    add_check(
        validation_results,
        "Philippines 2007 population",
        manifest["controls"]["philippines_2007_population"],
        int(
            canonical_df.loc[
                (canonical_df["country"] == "Philippines")
                & (canonical_df["year"] == 2007),
                "pop"
            ].sum()
        ),
    )

    add_check(
        validation_results,
        "Population matrix baseline",
        True,
        bool(
            np.allclose(
                matrix_df["1982"].to_numpy(dtype=float),
                100.0,
                rtol=0,
                atol=1e-8,
            )
        ),
    )

    add_check(
        validation_results,
        "Pandas NumPy Asia total agreement",
        asia_population,
        numpy_asia_population,
    )

    if reporting_year == 2007:
        add_check(
            validation_results,
            "Asia 2007 rows",
            manifest["controls"]["asia_2007_rows"],
            len(asia_df),
        )
    print("\nAnalytical processing: PASS")

    print("\nStarting safe output staging...")

    #Make sure the output's parent folder exists.
    output_dir = output_dir.resolve()

    output_dir.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    #Create a temporary folder beside output.

    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=".recovery-stage-",
            dir=output_dir.parent
        )
    )

    try:
        print("Writing files to staging directory...")
        # Save quarantined and duplicate records.
        save_record_report(
            all_quarantined,
            staging_dir / "quarantine.csv",
        )

        save_record_report(
            all_duplicates,
            staging_dir / "duplicate_log.csv",
        )

        print(
            f"Quarantined records saved: {len(all_quarantined)}"
        )

        print(
            f"Duplicate records saved: {len(all_duplicates)}"
        )

        #Save the three analytical reports.
        asia_df.to_csv(
            staging_dir / "asia_selected_year.csv",
            index=False
        )

        history_df.to_csv(
            staging_dir / "country_history.csv",
            index=False
        )

        matrix_df.to_csv(
            staging_dir / "population_index.csv",
            index=False
        )

        print("Analytical reports: STAGED")
        add_audit(
            audit_log,
            step="analysis",
            source_file="canonical",
            operation="generate_analytical_reports",
            rule=f"Reporting year {reporting_year}",
            rows_before=len(canonical_df),
            rows_after=len(canonical_df),
        )

        add_audit(
            audit_log,
            step="export",
            source_file="canonical",
            operation="export_and_reload",
            rule="Four canonical formats must round-trip",
            rows_before=len(canonical_df),
            rows_after=len(canonical_df),
        )

        #Export all four canonical formats, reloads and compares every export/
        export_paths = export_and_verify(
            canonical_df,
            staging_dir
        )

        for format_name in (
            "csv",
            "xlsx",
            "json",
            "parquet"
        ):
            if format_name not in export_paths:
                raise ValueError(
                    f"Missing export: {format_name}"
                )
            print(
                f"Canonical {format_name.upper()}: VERIFIED"
            )

        for format_name in (
            "csv",
            "xlsx",
            "json",
            "parquet",
        ):
            add_check(
                validation_results,
                f"{format_name.upper()} export roundtrip",
                True,
                format_name in export_paths,
            )

        # Save the validation report in staging.
        if not all(
            result["pass"]
            for result in validation_results
        ):
            raise ValueError(
                "One or more validation checks failed"
            )

        save_validation(
            validation_results,
            staging_dir / "validation.csv",
        )

        print("Validation report: STAGED")

        #Publish only after all checks succeed.
        save_audit(
            audit_log,
            staging_dir / "audit_log.csv",
        )

        print("Audit log: STAGED")
        publish_staging(
            staging_dir,
            output_dir
        )

        print("Staged files published successfully!")

    except Exception:
        #Remove incomplete temporary files.
        if staging_dir.exists():
            shutil.rmtree(staging_dir)

        print(
            "Staging failed. Previous outputs were preserved."
        )

        raise

    print("\nSafe Staging and Publication: PASS")


def run_pipeline(config: dict) -> None:
    """Run the pipeline and report failures safely."""

    validation_results = []

    try:
        _run_pipeline(
            config,
            validation_results,
        )

    except Exception as error:
        # Keep failure diagnostics outside output/,
        # so previous successful outputs remain intact.
        output_dir = Path(config["output_dir"])
        failure_path = (
            output_dir.parent / "failed_validation.csv"
        )

        add_check(
            validation_results,
            "Pipeline execution",
            "success",
            f"{type(error).__name__}: {error}",
        )

        save_validation(
            validation_results,
            failure_path,
        )

        print(
            f"Failure report saved: {failure_path}"
        )

        raise