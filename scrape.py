#!/usr/bin/env python3

import argparse
import datetime
import os
import re
import time
from io import StringIO
from itertools import compress
from urllib.error import HTTPError

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

URL = "https://www.basketball-reference.com/"

available_player_stats = [
    "totals",
    "per_game",
    "per_minute",
    "per_poss",
    "advanced",
    "play-by-play",
    "shooting",
    "adj_shooting"
]

available_team_stats = [
    "standings"
]

available_misc_stats = [
    "leaders",
    "mvps"
]

available_stats = [
    *available_player_stats,
    *available_team_stats,
    *available_misc_stats
]

available_leaders_stats = [
    "pts",
    "ppg",
    "r",
    "rpg",
    "or",
    "dr",
    "a",
    "apg",
    "s",
    "spg",
    "b",
    "bpg"
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
current_year = int(datetime.date.today().strftime("%Y"))


def handle_agg(series):
    if series.name == "Tm":
        result = ""
        for s in series:
            if s != "TOT":
                result += "-" + s
        return result.strip("-")
    else:
        return series.iloc[0]


def format_multi_index_columns(columns):
    unnamed_mask = [
        True if col[0].startswith("Unnamed") else False for col in columns
    ]
    named_mask = [not m for m in unnamed_mask]

    first_col_names = ["" for m in unnamed_mask if m] + \
        [col[0] for col in list(compress(columns, named_mask))]

    second_col_names = [
        col[1] for col in list(compress(columns, unnamed_mask))
    ] + [col[1] for col in list(compress(columns, named_mask))]

    new_columns = [
        " ".join(col).rstrip('_').lstrip(" ") for col in zip(
            first_col_names, second_col_names
        )
    ]

    return new_columns


def scrape_players_multi_index(response):
    html = response.text
    soup = BeautifulSoup(re.sub("<!--|-->", "", html), "html.parser")
    table = soup.find("table")

    df = pd.read_html(StringIO(str(table)))[0]
    df = df.dropna(axis=1, how="all")

    df.columns = format_multi_index_columns(df.columns.tolist())

    stat_columns = df.columns[df.columns.tolist().index("G"):]
    for sc in stat_columns:
        df[sc] = pd.to_numeric(df[sc], errors="coerce")

    df = df.drop("Rk", axis=1)

    player_name_mask = df["Player"].apply(
        lambda x: not isinstance(x, str) or x == "Player"
    )
    rows_to_drop = df[player_name_mask].index
    df.drop(rows_to_drop, inplace=True)

    df["Player"] = df["Player"].apply(
        lambda x: x.replace("*", "")
    )
    agg_df = df.groupby("Player").agg(handle_agg).reset_index()

    return agg_df


def scrape_players_single_index(response):
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")

    df = pd.read_html(StringIO(str(table)))[0]
    df = df.dropna(axis=1, how="all")
    df = df.drop("Rk", axis=1)

    columns = df.columns.tolist()
    stat_columns = columns[columns.index("G"):]

    for sc in stat_columns:
        df[sc] = pd.to_numeric(df[sc], errors="coerce")

    player_name_mask = df["Player"].apply(
        lambda x: not isinstance(x, str) or x == "Player"
    )
    rows_to_drop = df[player_name_mask].index
    df.drop(rows_to_drop, inplace=True)

    df["Player"] = df["Player"].apply(lambda x: x.replace("*", ""))
    agg_df = df.groupby("Player").agg(handle_agg).reset_index()

    return agg_df


def scrape_standings(response):
    html = response.text
    soup = BeautifulSoup(re.sub("<!--|-->", "", html), "html.parser")
    table = soup.find_all("table")

    df_east = pd.read_html(StringIO(str(table[0])))[0]
    df_west = pd.read_html(StringIO(str(table[1])))[0]

    # Handles older standings tables
    if isinstance(df_west.columns, pd.MultiIndex):
        index_east = df_east[df_east["Team"] == "Eastern Division"].index[0]
        index_west = df_east[df_east["Team"] == "Western Division"].index[0]

        # Handle central divison separately, this is only the case in 1950
        index_central = df_east[df_east["Team"] == "Central Division"].index[0]
        if index_central is not None:
            df_central = df_east.iloc[index_central+1: index_east, :]
        else:
            df_central = None

        df_west = df_east.iloc[index_west+1:, :]
        df_east = df_east.iloc[index_east+1: index_west, :]
    else:
        df_central = None

    df_east.columns = df_east.columns.str.replace(
        "Eastern Conference", "Team"
    )
    df_west.columns = df_west.columns.str.replace(
        "Western Conference", "Team"
    )

    df_east = df_east.dropna(axis=1, how="all")
    df_west = df_west.dropna(axis=1, how="all")

    for sc in df_east.columns.tolist()[1:]:
        df_east[sc] = pd.to_numeric(df_east[sc], errors="coerce")
        df_west[sc] = pd.to_numeric(df_west[sc], errors="coerce")

    df_east["Team"] = df_east["Team"].apply(
        lambda x: x.replace("*", "")
    )
    df_west["Team"] = df_west["Team"].apply(
        lambda x: x.replace("*", "")
    )

    # Handle central division
    if df_central is not None:
        df_central = df_central.dropna(axis=1, how="all")

        for sc in df_central.columns.tolist()[1:]:
            df_central[sc] = pd.to_numeric(df_central[sc], errors="coerce")

        df_central["Team"] = df_central["Team"].apply(
            lambda x: x.replace("*", "")
        )

        df_central = df_central.reset_index(drop=True)

    df_east = df_east[~df_east["Team"].str.contains("Division")]
    df_west = df_west[~df_west["Team"].str.contains("Division")]

    return (
        df_east.reset_index(drop=True),
        df_west.reset_index(drop=True),
        df_central
    )


def scrape_leaders(response):
    html = response.text
    soup = BeautifulSoup(re.sub("<!--|-->", "", html), "html.parser")
    table = soup.find_all("table")

    dfs = []
    for i in range(0, len(available_leaders_stats)):
        df = pd.read_html(StringIO(str(table[i])))[0]

        df = df.drop(labels=[0], axis=1)
        df.columns = ["Player", "Total"]
        df["Player"] = df["Player"].apply(
            lambda x: x.split("•")[0].rstrip(" ").replace("*", "")
        )

        dfs.append(df)

    return dfs


def scrape_mvps(response):
    html = response.text
    soup = BeautifulSoup(re.sub("<!--|-->", "", html), "html.parser")
    table = soup.find("table")

    df = pd.read_html(StringIO(str(table)))[0]
    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.droplevel()
    df = df.drop(labels=["Rank"], axis=1)

    for sc in df.columns[3:]:
        df[sc] = pd.to_numeric(df[sc], errors="coerce")

    return df


def make_request(season_end, stat):
    url_appendix = f"leagues/NBA_{season_end}_{stat}.html"
    if stat in single_index:
        scrape_table = scrape_players_single_index
    elif stat in multi_index:
        scrape_table = scrape_players_multi_index
    elif stat in available_team_stats:
        scrape_table = scrape_standings
    elif stat == "leaders":
        scrape_table = scrape_leaders
    elif stat == "mvps":
        url_appendix = f"awards/awards_{season_end}.html"
        scrape_table = scrape_mvps
    else:
        raise ValueError

    response = requests.get(URL + url_appendix)

    if response.status_code == 200:
        return scrape_table(response)
    else:
        raise HTTPError(response.status_code)


def save_stat_tables(save_path, *stats, start_season=1950, end_season=None):
    start_season = start_season or 1950
    end_season = end_season or current_year
    if start_season > end_season:
        raise ValueError

    # Get data in batches of 30, since the website
    # does not allow for more requests per minute ¯\_(ツ)_/¯
    batch_size = 30

    for stat in stats:
        print(f"Loading {stat}")

        if stat in ["shooting", "play-by-play"]:
            cur_start_season = 1997 if start_season < 1997 else start_season
            print(
                "Disclaimer: stats only available starting from",
                "1997"
            )
        elif stat in ["per_poss", "leaders"]:
            cur_start_season = 1974 if start_season < 1974 else start_season
            print(
                "Disclaimer: stats only available starting from",
                "1974"
            )
        elif stat == "mvps":
            cur_start_season = 1957 if start_season < 1957 else start_season
            print(
                "Disclaimer: stats only available starting from",
                "1957"
            )
        else:
            cur_start_season = start_season

        for batch_start in range(cur_start_season, end_season+1, batch_size):
            pbar = tqdm(
                range(batch_start, min(batch_start+batch_size, end_season+1)),
                ascii=True
            )
            for season in pbar:
                pbar.set_description(f"Processing {season}")
                df = make_request(season, stat)

                if stat == "standings":
                    df_east, df_west, df_central = df
                    df_east.to_csv(
                        f"{save_path}/{stat}_east_{season}.csv",
                        index=False
                    )
                    df_west.to_csv(
                        f"{save_path}/{stat}_west_{season}.csv",
                        index=False
                    )

                    if df_central is not None:
                        df_central.to_csv(
                            f"{save_path}/{stat}_central_{season}.csv",
                            index=False
                        )
                elif stat == "leaders":
                    dfs = df
                    for lstat, df in zip(available_leaders_stats, dfs):
                        df.to_csv(
                            f"{save_path}/{lstat}_leaders_{season}.csv",
                            index=False
                        )
                else:
                    df.to_csv(
                        f"{save_path}/player_{stat}_{season}.csv",
                        index=False
                    )

            # Don't start cooldown if there are no seasons left
            if min(batch_start+batch_size, end_season+1) == end_season:
                break

            for i in tqdm(range(0, 60), desc="Request cooldown (60s)"):
                time.sleep(1)


def parse_args():
    stat_options = ", ".join([stat for stat in available_stats])

    parser = argparse.ArgumentParser(description="Scrape NBA data")
    parser.add_argument(
        "stats",
        metavar="stats",
        type=str,
        nargs="+",
        help=f"stat categories to scrape [{stat_options}]"
    )
    parser.add_argument(
        "--seasons",
        required=False,
        metavar="seasons",
        type=str,
        nargs=1,
        help="(optional) range of seasons to scrape from, e.g. 1996-1998",
    )

    args = parser.parse_args()
    for stat in args.stats:
        if stat not in available_stats:
            raise ValueError(
                f"'{stat}' is not a valid stat. Read help menu for more info"
            )

    if args.seasons:
        if len(args.seasons) > 1:
            raise ValueError(
                f"{len(args.seasons)} date args provided, 1 expected"
            )

        date_pattern = re.compile(r"^(19|20)\d{2}-(19|20)\d{2}$")
        if date_pattern.match(args.seasons[0]):
            start_season = int(args.seasons[0].split("-")[0])
            end_season = int(args.seasons[0].split("-")[1])
        else:
            raise ValueError(
                "Invalid season format provided. Read help menu for more info"
            )

        valid_seasons = range(1950, current_year + 1)
        if (
                start_season > end_season or
                start_season not in valid_seasons or
                end_season not in valid_seasons
           ):
            raise ValueError("Invalid season range provided")
    else:
        start_season = end_season = None

    return args.stats, start_season, end_season


if __name__ == "__main__":
    stats, start_season, end_season = parse_args()
    save_stat_tables(
        path,
        *stats,
        start_season=start_season,
        end_season=end_season
    )
