
"""Pipeline for four-format data recovery and validation."""

import hashlib
import json
from pathlib import Path

import pandas as pd

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
)

from src.exporter import (
    export_and_verify,
    compare_frames,
)

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

def run_pipeline(config: dict) -> None:
    """Load and verify the four input datasets."""

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
        print("Validation: PASS")
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

    print("All validation counts: PASS")