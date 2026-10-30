"""JSON and Parquet file readers."""

import json
from pathlib import Path
from typing import Any, Dict, Union
import pandas as pd


def read_country_json(file_path: Union[str, Path], manifest: Dict[str, Any]) -> pd.DataFrame:
    """Read and flatten country records from a JSON file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    record_key = manifest.get("json_record_key", "records")
    if isinstance(raw_data, dict) and record_key in raw_data:
        records = raw_data[record_key]
    elif isinstance(raw_data, list):
        records = raw_data
    else:
        records = raw_data.get("data", raw_data)

    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("Expected a top-level JSON list or nested list of record objects.")

    return pd.DataFrame.from_records(records)
