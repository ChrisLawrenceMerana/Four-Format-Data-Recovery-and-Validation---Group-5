"""Tests for JSON/Parquet readers and validation."""

import unittest
import pandas as pd
import numpy as np

from src.json_parquet_readers import read_country_json, read_country_parquet
from src.normalizers import apply_column_mapping, normalize_and_validate, SCHEMA


class TestJsonParquet(unittest.TestCase):

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.sample_manifest = {
            "json_record_key": "records",
            "column_mapping": {
                "country_name": "country",
                "continent_name": "continent",
                "observation_year": "year",
                "life_expectancy": "lifeExp",
                "population": "pop",
                "gdp_per_capita": "gdpPercap"
            }
        }
        
        self.reference_df = pd.DataFrame({
            "country": ["Philippines", "Philippines"],
            "continent": ["Asia", "Asia"],
            "year": [2002, 2007],
            "lifeExp": [69.0, 71.5],
            "pop": [82000000, 87900000],
            "gdpPercap": [3100.5, 3500.0]
        }).astype(SCHEMA)

    def test_json_file_not_found(self) -> None:
        """Verify FileNotFoundError on missing JSON file."""
        with self.assertRaises(FileNotFoundError):
            read_country_json("nonexistent.json", self.sample_manifest)

    def test_parquet_file_not_found(self) -> None:
        """Verify FileNotFoundError on missing Parquet file."""
        with self.assertRaises(FileNotFoundError):
            read_country_parquet("nonexistent.parquet", self.sample_manifest)

    def test_missing_column_raises_error(self) -> None:
        """Verify KeyError when canonical columns are missing."""
        incomplete_df = pd.DataFrame({
            "country": ["Philippines"],
            "year": [2007]
        })
        with self.assertRaises(KeyError):
            apply_column_mapping(incomplete_df, self.sample_manifest)

    def test_duplicate_key_rejection(self) -> None:
        """Verify ValueError on duplicate country-year keys."""
        trial = pd.concat([self.reference_df, self.reference_df.iloc[[0]]], ignore_index=True)
        with self.assertRaises(ValueError) as ctx:
            normalize_and_validate(trial)
        self.assertIn("Duplicate country-year key", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()