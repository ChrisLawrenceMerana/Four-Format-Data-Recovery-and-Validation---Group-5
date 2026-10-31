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


def normalize_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce data types, uniqueness, and domain bounds."""
    result = df.loc[:, list(SCHEMA)].copy()
    
    if result.isna().any().any():
        raise ValueError("This dataset must not contain missing fields.")
    
    for column in ("year", "pop"):
        numeric = pd.to_numeric(result[column], errors="raise")
        if not np.isfinite(numeric.to_numpy(dtype=float)).all() or not (numeric % 1 == 0).all():
            raise ValueError(f"{column} must contain finite whole numbers.")
            
    try:
        result = result.astype(SCHEMA)
    except (ValueError, TypeError) as error:
        raise ValueError(f"Cannot apply the expected schema: {error}") from error
        
    if result.duplicated(["country", "year"]).any():
        raise ValueError("Duplicate country-year key.")
        
    if not (result["pop"] > 0).all():
        raise ValueError("Population must be positive.")
        
    if not (np.isfinite(result["lifeExp"]) & result["lifeExp"].between(0, 120)).all():
        raise ValueError("Life expectancy must be finite and between 0 and 120.")
        
    if not (np.isfinite(result["gdpPercap"]) & result["gdpPercap"].gt(0)).all():
        raise ValueError("GDP per capita must be finite and positive.")
        
    if result.empty:
        raise ValueError("No records were loaded.")
        
    return result