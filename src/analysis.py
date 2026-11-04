"""Module for pandas analysis"""

import pandas as pd
from typing import Any, Dict

def generate_asia_selected_year(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Selects Asia and configured year, adds population in millions and descending life-expectancy rank. Afterwards, sorts by rank and country."""


    #Reads reporting year w/ default as 2007
    reporting_year = config.get("reporting_year", 2007)

    #.loc filter according to continent and year
    asia_mask = (df["continent"] == "Asia") & (df["year"]) == reporting_year
    asia_df = df.loc[asia_mask].copy()

    #Adds population in millions
    asia_df["pop_millions"] = asia_df["pop"] / 1000000

    #Adds descending life-expectancy
    asia_df["lifeExp_rank"] = asia_df["lifeExp"].rank(ascending=False, method="min")

    #Sort by rank and then country
    asia_df =asia_df.sort_values(by=["lifeExp_rank", "country"]).reset_index(drop=True)

    return asia_df

def calculate_asia_pop(asia_df: pd.DataFrame) -> int:
    """Computes the asian population of a selected year"""

    return int(asia_df["pop"].sum())