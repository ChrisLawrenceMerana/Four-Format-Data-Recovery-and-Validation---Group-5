"""Row validation, quarantine, duplicates and conflicts."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

COLUMNS = ["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]
TEXT = {"country", "continent"}
WHOLE = {"year", "pop"}


class ConflictingKeyError(Exception):
    """Raised when two valid rows share (country, year) but disagree elsewhere."""


class ValidationRun:
    """Holds the validation outcome for one source file."""

    def __init__(self, source_file: str, raw_rows: int) -> None:
        self.source_file = source_file
        self.raw_rows = raw_rows
        self.clean_rows: list[dict[str, Any]] = []
        self.quarantined: list[dict[str, Any]] = []
        self.duplicates: list[dict[str, Any]] = []

    def reconciles(self) -> bool:
        """Return True if raw = rejected + duplicate copies + canonical rows."""
        kept = len(self.quarantined) + len(self.duplicates) + len(self.clean_rows)
        return kept == self.raw_rows

def check_value(column: str, value: Any, rules: dict[str, Any]) -> Any:
    """Return the cleaned value, or raise ValueError('column: reason')."""
    text = "" if value is None or pd.isna(value) else str(value).strip()
    if text == "":
        raise ValueError(f"{column}: missing value")
    if column in TEXT:
        if column == "continent" and text not in rules["allowed_continents"]:
            raise ValueError(f"{column}: not allowed")
        return text
    try:
        number = float(text)
    except ValueError:
        raise ValueError(f"{column}: invalid number") from None
    if not math.isfinite(number):
        raise ValueError(f"{column}: non-finite number")
    if column in WHOLE:
        if not number.is_integer():
            raise ValueError(f"{column}: fractional value")
        number = int(number)
    if column == "year" and number not in rules["allowed_years"]:
        raise ValueError(f"{column}: not an allowed year")
    low, high = rules.get("ranges", {}).get(column, (-math.inf, math.inf))
    if not low <= number <= high:
        raise ValueError(f"{column}: out of range")
    return number