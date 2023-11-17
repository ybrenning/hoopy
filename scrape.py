#!/usr/bin/env python3

import os
import time
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

URL = "https://www.basketball-reference.com/"

available_stats = [
    "totals",
    "per_game",
    "per_minute",
    "per_poss",
    "advanced",
    "play-by-play",
    "shooting",
    "adj_shooting"
]

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
    if stat not in available_stats:
        raise ValueError

    # TODO: Implement these
    if stat in ["shooting", "adj_shooting"]:
        raise NotImplementedError

    response = requests.get(URL + f"leagues/NBA_{season_end}_{stat}.html")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")

        df = pd.read_html(StringIO(str(table)))[0]

        # TODO: Refactor all these if statements
        if stat == "play-by-play":
            idx = df.columns
            colnames = ["General" for _ in range(5)] + \
                [col[0] for col in idx[5:]]

            new_idx = list(zip(colnames, [col[1] for col in idx]))
            df.columns = pd.MultiIndex.from_tuples(new_idx)

        df = df.dropna(axis=1, how="all")

        columns = df.columns.tolist()

        if stat == "play-by-play":
            stat_columns = columns[[col[1] for col in columns].index("G"):]
        else:
            stat_columns = columns[columns.index("G"):]

        for sc in stat_columns:
            df[sc] = pd.to_numeric(df[sc], errors="coerce")

        if stat == "play-by-play":
            df[("General", "Player")] = df[("General", "Player")].apply(
                lambda x: x.replace("*", "")
            )
            agg_df = df.groupby(
                ("General", "Player")
            ).agg(handle_agg).reset_index()
        else:
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
    df = get_player_totals_from_season(2023, stat="play-by-play")
    print(df)
    # save_player_totals(path, ["totals", "advanced"])
