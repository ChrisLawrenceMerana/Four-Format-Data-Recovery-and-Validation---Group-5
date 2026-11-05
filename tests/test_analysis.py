"""Tests for pandas analysis, matrixes, and calculations"""

import unittest
import pandas as pd
import numpy as np

from src.analysis import (
    asia_selected_year,
    asia_pop,
    country_history,
    population_matrix,
    calc_verification,
)

class AnalysisTest(unittest.TestCase):

    def setUp(self):
        """Mock dataframe & config for testing"""

        self.mock_df = pd.DataFrame([
            {"country": "Philippines", "continent": "Asia", "year": 1982, "lifeExp": 62, "pop": 50000000, "gdpPercap": 2000},
            {"country": "Philippines", "continent": "Asia", "year": 1987, "lifeExp": 64, "pop": 57000000, "gdpPercap": 2100},
            {"country": "Philippines", "continent": "Asia", "year": 1992, "lifeExp": 66, "pop": 65000000, "gdpPercap": 2200},
            {"country": "Philippines", "continent": "Asia", "year": 1997, "lifeExp": 68, "pop": 73000000, "gdpPercap": 2400},
            {"country": "Philippines", "continent": "Asia", "year": 2002, "lifeExp": 70, "pop": 81000000, "gdpPercap": 2600},
            {"country": "Philippines", "continent": "Asia", "year": 2007, "lifeExp": 71.1, "pop": 91077287, "gdpPercap": 3000},

            {"country": "Indonesia", "continent": "Asia", "year": 1982, "lifeExp": 58, "pop": 150000000, "gdpPercap": 1500},
            {"country": "Indonesia", "continent": "Asia", "year": 1987, "lifeExp": 60, "pop": 170000000, "gdpPercap": 1600},
            {"country": "Indonesia", "continent": "Asia", "year": 1992, "lifeExp": 62, "pop": 190000000, "gdpPercap": 1800},
            {"country": "Indonesia", "continent": "Asia", "year": 1997, "lifeExp": 64, "pop": 200000000, "gdpPercap": 2000},
            {"country": "Indonesia", "continent": "Asia", "year": 2002, "lifeExp": 67, "pop": 215000000, "gdpPercap": 2200},
            {"country": "Indonesia", "continent": "Asia", "year": 2007, "lifeExp": 70, "pop": 230000000, "gdpPercap": 2500},

            {"country": "Thailand", "continent": "Asia", "year": 1982, "lifeExp": 65, "pop": 48000000, "gdpPercap": 2100},
            {"country": "Thailand", "continent": "Asia", "year": 1987, "lifeExp": 67, "pop": 53000000, "gdpPercap": 2300},
            {"country": "Thailand", "continent": "Asia", "year": 1992, "lifeExp": 69, "pop": 58000000, "gdpPercap": 2700},
            {"country": "Thailand", "continent": "Asia", "year": 1997, "lifeExp": 71, "pop": 61000000, "gdpPercap": 3100},
            {"country": "Thailand", "continent": "Asia", "year": 2002, "lifeExp": 72, "pop": 63000000, "gdpPercap": 3500},
            {"country": "Thailand", "continent": "Asia", "year": 2007, "lifeExp": 73, "pop": 65000000, "gdpPercap": 4000},

            {"country": "France", "continent": "Europe", "year": 2007, "lifeExp": 80.7, "pop": 62000000, "gdpPercap": 30000},
        ])
        self.config = {"reporting_year": 2007}

    def test_year_filter_rank(self):
        """Tests the filters for non-asian countries and adds desired columns"""

        result = asia_selected_year(self.mock_df, self.config)

        self.assertNotIn("France", result["country"].values)
        self.assertIn("pop_millions", result.columns)
        self.assertIn("lifeExp_rank", result.columns)

        #Verifies ranking for a non-asian country
        test_rank = result.loc[
            result["country"] == "Thailand",
            "lifeExp_rank"
        ].values[0]
        self.assertEqual(test_rank, 1.0)

    def test_asia_pop_calc(self):
        """Test pop sum"""

        asia_df = asia_selected_year(self.mock_df, self.config)
        total_pop = asia_pop(asia_df)
        desired = 91077287 + 230000000 + 65000000
        self.assertEqual(total_pop, desired)

    def test_country_history(self):
        """Test Philippine historical years & life expectancy change calc"""

        history_df = country_history(self.mock_df)

        self.assertEqual(history_df.loc[0, "lifeExp_change"], 0)
        self.assertAlmostEqual(history_df.loc[1, "lifeExp_change"], 2)

    def test_matrix(self):
        """Test numpy matrix"""

        matrix_df = population_matrix(self.mock_df)

        self.assertIn("country", matrix_df.columns)
        self.assertIn("2007", matrix_df.columns)
        self.assertEqual(len(matrix_df), 3)

    def test_calc_verification(self):
        """Test verification"""

        test = calc_verification(self.mock_df)
        self.assertIn("asia_population_matches_benchmark", test)
        self.assertIn("ph_population_matches_benchmark", test)
        self.assertIn("calculated_asia_pop", test)
        self.assertIn("calculated_ph_pop", test)

if __name__ == "__main__":
    unittest.main()