#!/usr/bin/env python3

import os
import time
from io import StringIO

import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

URL = "https://www.basketball-reference.com/"

stats = ["totals", "advanced"]

path = os.getcwd() + "/data"


def handle_agg(series):
    if series.name == "Tm":
        result = ""
        for s in series:
            if s != "TOT":
                result += "-" + s
        return result.strip("-")
    else:
        return series.iloc[0]


def get_player_totals_from_season(season_end, stat):
    if stat in ["shooting", "play-by-play", "adj_shooting"]:
        raise NotImplementedError

    response = requests.get(URL + f"leagues/NBA_{season_end}_{stat}.html")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")

        df = pd.read_html(StringIO(str(table)))[0]
        df = df[df["Player"] != "Player"]
        df = df.dropna(axis=1, how="all")

        columns = df.columns.tolist()
        stat_columns = columns[columns.index("G"):]

        for sc in stat_columns:
            df[sc] = pd.to_numeric(df[sc], errors="coerce")

        df["Player"] = df["Player"].apply(lambda x: x.replace("*", ""))

        agg_df = df.groupby("Player").agg(handle_agg).reset_index()

        return agg_df
    else:
        return None


def save_player_totals(save_path, *stats):
    # Get data in batches of 30, since the website
    # does not allow for more requests per minute ¯\_(ツ)_/¯

    for stat in stats:
        print(f"Loading {stat}")
        for batch in range(1950, 2023+1, 30):
            pbar = tqdm(range(batch, min(batch+30, 2024)), ascii=True)
            for season in pbar:
                pbar.set_description(f"Processing {season}")
                df = get_player_totals_from_season(season, stat)
                df.to_csv(f"{save_path}/player_{stat}_{season}.csv")

            for i in tqdm(range(0, 60), desc="Request cooldown"):
                time.sleep(1)


if __name__ == "__main__":
    save_player_totals(path, *stats)
