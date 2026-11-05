import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.exporter import(
    export_and_verify,
    compare_frames
)

class TestMember5(unittest.TestCase):

    def setUp(self):
        self.sample = pd.DataFrame([
            {
                "country":"Philippines",
                "continent":"Asia",
                "year":2007,
                "lifeExp":71.688,
                "pop":91077287,
                "gdpPercap":3190.481
            }
        ])

    def test_export_and_verify(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = export_and_verify(
                self.sample,
                folder
            )

            self.assertEqual(len(paths), 4)

            for path in paths.values():
                self.assertTrue(Path(path).exists())

    def test_corrupted_value(self):
        corrupted = self.sample.copy()

        corrupted.loc[0, "pop"] = 123

        with self.assertRaises(AssertionError):
            compare_frames(
                self.sample,
                corrupted
            )

if __name__ == "__main__":
    unittest.main()