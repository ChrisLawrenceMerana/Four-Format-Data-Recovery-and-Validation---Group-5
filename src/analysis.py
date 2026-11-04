"""Module for pandas analysis & numpy matrix"""

import numpy as np
import pandas as pd
from typing import Any, Dict, Tuple

def asia_selected_year(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
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

def asia_pop(asia_df: pd.DataFrame) -> int:
    """Computes the asian population of a selected year"""

    return int(asia_df["pop"].sum())

def country_history(df: pd.DataFrame) -> pd.DataFrame:
    """Searches for Philippine observations according to year"""

    #Philippine and year filter
    ph_mask = df["country"] == "Philippines"
    ph_df = df.loc[ph_mask].sort_values(by="year").copy().reset_index(drop=True)

    if ph_df.empty:
        raise ValueError("No observations found")

    #Million population add
    ph_df["pop_millions"] = ph_df["pop  "] / 1000000

    #Life-expectancy
    first_life_exp = ph_df.loc[0, "lifeExp"]
    ph_df["lifeExp_change"] = ph_df["lifeExp"] - first_life_exp

    return ph_df

def population_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Creates 3x6 population matrix of the Philippines, Indonesia, Thailand in the years 1982, 1987, 1992, 1997, 2002, and 2007. Afterwards, Each row's 1982 baseline is broadcasted and soon exported as a .csv file"""

    countries = ["Philippines", "Indonesia", "Thailand"]
    years = [1982, 1987, 1992, 1997, 2002, 2007]

    #Subset for stated countries and years
    subset = df[df["country"].isin(countries) & df["year"].isin(years)]

    #Country year matrix
    pivot_df = subset.pivot(index="country", columns="year", values="pop")
    pivot_df = pivot_df.reindex(countries, columns=years)

    #Numpy array conversion
    pop_matrix = pivot_df.to_numpy(dtype=float)
    shape_before = pop_matrix.shape

    #Broadcasting
    baseline = pop_matrix[:, 0:1]
    indexed_matrix = (pop_matrix / baseline) *100
    shape_after = indexed_matrix.shape
    print(f"Shape before broadcast: {shape_before}. Shape after broadcast: {shape_after}")

    #Loop check
    indexed_loop = np.empty_like(pop_matrix)
    for i in range(pop_matrix.shape[0]):
        base= pop_matrix[1, 0]
        for j in range(pop_matrix.shape[1]):
            indexed_loop[i, j] = (pop_matrix[i, j] / base) *100

    #Broadcasting verification w/ loop calculation
    np.testing.assert_allclose(
        indexed_matrix, indexed_loop, rtol=1e-8,
        err_msg="Broadcasting does not match loop calculation."
    )

    #Boolean selection + aggregate
    mask = pop_matrix > 100000000
    filtered_mean = float(pop_matrix[mask]. mean()) if mask.any() else 0
    print(f"Boolean selection & aggregation: {filtered_mean:,.2f}")

    #Dataframe export
    result_df = pd.DataFrame(indexed_matrix, index=countries, columns=[str(y) for y in years])
    result_df.index.name = "country"
    result_df = result_df.reset_index()

    return result_df