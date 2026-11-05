"""Tests for CLI configuration and output protection."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestCLIIntegration(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.work_dir = Path(self.temp.name)

        with (ROOT / "config.json").open(
            encoding="utf-8"
        ) as file:
            self.config = json.load(file)

        for key in ("data_dir", "manifest"):
            path = Path(self.config[key])
            if not path.is_absolute():
                self.config[key] = str(ROOT / path)

        self.config["output_dir"] = str(
            self.work_dir / "output"
        )

    def run_with_config(self, config):
        config_path = self.work_dir / "test_config.json"

        config_path.write_text(
            json.dumps(config),
            encoding="utf-8",
        )

        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "main.py"),
                "--config",
                str(config_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_invalid_reporting_year(self):
        config = self.config.copy()
        config["reporting_year"] = 1999

        result = self.run_with_config(config)

        self.assertNotEqual(result.returncode, 0)

    def test_missing_data_directory(self):
        config = self.config.copy()
        config["data_dir"] = str(
            self.work_dir / "nonexistent_data"
        )

        result = self.run_with_config(config)

        self.assertNotEqual(result.returncode, 0)

    def test_previous_output_preserved(self):
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir()

        original = output_dir / "existing.txt"
        original.write_text(
            "previous successful output",
            encoding="utf-8",
        )

        config = self.config.copy()
        config["data_dir"] = str(
            self.work_dir / "nonexistent_data"
        )

        result = self.run_with_config(config)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            original.read_text(encoding="utf-8"),
            "previous successful output",
        )

if __name__ == "__main__":
    unittest.main()