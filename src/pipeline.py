import json
from pathlib import Path

import pandas as pd

from src.readers import(
    read_csv_records,
    read_excel_records
)

from src.json_parquet_reader import(
    read_country_json,
    read_country_parquet
)

from src.validation import validate_and_dedupe

from src.analysis import (
    asia_selected_year,
    asia_pop,
    country_history,
    population_matrix
)

from src.exporter import(
    export_and_verify,
    compare_frames
)

def run_pipeline(config: dict) -> None:
    """Run the four-format recovery and validation pipeline."""

    data_dir = Path(config["data_dir"])
    output_dir = Path(config["output_dir"])

    with open(config["manifest"], encoding="utf-8") as file:
        manifest = json.load(file)

    reporting_year = config.get("reporting_year", 2007)

    print("Data directory:", data_dir)
    print("Output directory:", output_dir)
    print("Reporting year:", reporting_year)