

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import Image
import requests
import json 
import time
import os


#
#       this file contains information and functions required to generate team and player statistics and analytics from the 2024 season.
#       the data from which this file draws from is stored locally in the "Data" folder. 
#       this code creates four dataframes, team analytics, player analytics, team statistics, and player statistics. 
#


# addresses to the analytics and statistics directories 
analytics_directory = r"C:\Users\grant\Desktop\Sam & Grant Lose Their Money\Git Ready\Data\2024_SEASONAL_ANALYTICS"
statistics_directory = r"C:\Users\grant\Desktop\Sam & Grant Lose Their Money\Git Ready\Data\2024_SEASONAL_STATISTICS"


# addresses to specific parameters for a given datasheet (team_analytics, player_analytics, etc.). 
# the functions below allow the user to define any valid parameter address here and it will be stored and displayed in the table. 
endpoint_addresses = {

                'team_analytics' : {
                                    "Corsi For" : lambda d: d['own_record']['statistics']['total']['corsi_for'],
                                    "Corsi Against" : lambda d: d['own_record']['statistics']['total']['corsi_against'],
                                    "Corsi Delta" : lambda d: d['own_record']['statistics']['total']['corsi_total'],
                                    "Corsi %" : lambda d: d['own_record']['statistics']['total']['corsi_pct'],
                                    "Fenwick_For" : lambda d: d['own_record']['statistics']['total']['fenwick_for'],
                                    "Fenwick Against" : lambda d: d['own_record']['statistics']['total']['fenwick_against'],
                                    "Fenwick Delta" : lambda d: d['own_record']['statistics']['total']['fenwick_total'],
                                    "Fenwick %" : lambda d: d['own_record']['statistics']['total']['fenwick_pct'],
                },



                'player_analytics' : {
                                    "Name" : lambda d: d['full_name'],
                                    "Corsi For" : lambda d: d['statistics']['total']['corsi_for'],
                                    "Corsi Against" : lambda d: d['statistics']['total']['corsi_against'],
                                    "Corsi Delta" : lambda d: d['statistics']['total']['corsi_total'],
                                    "Corsi %" : lambda d: d['statistics']['total']['corsi_pct'],
                                    "Fenwick_For" : lambda d: d['statistics']['total']['fenwick_for'],
                                    "Fenwick Against" : lambda d: d['statistics']['total']['fenwick_against'],
                                    "Fenwick Delta" : lambda d: d['statistics']['total']['fenwick_total'],
                                    "Fenwick %" : lambda d: d['statistics']['total']['fenwick_pct'],
                },



                'team_stats' : {
                                    "Wins" : lambda d: d['own_record']['goaltending']['total']['wins'],
                                    "Losses" : lambda d: d['own_record']['goaltending']['total']['losses'],
                                    "OT Losses" : lambda d: d['own_record']['goaltending']['total']['overtime_losses'],
                                    "Goals": lambda d: d['own_record']['statistics']['total']['goals']
                }, # find odds of going to OT, odds of getting an empty net, odds of each team pulling goalie



                'player_stats' : {

                                    "Name" : lambda d: d['full_name'],
                                    "Position" : lambda d: d['primary_position'],
                                    "Games Played" : lambda d: d['statistics']['total']['games_played'],
                                    "Shots Blocket" : lambda d: d['statistics']['total']['blocked_shots'],
                                    "Shots ON" : lambda d: d['statistics']['total']['shots'],
                                    "Shots OFF" : lambda d: d['statistics']['total']['missed_shots'],                 
                }

}


# handles the case of storing team related data. this function acts as an intermediate to creating the final dataframe (which is done below). 
# the "data" is the seasonal (2024) statistics for a given team, containing information for both players and teams. 

def fill_team_data(data, storing_dict, fetching_endpoint_dict):

    """
    args:
        data (.json): seasonal analytics, or statistics for a given team (includes all individual player information).
        storing dict (dict): the dictionary allocated to store all league wide data (one allocated for each of the 4 tables).
        fetching_endpoint_dict (dict): the appropriate dict of parameter addresses to be fetched (from the "endpoint_addresses" dictionary above).
    """

    temp_storing_dict = {}      # for temporary storage

    # create the team labels for the dataframe | handling the two teams from New York  
    if data["market"] == "New York":
        team_market = f"{data['market']} {data['name']}"
    else:
        team_market = data["market"]

    # store team ID and name 
    team_id = data['id']
    temp_storing_dict['Team'] = team_market

    # iterate through each endpoint datapoint address in "fetching_endpoint_dict"
    # and store it in "temp_storing_dict"
    for KEY, VALUE in fetching_endpoint_dict.items():
                temp_storing_dict[KEY] = VALUE(data)
                
    # store the information of the specific team in the final storage dict 
    storing_dict[team_id] = pd.Series(temp_storing_dict)
    


