"""Module containing format readers for CSV and Excel files."""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

CANONICAL_COLUMNS = ["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]


def read_csv_records(
    file_path: str | Path,
    encoding: str = "cp1252",
    delimiter: str = ";",
    comment_lines: int = 2,
    column_mapping: Optional[Dict[str, str]] = None,
    drop_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Parses raw CSV records handling custom encoding, delimiter, and comments.

    Preserves 1-based source record indices for downstream audit and validation.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    # Read records, skipping documented initial comment lines
    df = pd.read_csv(
        path,
        encoding=encoding,
        delimiter=delimiter,
        skiprows=comment_lines,
        dtype=str,
        keep_default_na=False,
    )

    # 1-based source record position
    df["source_record"] = range(1, len(df) + 1)
    df["source_file"] = path.name

    # Drop non-canonical metadata fields if requested
    if drop_columns:
        for col in drop_columns:
            if col in df.columns:
                df = df.drop(columns=[col])

    # Apply canonical column rename
    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Validate that all canonical columns exist
    missing_cols = set(CANONICAL_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"CSV file '{path.name}' is missing required canonical columns: {missing_cols}"
        )

    return df


def read_excel_records(
    file_path: str | Path,
    sheet_name: str = "observations",
    column_mapping: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Parses observations sheet from Excel workbook."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(
        path, sheet_name=sheet_name, dtype=str, keep_default_na=False
    )

    df["source_record"] = range(1, len(df) + 1)
    df["source_file"] = path.name

    if column_mapping:
        df = df.rename(columns=column_mapping)

    missing_cols = set(CANONICAL_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Excel file '{path.name}' is missing required canonical columns: {missing_cols}"
        )

    return df