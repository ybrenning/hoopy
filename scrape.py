import os
import time

import requests
import pandas as pd
from bs4 import BeautifulSoup

url = "https://www.basketball-reference.com/"

path = os.getcwd() + "/data"


def first_row_value(series):
    return series.iloc[0]


def first_row_or_nan(series):
    result = ""
    for s in series:
        result += "-" + s
    return result.strip("-")
    if len(series) >= 2:
        return pd.NA
    else:
        return series.iloc[0]


handle_column_aggs = {
    "Rk": first_row_value,
    "Pos": first_row_value,
    "Age": first_row_value,
    "Tm": first_row_or_nan,
    "G": "sum",
    "GS": "sum",
    "MP": "sum",
    "FG": "sum",
    "FGA": "sum",
    "FG%": "mean",
    "3P": "sum",
    "3PA": "sum",
    "3P%": "mean",
    "2P": "sum",
    "2PA": "sum",
    "2P%": "mean",
    "eFG%": "mean",
    "FT": "sum",
    "FTA": "sum",
    "FT%": "mean",
    "ORB": "sum",
    "DRB": "sum",
    "TRB": "sum",
    "AST": "sum",
    "STL": "sum",
    "BLK": "sum",
    "TOV": "sum",
    "PF": "sum",
    "PTS": "sum"
}


def get_player_totals_from_season(season_end):
    response = requests.get(url + f"leagues/NBA_{season_end}_totals.html")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")

        df = pd.read_html(str(table))[0]
        df = df[(df["Player"] != "Player") & (df["Tm"] != "TOT")]

        columns = df.columns.tolist()
        stat_columns = columns[columns.index("G"):]

        for sc in stat_columns:
            df[sc] = pd.to_numeric(df[sc], errors="coerce")

        df["Player"] = df["Player"].apply(lambda x: x.replace("*", ""))

        agg_df = df.groupby("Player").agg(handle_column_aggs).reset_index()

        return agg_df
    else:
        return None


def save_player_totals(path):
    # Get data in batches of 29, since the website
    # does not allow for more requests per minute ¯\_(ツ)_/¯
    for batch in range(1950, 2023+1, 29):
        for season in range(batch, batch+29):
            if season > 2023:
                break

            print(f"Fetching season {season}")
            df = get_player_totals_from_season(season)
            df.to_csv(f"{path}/player_totals_{season}.csv")

        time.sleep(60)


if __name__ == "__main__":
    save_player_totals(path)
