#Create validation reports for successfuly and failed runs.

from pathlib import Path
import pandas as pd

COLUMNS = [
    "check",
    "expected",
    "actual",
    "tolerance",
    "pass",
]

def add_check(
    results: list[dict],
    check: str,
    expected: object, 
    actual: object, 
    tolerance: float = 0,
) -> None:
    #Record a comparison and whether it passed

    if (
        isinstance(expected,(int,float))
        and isinstance(actual,(int,float))
        and not isinstance(expected, bool)
        and not isinstance(actual,bool)
    ):
        passed = abs(actual - expected) <= tolerance
    else:
        passed = actual == expected

    results.append({
        "check": check, 
        "expected": expected, 
        "actual": actual,
        "tolerance": tolerance,
        "pass": passed,
    })

def save_validation(
    results: list[dict],
    path: Path,
) -> None:
    #Save the validation results as a CSV.

    path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        results,
        columns=COLUMNS,
    ).to_csv(path,index=False)