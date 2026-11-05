#Audit logging for pipline operations.

from pathlib import Path
import pandas as pd

AUDIT_COLUMNS = [
    "step",
    "source_file",
    "operation",
    "rule",
    "rows_before",
    "rows_after",
]

def add_audit(
    audit_log: list[dict],
    step: str,
    source_file: str,
    operation: str,
    rule: str,
    rows_before: int,
    rows_after: int,
) -> None:
    #Record one pipeline operation.

    audit_log.append({
        "step": step,
        "source_file": source_file,
        "operation": operation,
        "rule": rule,
        "rows_before": rows_before,
        "rows_after": rows_after,
    })

def save_audit (
    audit_log: list[dict],
    file_path:Path,
)->None:
    #Save audit events as a CSV File.

    pd.DataFrame(
        audit_log,
        columns=AUDIT_COLUMNS,
    ).to_csv(file_path,index=False)