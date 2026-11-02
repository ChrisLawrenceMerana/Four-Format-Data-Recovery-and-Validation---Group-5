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