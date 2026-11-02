"""Checks for row validation, quarantine, duplicates and conflicts."""

import unittest

import pandas as pd

from src.validation import ConflictingKeyError, validate_and_dedupe

RULES = {
    "allowed_years": set(range(1952, 2008, 5)),
    "allowed_continents": {"Africa", "Americas", "Asia", "Europe", "Oceania"},
    "ranges": {"lifeExp": (0, 120), "pop": (1, 10**11), "gdpPercap": (0, 10**7)},
}
GOOD = {"country": "Philippines", "continent": "Asia", "year": "2007",
        "lifeExp": "71.688", "pop": "91077287", "gdpPercap": "3190.481"}


def make_df(*overrides: dict) -> pd.DataFrame:
    """Build a string DataFrame from GOOD plus per-row overrides."""
    return pd.DataFrame([{**GOOD, **o} for o in overrides])


class ValidationTests(unittest.TestCase):
    def test_normal_row_is_trimmed_and_typed(self):
        table, run = validate_and_dedupe(make_df({"country": " Philippines "}), "f.csv", RULES)
        self.assertEqual(table.loc[0, "country"], "Philippines")
        self.assertEqual(str(table["year"].dtype), "int64")
        self.assertTrue(run.reconciles())

    def test_reconciliation_adds_up(self):
        df = make_df({}, {}, {"year": "1952", "lifeExp": "abc"})
        _, run = validate_and_dedupe(df, "f.csv", RULES)
        self.assertEqual((run.raw_rows, len(run.quarantined), len(run.duplicates)), (3, 1, 1))
        self.assertTrue(run.reconciles())

def test_bad_rows_are_quarantined(self):
        bad = [{"lifeExp": "abc"}, {"year": "1997.5"}, {"pop": "100.25"}, {"lifeExp": "nan"},
               {"gdpPercap": "inf"}, {"lifeExp": "999"}, {"year": "1900"},
               {"country": "  "}, {"pop": ""}]
        for override in bad:
            with self.subTest(override=override):
                table, run = validate_and_dedupe(make_df(override), "f.csv", RULES)
                self.assertEqual((len(table), len(run.quarantined)), (0, 1))

    def test_quarantine_keeps_raw_value(self):
        _, run = validate_and_dedupe(make_df({"lifeExp": "abc"}), "f.csv", RULES)
        self.assertEqual(run.quarantined[0]["lifeExp"], "abc")
        self.assertEqual(run.quarantined[0]["source_record"], 1)        