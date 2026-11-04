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