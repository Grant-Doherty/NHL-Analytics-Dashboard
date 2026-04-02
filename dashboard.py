

#
#       This program creates a dashboard that runs locally using "dash". This file contains the HTML mechanics that loads the dashboard.
#       This file imports data using python functions written in other files. These files contain the mechanics that imports the data from 
#       an official NHL API, and organizes the data into dataframes. The specific metrics that are displayed on the dashboard are speficied 
#       in these files. To edit the form of the dashboard, reference the files and functions that create these DFs. Current season data must 
#       be imported manually using "Update 2025 Game Data.py".
#

import dash
from dash import Dash, html, dcc, Input, Output, dash_table, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go

# --------- Importing dataframes from local files --------- #

# load_2024 loads four dictionaries (TEAM_ANALYTICS_2024, etc.) that stores seasonal information for players and teams. 
from load_2024 import TEAM_ANALYTICS_2024, PLAYER_ANALYTICS_2024, TEAM_STATS_2024, PLAYER_STATS_2024

# rename dicts to something more clean
TA24, PA24, TS24, PS24 = TEAM_ANALYTICS_2024, PLAYER_ANALYTICS_2024, TEAM_STATS_2024, PLAYER_STATS_2024

# functions to compile DFs for 2025 season data (teams and players)
from load_2025 import compile_agent_data_2025

# misc. functions.
from dash_functions import load_player_and_team_options, rolling_ROC, rolling_difference_in_averages
player_team_autocomplete_list = load_player_and_team_options()


# --------- Creating the dashboard --------- #

# maps selection from the dropdown menu to the appropriate dataframe
df_map = {
    "TA24": TA24,
    "PA24": PA24,
    "TS24": TS24,
    "PS24": PS24
}

# create the app
app = dash.Dash(
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True # Crucial because agent-table is generated dynamically
)

# defining the layout

# 2024 season title
app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.Div(
                [   
                    html.H1("2024 NHL Season", className="my-4"),
                    html.Img(
                        src="/assets/NHL_logo2.png",
                        style={"height": "60px", "marginLeft": "7px"}
                    )
                ],
                style={"display": "flex", "alignItems": "center", "justifyContent": "center"}
            )
        )
    ),

# dropdown title
    dbc.Row([
        dbc.Col(
            dbc.Label("Select Which Table to View", className="fw-bold", style = {"paddingTop":"12px", "paddingLeft" : "3px"}),
            width="auto"
        ),
    ]),

# dropdown
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='view-selector',
                options=[
                    {'label': 'Team Analytics', 'value': 'TA24'},
                    {'label': 'Player Analytics', 'value': 'PA24'},
                    {'label': 'Team Stats', 'value': 'TS24'},
                    {'label': 'Player Stats', 'value': 'PS24'}
                ],
                value='TA24',
                clearable=False,
                className="mb-3"
            ),
        )
    ]),

    html.Br(), 
# 2024 table placeholder                             
    html.Div(id='table-container'), 
    html.Br(), 

    dbc.Row([
        dbc.Col(
            html.Div(
                [
                    html.H1("2025 NHL Season", className = "my-4"),
                    html.Img(
                        src="/assets/NHL_logo2.png",
                        style = {"height": "60px", "marginLeft": "7px"}
                    )
                ],
                style = {"display": "flex", "alignItems": "center", "justifyContent": "center"}  
            )
        )
    ]),

# 2025 Season title
    dbc.Row([
        dbc.Col(
            dbc.Label("Enter a Player or Team to Graph", className="fw-bold", style = {"paddingTop":"12px", "paddingLeft" : "3px"}),
            width="auto"
        ),
    ]),
# search bar to load a specific player or team's data from the 2025 Season. 
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id = "player-lookup",
                options = player_team_autocomplete_list,
                placeholder = "Search a Player or Team...",
                searchable = True,
                clearable = True, 
                className = "mb-3"
            ),
        )
    ]),

    html.Br(),
# placeholder for the selected dataframe (player or team's 2025 seasonal data)
    html.Div(id="selected-player-id"),
    html.Br(),
# placeholder for the graph to visualize the timeseries of a specific player/team metric. 
    dcc.Graph(id="metric-timeseries-chart"),
    html.Br(), html.Br(), html.Br(), html.Br(), html.Br()
    
], fluid=True)


# --------- callback to link the 2024 dropdown to the chart --------- #
@app.callback(
    Output('table-container', 'children'),
    Input('view-selector', 'value')
)
def update_table(view):

    df = df_map[view]   # maps the df to view from the df_map dict 

    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in df.columns],
        page_size=10,
        filter_action="native", # allows the user to filter the data using custom filters (ie <10)
        sort_action="native", # allows the user to reorder (ascending/descending)
        style_table={"overflowX": "auto"}, # makes the table scrollable
        style_header={"backgroundColor": "#e9ecef", "fontWeight": "bold", "border": "1px solid #dee2e6"},
        style_cell={"padding": "8px", "fontFamily": "Arial", "fontSize": 14, "border": "1px solid #dee2e6", "backgroundColor": "white"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}]
    )

# --------- callback to link search bar to the 2025 table --------- #
@app.callback(
    Output("selected-player-id", "children"),
    Input("player-lookup", "value")
)
def load_2025_table(player_ID):

    if player_ID is None:       # handles the default case where no agent is selected
        return no_update

    df = compile_agent_data_2025(player_ID)
    df = df.reset_index().rename(columns={"index": "Agent Metric"})

    return dash_table.DataTable(
        id = "agent-table",
        data=df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in df.columns],
        fixed_columns={'headers': True, 'data': 1},     # keeps the column headers in view when scrolling
        row_selectable="single",
        page_size=25,
        filter_action="native",
        style_table={"min_width": "100%", "overflowX": "auto"},
        style_header={"backgroundColor": "#e9ecef", "fontWeight": "bold", "border": "1px solid #dee2e6"},
        style_cell={"minWidth": "150px", "width": "150px", "maxWidth": "150px", "padding": "8px", "fontFamily": "Arial", "fontSize": 14, "border": "1px solid #dee2e6", "backgroundColor": "white"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"}]
    )

# --------- callback to plot metric from selected row --------- #
@app.callback(
    Output("metric-timeseries-chart", "figure"),
    [
        Input("agent-table", "selected_rows"),
        Input("agent-table", "data")
    ],
    prevent_initial_call=True # Prevents errors before 'agent-table' exists
)
def plot_metric_from_row(selected_rows, table_data):

    if not selected_rows or not table_data:     # handles the default case where no metric is selected
        return go.Figure()

    row_idx = selected_rows[0]
    row = table_data[row_idx]

    metric_name = row["Agent Metric"]
    # Filter out the 'Agent Metric' key to get only the dates
    dates = [c for c in row.keys() if c != "Agent Metric"]
    values = [row[d] for d in dates]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        name=metric_name
    ))

    fig.update_layout(
        title=f"{metric_name} Over Time",
        xaxis_title="Date",
        yaxis_title=metric_name,
        template="plotly_white",
        height = 500
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True)