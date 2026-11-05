# Four-Format Data Recovery and Validation

**Group 5 — Python Data Recovery Project**

## Project Overview

This project implements a reproducible data recovery and validation pipeline using the historical Gapminder teaching dataset. It processes four file formats—CSV, Excel, JSON, and Parquet—and produces a consistent canonical dataset.

The pipeline verifies input integrity, standardizes column names, validates records, quarantines invalid observations, removes exact duplicates, compares recovered datasets, performs Pandas and NumPy analysis, and exports verified results.

## Group Members

- Aljur Cabalfin — CSV and Excel Readers
- Macie Moises — JSON and Parquet Processing
- Sheryl Jane Galleto — Data Validation
- Clarence John Ello — Data Analysis and NumPy
- Chris Lawrence Meraña — Export and Pipeline Integration

## Requirements

- Python 3.10 or later with compatible dependencies
- pip
- Git
- Jupyter Notebook (for the technical report)

Required Python packages are listed in `requirements.txt`.

## Installation

1. Clone the repository:

   `git clone https://github.com/ChrisLawrenceMerana/Four-Format-Data-Recovery-and-Validation---Group-5.git`

2. Open the project folder.

3. Install dependencies:

   `py -m pip install -r requirements.txt`

## Running the Pipeline

From the project root, run:

`py main.py --config config.json`

The pipeline reads the supplied files in `data/` and saves verified results in `output/`.

The default reporting year is 2007.

## Automated Testing

Run the test suite using:

`py -m unittest discover -s tests -p "test_*.py" -v`

Generate the test report using:

`py -m unittest discover -s tests -p "test_*.py" -v *> test_results.txt`

The test suite covers input reading, validation, duplicate handling, format comparisons, exports, integration, and failure scenarios.

## Expected Recovery Results

| Metric | Expected Result |
|---|---:|
| Raw records per input format | 1,712 |
| Invalid records per format | 6 |
| Exact duplicates per format | 2 |
| Canonical records | 1,704 |
| Total quarantined records | 24 |
| Total duplicates removed | 8 |
| Countries | 142 |

The four source formats represent the same underlying observations. Therefore, the canonical dataset contains 1,704 records rather than combining all four sources into one larger table.

## Generated Outputs

The `output/` directory contains:

| File | Description |
|---|---|
| `canonical.csv` | Canonical dataset in CSV |
| `canonical.xlsx` | Canonical dataset in Excel |
| `canonical.json` | Canonical dataset in JSON |
| `canonical.parquet` | Canonical dataset in Parquet |
| `asia_selected_year.csv` | Selected-year Asian country observations |
| `country_history.csv` | Philippines historical observations |
| `population_index.csv` | NumPy-based population index |
| `validation.csv` | Validation and agreement checks |
| `audit_log.csv` | Processing audit trail |
| `quarantine.csv` | Rejected records with reasons |
| `duplicate_log.csv` | Exact duplicate records removed |

## Jupyter Technical Report

The project includes `report.ipynb` and `report.html`.

To open the notebook, use VS Code with the Jupyter extension or run:

`py -m jupyter notebook report.ipynb`

To export the notebook as HTML:

`py -m jupyter nbconvert --to html report.ipynb --output report.html`

The report presents recovery counts, cross-format agreement, NumPy results, and interpretations.

## Data Integrity and Failure Handling

Original input files are verified using SHA-256 checksums recorded in `manifest.json`.

Invalid records are quarantined, and exact duplicates are logged separately.

The pipeline uses a temporary staging directory. Final outputs are published only after required checks succeed. On failure, previously published results are preserved and a `failed_validation.csv` diagnostic report may be generated.

## Submission Documentation

- `contributions.csv` — Group member responsibilities and Git contribution evidence
- `reviews.md` — Peer review documentation
- `submission_manifest.txt` — Repository URL, release tag, commit hash, and original input hashes
- `test_results.txt` — Automated test results