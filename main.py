import argparse
import json

from src.pipeline import run_pipeline

def main() -> None:
    """Run the recovery pipeline using a configuration file."""

    parser = argparse.ArgumentParser(
        description="Four-Format Data Recovery and Validation"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration JSON file"
    )

    args = parser.parse_args()

    try:
        with open(args.config, encoding="utf-8") as file:
            config = json.load(file)

        run_pipeline(config)

        print("Pipeline completed successfully.")

    except Exception as error:
        print(f"Pipeline failed: {error}")
        raise SystemExit(1) from error

if __name__ == "__main__":
    main()