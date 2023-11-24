#!/usr/bin/env python3

import os
import time
from io import StringIO
from urllib.error import HTTPError

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

single_index = [
    "totals",
    "per_game",
    "per_minute",
    "per_poss",
    "advanced"
]

multi_index = [
    "play-by-play",
    "shooting",
    "adj_shooting"
]

path = os.getcwd() + "/data"


def handle_agg(series):
    if series.name == "Tm" or series.name == "General Tm":
        result = ""
        for s in series:
            if s != "TOT":
                result += "-" + s
        return result.strip("-")
    else:
        return series.iloc[0]


def scrape_multi_index_table(response):
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")

    df = pd.read_html(StringIO(str(table)))[0]
    df = df.dropna(axis=1, how="all")

    # TODO: This only handles column names for shooting and play-by-play
    columns = df.columns.tolist()
    rename_amount = len([
        col for col in columns if col[0].startswith("Unnamed")
    ])
    first_col_names = ["General" for _ in range(rename_amount)] + \
        [col[0] for col in columns[rename_amount:]]

    new_columns = list(zip(first_col_names, [col[1] for col in columns]))
    df.columns = pd.MultiIndex.from_tuples(new_columns)

    stat_columns = new_columns[[col[1] for col in columns].index("G"):]
    for sc in stat_columns:
        df[sc] = pd.to_numeric(df[sc], errors="coerce")

    df.columns = [" ".join(col_name).rstrip('_') for col_name in df.columns]
    df = df.drop("General Rk", axis=1)

    df["General Player"] = df["General Player"].apply(
        lambda x: x.replace("*", "")
    )
    agg_df = df.groupby("General Player").agg(handle_agg).reset_index()

    return agg_df


def scrape_single_index_table(response):
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")

    df = pd.read_html(StringIO(str(table)))[0]
    df = df.dropna(axis=1, how="all")
    df = df.drop("Rk", axis=1)

    columns = df.columns.tolist()

    stat_columns = columns[columns.index("G"):]

    for sc in stat_columns:
        df[sc] = pd.to_numeric(df[sc], errors="coerce")

    df["Player"] = df["Player"].apply(lambda x: x.replace("*", ""))
    agg_df = df.groupby("Player").agg(handle_agg).reset_index()

    return agg_df


def make_request(season_end, stat):
    # TODO: Implement adj_shooting (table messed up due to JS)
    if stat in ["adj_shooting"]:
        raise NotImplementedError

    if stat in single_index:
        scrape_table = scrape_single_index_table
    elif stat in multi_index:
        scrape_table = scrape_multi_index_table
    else:
        raise ValueError

    response = requests.get(URL + f"leagues/NBA_{season_end}_{stat}.html")

    if response.status_code == 200:
        return scrape_table(response)
    else:
        raise HTTPError(response.status_code)


def save_player_totals(save_path, *stats):
    # Get data in batches of 30, since the website
    # does not allow for more requests per minute ¯\_(ツ)_/¯

    for stat in stats:
        print(f"Loading {stat}")
        for batch in range(1950, 2023+1, 30):
            pbar = tqdm(range(batch, min(batch+30, 2024)), ascii=True)
            for season in pbar:
                pbar.set_description(f"Processing {season}")
                df = make_request(season, stat)
                df.to_csv(f"{save_path}/player_{stat}_{season}.csv")

            for i in tqdm(range(0, 60), desc="Request cooldown"):
                time.sleep(1)


if __name__ == "__main__":
    df = make_request(season_end=2023, stat="shooting")
    # save_player_totals(path, ["totals", "advanced"])
