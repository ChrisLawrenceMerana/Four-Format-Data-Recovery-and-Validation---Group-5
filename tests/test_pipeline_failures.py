"""Integration tests for pipeline failure handling."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

class TestPipelineFailures(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.work_dir = Path(self.temp_dir.name)

        with open(
            PROJECT_ROOT / "config.json",
            encoding="utf-8",
        ) as file:
            self.config = json.load(file)

        # Resolve paths against the project folder.
        for key in ("data_dir", "manifest"):
            path = Path(self.config[key])

            if not path.is_absolute():
                self.config[key] = str(
                    PROJECT_ROOT / path
                )

        # Never overwrite the real output folder.
        self.config["output_dir"] = str(
            self.work_dir / "output"
        )

    def run_pipeline(self):
        config_path = self.work_dir / "config.json"

        config_path.write_text(
            json.dumps(self.config),
            encoding="utf-8",
        )

        return subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "main.py"),
                "--config",
                str(config_path),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_input_directory(self):
        self.config["data_dir"] = str(
            self.work_dir / "missing_data"
        )

        result = self.run_pipeline()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            (self.work_dir / "failed_validation.csv").exists()
        )

    def test_missing_manifest(self):
        self.config["manifest"] = str(
            self.work_dir / "missing_manifest.json"
        )

        result = self.run_pipeline()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            (self.work_dir / "failed_validation.csv").exists()
        )

    def test_corrupted_input_hash(self):
        # Copy the manifest and deliberately use
        # an incorrect hash for the first input.
        with open(
            self.config["manifest"],
            encoding="utf-8",
        ) as file:
            manifest = json.load(file)

        manifest["files"][0]["sha256"] = "0" * 64

        altered_manifest = (
            self.work_dir / "altered_manifest.json"
        )

        altered_manifest.write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )

        self.config["manifest"] = str(
            altered_manifest
        )

        result = self.run_pipeline()

        self.assertNotEqual(result.returncode, 0)

        self.assertIn(
            "SHA-256 mismatch",
            result.stdout + result.stderr,
        )

    def test_previous_output_is_preserved(self):
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(parents=True)

        sentinel = output_dir / "existing_report.txt"
        sentinel.write_text(
            "previous successful output",
            encoding="utf-8",
        )

        self.config["data_dir"] = str(
            self.work_dir / "missing_data"
        )

        result = self.run_pipeline()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(sentinel.exists())
        self.assertEqual(
            sentinel.read_text(encoding="utf-8"),
            "previous successful output",
        )

if __name__ == "__main__":
    unittest.main()