from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px

from nba_api.stats.endpoints import leagueleaders


def generate_seasons(start, end):
    seasons = []
    for i in range(start, end + 1):
        seasons.append(f"{i:02}-{int(str(i % 100 + 1)[-2:]):02}")
    return seasons


seasons = generate_seasons(1952, 2023)
three_pt_seasons = seasons[seasons.index("1979-80"):]

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children="NBA Stats", style={"textAlign": "center"}),
    dcc.Dropdown(three_pt_seasons, seasons[-1], id="season-dropdown"),
    dcc.Graph(id="graph-content")
])


@callback(
    Output("graph-content", "figure"),
    Input("season-dropdown", "value")
)
def update_scatter(season):
    top_500 = leagueleaders.LeagueLeaders(
        season=season,
        season_type_all_star="Regular Season",
        stat_category_abbreviation="PTS"
    ).get_data_frames()[0][:500]

    top_500["PPG"] = round(top_500["PTS"] / top_500["GP"], 2)

    # These API requests rake forever...
    # def get_player_pos(player_id):
    #     return str(commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]["POSITION"])
    #
    # top_500["POS"] = top_500["PLAYER_ID"].map(get_player_pos)
    # print(top_500["POS"])
    print(top_500.columns)

    return px.scatter(top_500, x="PPG", y="FG3M", hover_data=["PLAYER"])


if __name__ == "__main__":
    app.run(debug=True)
