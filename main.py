
"""Command-line entry point for the recovery pipeline."""

import argparse
import json
import sys
from pathlib import Path

from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Four-format data recovery and validation"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to the JSON configuration file",
    )

    args = parser.parse_args()

    try:
        config_path = Path(args.config)

        with config_path.open(encoding="utf-8") as file:
            config = json.load(file)

        # Resolve relative paths from the config file's folder.
        for key in ("data_dir", "output_dir", "manifest"):
            if key in config:
                path = Path(config[key])

                if not path.is_absolute():
                    config[key] = str(
                        config_path.resolve().parent / path
                    )

        run_pipeline(config)

    except Exception as error:
        print(
            f"Pipeline failed: {error}",
            file=sys.stderr,
        )
        return 1

    print("Pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())