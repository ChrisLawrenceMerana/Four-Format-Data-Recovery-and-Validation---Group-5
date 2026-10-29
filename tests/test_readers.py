"""Automated checks for CSV and Excel format readers."""

import unittest
from pathlib import Path
from src.readers import CANONICAL_COLUMNS, read_csv_records, read_excel_records


class TestReaders(unittest.TestCase):

    def setUp(self):
        self.csv_path = Path("data/country_records.csv")
        self.excel_path = Path("data/country_records.xlsx")
        self.missing_col_csv = Path("data/missing_column.csv")

    def test_csv_reader_normal(self):
        """Verifies CSV parsing, raw row count (1712), and canonical headers."""
        if not self.csv_path.exists():
            self.skipTest("Case data not present.")

        mapping = {
            "country_name": "country",
            "region": "continent",
            "record_year": "year",
            "life_expectancy": "lifeExp",
            "population_total": "pop",
            "gdp_per_capita": "gdpPercap",
        }
        df = read_csv_records(
            self.csv_path,
            column_mapping=mapping,
            drop_columns=["metadata_notes"],
        )
        self.assertEqual(len(df), 1712)
        for col in CANONICAL_COLUMNS:
            self.assertIn(col, df.columns)

    def test_excel_reader_normal(self):
        """Verifies Excel sheet parsing, raw row count (1712), and canonical headers."""
        if not self.excel_path.exists():
            self.skipTest("Case data not present.")

        mapping = {
            "Country": "country",
            "Continent": "continent",
            "Year": "year",
            "Life_Expectancy": "lifeExp",
            "Population": "pop",
            "GDP_per_Capita": "gdpPercap",
        }
        df = read_excel_records(
            self.excel_path, sheet_name="observations", column_mapping=mapping
        )
        self.assertEqual(len(df), 1712)
        for col in CANONICAL_COLUMNS:
            self.assertIn(col, df.columns)

    def test_missing_file_failure(self):
        """Ensures FileNotFoundError is raised for non-existent files."""
        with self.assertRaises(FileNotFoundError):
            read_csv_records("data/non_existent_file.csv")

    def test_missing_column_failure(self):
        """Ensures ValueError is raised when required columns cannot be mapped."""
        if self.missing_col_csv.exists():
            with self.assertRaises(ValueError):
                read_csv_records(self.missing_col_csv)


if __name__ == "__main__":
    unittest.main()