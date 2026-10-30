"""Column mapping and schema validation utilities."""

from typing import Any, Dict
import numpy as np
import pandas as pd

SCHEMA: Dict[str, str] = {
    "country": "string",
    "continent": "string",
    "year": "int64",
    "lifeExp": "float64",
    "pop": "int64",
    "gdpPercap": "float64",
}


def apply_column_mapping(df: pd.DataFrame, manifest: Dict[str, Any]) -> pd.DataFrame:
    """Map source columns to canonical schema names."""
    column_mapping = manifest.get("column_mapping", {})
    if column_mapping:
        df = df.rename(columns=column_mapping)

    missing_cols = [col for col in SCHEMA if col not in df.columns]
    if missing_cols:
        raise KeyError(f"File error: Missing required columns: {missing_cols}")

    return df


