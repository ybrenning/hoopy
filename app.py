import os

import pandas as pd

from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px


data_path = os.getcwd() + "/data"
seasons = [year for year in range(1950, 2023 + 1)]
three_pt_seasons = seasons[seasons.index(1980):]

app = Dash(__name__)


def plot_fg_percentages():
    dfs = []
    for season in seasons:
        df = pd.read_csv(data_path + f"/player_totals_{season}.csv")
        df["season"] = season
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[["season",  "eFG%", "FG%",]]

    new_df = combined.groupby("season").mean().reset_index()

    fig = px.line(
        new_df,
        x="season",
        y=new_df.columns[1:],
        markers=".",
        template="seaborn"
    )

    fig.add_vline(x=1980, line_width=3, line_dash="dash", line_color="green")

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
    ], )
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
    app.run(debug=True)
