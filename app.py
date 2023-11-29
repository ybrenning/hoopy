#!/usr/bin/env python3

import datetime
import os

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, callback, dcc, html

data_path = os.getcwd() + "/data"
current_year = int(datetime.date.today().strftime("%Y"))

seasons = [year for year in range(1950, current_year + 1)]
three_pt_seasons = seasons[seasons.index(1980):]

app = Dash(__name__)


def plot_fg_percentages():
    totals_dfs = []
    adv_dfs = []
    for season in seasons:
        totals_df = pd.read_csv(data_path + f"/player_totals_{season}.csv")
        adv_df = pd.read_csv(data_path + f"/player_advanced_{season}.csv")
        totals_df["season"] = season
        totals_dfs.append(totals_df)
        adv_df["season"] = season
        adv_dfs.append(adv_df)

    totals_combined = pd.concat(totals_dfs, ignore_index=True)
    totals_combined = totals_combined[["season",  "eFG%", "FG%"]]

    adv_combined = pd.concat(adv_dfs, ignore_index=True)
    adv_combined = adv_combined[["season", "TS%"]]

    totals_new_df = totals_combined.groupby("season").mean().reset_index()
    adv_new_df = adv_combined.groupby("season").mean().reset_index()

    new_df = pd.merge(totals_new_df, adv_new_df)

    fig = px.line(
        new_df,
        x="season",
        y=new_df.columns[1:],
        markers=".",
        template="seaborn",
        labels={"season": "Season", "value": "Shooting Percentage"}
    )

    fig.add_vline(x=1980, line_width=3, line_dash="dash", line_color="green")

    fig.add_annotation(
        x=1980,
        y=0.55,
        text="Introduction of 3PT line",
        showarrow=False,
        yshift=10,
    )

    fig.update_layout(
        autosize=False,
        width=1000,
        height=750,
        margin=dict(
            l=100,
            r=100,
            b=100,
            t=100,
            pad=4
        ),
    )

    return fig


# TODO: Implement this
def plot_ages():
    means = []
    medians = []
    for season in seasons:
        df = pd.read_csv(f"{data_path}/player_totals_{season}.csv")
        means.append(df["Age"].mean())
        medians.append(df["Age"].median())

    df = pd.DataFrame({"season": seasons, "mean": means, "median": medians})

    fig = px.line(
        df,
        x="season",
        y=["mean", "median"],
        template="seaborn"
    )

    fig.update_layout(
        autosize=False,
        width=1000,
        height=750,
        margin=dict(
            l=100,
            r=100,
            b=100,
            t=100,
            pad=4,
        ),
        yaxis_range=[24, 29],
    )

    return fig


app.layout = html.Div([
    html.H1(children="NBA Stats", style={"textAlign": "center"}),

    html.Div([
        dcc.Dropdown(
            three_pt_seasons,
            seasons[-1],
            id="season-dropdown",
        ),
    ]),

    html.Div([
        dcc.Graph(id="plot-ppg-threes"),
    ]),


    html.Div([
        dcc.Graph(figure=plot_fg_percentages(), id="plot-fg")
    ]),

    html.Div([
        dcc.Graph(figure=plot_ages(), id="plot-ages")
    ]),
])


@callback(
    Output("plot-ppg-threes", "figure"),
    Input("season-dropdown", "value")
)
def update_scatter(season_end):
    df = pd.read_csv(data_path + f"/player_totals_{season_end}.csv")
    df["PPG"] = round(df["PTS"] / df["G"], 2)

    fig = px.scatter(
        df,
        x="PPG",
        y="3P",
        color="Pos",
        hover_data=["Player"],
        template="seaborn"
    )

    fig.update_layout(
        autosize=False,
        width=1000,
        height=750,
        margin=dict(
            l=100,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
    )

    return fig


if __name__ == "__main__":
    mins_played_by_age()
    app.run(debug=True)
