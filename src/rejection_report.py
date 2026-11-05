#Save quarantined and duplicate records as CSV reports.

from pathlib import Path
import pandas as pd

def save_record_report(
    records: list,
    file_path: Path,
) -> None:
    #Write validation records without modifying them.

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    #Accept dictionaries, pandas Series, or DataFrames.
    if isinstance(records, pd.DataFrame):
        report_df = records.copy()
    else:
        report_df = pd.DataFrame(
            [
                record.to_dict()
                if isinstance(record, pd.Series)
                else record
                for record in records
            ]
        )

    report_df.to_csv(
        file_path,
        index=False,
    )