from pathlib import Path

import pandas as pd

SCHEMA = {
    "country": "string",
    "continent": "string",
    "year": "int64",
    "lifeExp": "float64",
    "pop": "int64",
    "gdpPercap": "float64",
}

COLUMNS = list(SCHEMA)

def compare_frames(
    expected: pd.DataFrame,
    actual: pd.DataFrame
) -> None:
    """Compare two canonical tables by country and year."""

    if list(expected.columns) != COLUMNS:
        raise AssertionError("Unexpected original columns")

    if list(actual.columns) != COLUMNS:
        raise AssertionError("Unexpected reloaded columns")

    # Check missing values before converting types.
    if not expected.isna().equals(actual.isna()):
        raise AssertionError("Missing-value mismatch")

    expected = expected.astype(SCHEMA)
    actual = actual.astype(SCHEMA)

    expected = expected.sort_values(
        ["country", "year"]
    ).reset_index(drop=True)

    actual = actual.sort_values(
        ["country", "year"]
    ).reset_index(drop=True)

    # Exact comparison for text and integer values.
    for column in ("country", "continent", "year", "pop"):
        pd.testing.assert_series_equal(
            expected[column],
            actual[column],
            check_exact=True
        )

    # Assignment tolerance for floating-point values.
    for column in ("lifeExp", "gdpPercap"):
        pd.testing.assert_series_equal(
            expected[column],
            actual[column],
            check_exact=False,
            rtol=0,
            atol=1e-8
        )

def export_and_verify(
    df: pd.DataFrame,
    output_dir: str | Path
) -> dict[str, str]:
    """Export four formats and verify every reload."""

    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    canonical = df[COLUMNS].astype(SCHEMA)

    paths = {
        "csv": folder / "canonical.csv",
        "xlsx": folder / "canonical.xlsx",
        "json": folder / "canonical.json",
        "parquet": folder / "canonical.parquet",
    }

    # Export canonical dataset.
    canonical.to_csv(
        paths["csv"],
        index=False
    )

    canonical.to_excel(
        paths["xlsx"],
        sheet_name="observations",
        index=False
    )

    canonical.to_json(
        paths["json"],
        orient="records",
        double_precision=15
    )

    canonical.to_parquet(
        paths["parquet"],
        index=False,
        engine="pyarrow"
    )

    # Reload the exported datasets.
    reloaded = {
        "csv": pd.read_csv(paths["csv"]),
        "xlsx": pd.read_excel(
            paths["xlsx"],
            sheet_name="observations"
        ),
        "json": pd.read_json(
            paths["json"],
            orient="records"
        ),
        "parquet": pd.read_parquet(
            paths["parquet"]
        ),
    }

    # Compare all four against the original.
    for format_name, table in reloaded.items():
        compare_frames(canonical, table)

        print(f"{format_name.upper()} round trip: PASS")

    return {
        name: str(path)
        for name, path in paths.items()
    }