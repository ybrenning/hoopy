from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px

# TODO: Read from csv
from scrape import all_player_totals_from_season


seasons = [year for year in range(1950, 2023 + 1)]
three_pt_seasons = seasons[seasons.index(1980):]

app = Dash(__name__)


def plot_threes_ratio():
    ...
    return px.line()


app.layout = html.Div([
    html.H1(children="NBA Stats", style={"textAlign": "center"}),
    dcc.Dropdown(three_pt_seasons, seasons[-1], id="season-dropdown"),
    dcc.Graph(id="graph-content"),
    dcc.Graph(figure=plot_threes_ratio(), id="plot-threes")
])


@callback(
    Output("graph-content", "figure"),
    Input("season-dropdown", "value")
)
def update_scatter(season):
    df = all_player_totals_from_season(season)
    df["PPG"] = round(df["PTS"] / df["G"], 2)

    return px.scatter(df, x="PPG", y="3P", color="Pos", hover_data=["Player"])


if __name__ == "__main__":
    app.run(debug=True)