# handles the case of storing player related data. this function acts as an intermediate to creating the final dataframe (which is done below).  
def fill_player_data(data, storing_dict, fetching_endpoint_dict, min_games = 9):

    """
    args:
        data (.json): seasonal analytics, or statistics for a given team (includes all individual player information).
        storing dict (dict): the dictionary allocated to store all league wide data (one allocated for each of the 4 tables).
        fetching_endpoint_dict (dict): the appropriate dict of parameter addresses to be fetched (from the "endpoint_addresses" dictionary above).
        min_games = 9 (int): include only the players that have played > min_games.  
    """

    temp_storing_dict = {}      # temporary storage

    # iterate through each player in "data"
    for player in data['players']:
        temp_storing_dict.clear()  # clear the temporary storing dict. this is redundant


        # create the team labels for the dataframe | handling the two teams from New York  
        if data["market"] == "New York":
            team_market = f"{data['market']} {data['name']}"
        else: 
            team_market = data["market"]

        # only take the players that have played more than "min_games"
        if player['statistics']['total']['games_played'] > min_games:
            temp_storing_dict['Team'] = team_market

            # iterate through each endpoint datapoint address in "fetching_endpoint_dict"
            # and store it in "temp_storing_dict"
            for KEY, VALUE in fetching_endpoint_dict.items():
                temp_storing_dict[KEY] = VALUE(player)

            # correct for players that have played on multiple teams | store the player's data in the final dict 
            if player['id'] in storing_dict:
                storing_dict[f"{player['id']}, {team_market}"] = pd.Series(temp_storing_dict, name=False)
            else:
                storing_dict[player['id']] = pd.Series(temp_storing_dict, name=False)

        else:
            continue

    # return the dict of player metrics 
    return storing_dict



# make sure you test the case where there are the same names on the same team. it might be worth using their player id instead of their names


# array of addresses to the two data directories
endpoints = [analytics_directory, statistics_directory]

# final dictionaries for each of the four tables for 2024 data 
team_stats_2024 = {}
player_stats_2024 = {}
team_analytics_2024 = {}
player_analytics_2024 = {}



for endpoint in endpoints:  # walk through each directory address in "endpoints"
    
    # walks through each file in the directories stored in "endpoints"
    for subdir, dirs, files in os.walk(endpoint):
        teams = []
        for file in files:
            if file.endswith(".json"):  # only consider the .json files
                
                file = os.path.join(subdir, file)   # parse the file name to the parent directory path
                
                try:
                    # open the file and store the .json file as "data"
                    with open(file) as f:
                        data = json.load(f)


                    ## ------- Load team and player analytics from 2024

                    if endpoint == analytics_directory:

                        fill_team_data(data = data,
                                        storing_dict = team_analytics_2024,
                                        fetching_endpoint_dict = endpoint_addresses['team_analytics'])

                        fill_player_data(data = data,
                                            storing_dict = player_analytics_2024,
                                            fetching_endpoint_dict = endpoint_addresses['player_analytics'])


                    ## ------- Load team and player statistics from 2024

                    if endpoint == statistics_directory:

                        fill_team_data(data = data,
                                        storing_dict = team_stats_2024,
                                        fetching_endpoint_dict = endpoint_addresses['team_stats'])
                        
                        fill_player_data(data = data,
                                            storing_dict = player_stats_2024,
                                            fetching_endpoint_dict = endpoint_addresses['player_stats'])


                except Exception as e:
                    print(file)
                    print(e)


TEAM_ANALYTICS_2024 = pd.DataFrame.from_dict(team_analytics_2024, orient = 'index')
PLAYER_ANALYTICS_2024 = pd.DataFrame.from_dict(player_analytics_2024, orient = 'index')
TEAM_STATS_2024 = pd.DataFrame.from_dict(team_stats_2024, orient = 'index')
PLAYER_STATS_2024 = pd.DataFrame.from_dict(player_stats_2024, orient = 'index')





