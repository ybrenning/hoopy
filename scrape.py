import requests
import pandas as pd
from bs4 import BeautifulSoup

url = "https://www.basketball-reference.com/leagues/NBA_2023_totals.html"


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


def main():
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find("table")

    df = pd.read_html(str(table))[0]
    df = df[(df["Player"] != "Player") & (df["Tm"] != "TOT")]

    columns = df.columns.tolist()
    stat_columns = columns[columns.index("G"):]

    for sc in stat_columns:
        df[sc] = pd.to_numeric(df[sc], errors="coerce")

    agg_df = df.groupby("Player").agg({
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
    }).reset_index()

    print(agg_df.sort_values(by=["3P", "3P%"], ascending=False)[0:20])


if __name__ == "__main__":
    main()
