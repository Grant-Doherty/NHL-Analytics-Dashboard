import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import Image
import requests
import json 
import time
import os
import statsmodels.api as sm


# this function creates an array of dicts of all the players and teams in the league along with their unique IDs, and additionally for players, their position and jersey number. 
# this dict is used as the list for the "look-up" bar in the 2025 season section. Allows players' names to be linked with thier unique ID in the search process.
def load_player_and_team_options():

    # a list made by myself of all players in the league. Note this list will be outdated if any new players enter the league. 
    with open(r"Data/League Manifest.json", "r") as f:
        manifest = json.load(f)

    player_team_options = []

    # iterate through all player IDs and the players' name in the manifest and get their name, position and number. 
    for player_id, p in manifest["Players"].items():
        name = p.get("Name", "")
        pos = p.get("Position", "")
        num = p.get("Number", "")

        # Build the label dynamically with only the fields that exist
        parts = [name]
        detail_parts = []

        if pos:
            detail_parts.append(pos)
        if num:
            detail_parts.append(f"#{num}")

        if detail_parts:
            parts.append(f"({', '.join(detail_parts)})")

        label = " ".join(parts)

        # append a dict (to "player_team_options") of the label being player name, position, number, as the label, and their unique ID being the value in the dict. 
        player_team_options.append({
            "label": label,
            "value": player_id
        })

    # interate through all team IDs and teams' name in the manifest and append a dict (to "player_team_options") of the label being team name as the label, 
    # and their unique ID being the value in the dict. 
    for team_ID, team_name in manifest["Teams"].items():
        player_team_options.append({
            "label": team_name,
            "value": team_ID
        })
    return player_team_options



# perfroms a linear regression on the "momentum_window"# most recent games of a particular metric.
# returns the slope and the standard error of the slope of the regression
# this momentum measuring metric is good on long time frames ~30 games
def rolling_ROC(metric_array, momentum_window):

    metric_array = np.array(metric_array)

    x = np.arange(momentum_window)
    x = sm.add_constant(x)
    y = metric_array[-momentum_window:]

    linear_regression = sm.OLS(y,x).fit()
    slope = linear_regression.params[1]
    slope_error = linear_regression.bse[1]

    return slope, slope_error


# if short_time_frame = 10, long_time_frame = 15
# determines the average of a metric from games -25 t -10, and from -10 to now and finds the difference. 
# this answers the question "is the player performing better in the last 10 games than in the previous 15"
# note that the reference for the long time frame is taken from the short time frame
# this momentum measuring metric is generally good for intermediate timeframes, like the timeframes used for the example
def rolling_difference_in_averages(metric_array, short_time_frame, long_time_frame):

    metric_array = np.array(metric_array)
    recent_average = np.mean(metric_array[-short_time_frame:])
    previous_average = np.mean(metric_array[-short_time_frame-long_time_frame:-short_time_frame])

    difference_in_averages = recent_average - previous_average

    return difference_in_averages