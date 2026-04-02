import numpy as np         
import pandas as pd        
import json                
import os                  
from pathlib import Path   





Game_Metrics = {

    "Player" : {

        "Analytics" : {
            "Address" : "Game Analytics.json",
            "Start Date" : lambda d: d["start_time"],
            "Endpoints" : {
                "Corsi for"    : lambda index, agent_ID: index[agent_ID]["statistics"].get("corsi_for", 0),
                "Corsi Total"  : lambda index, agent_ID: index[agent_ID]["statistics"].get("corsi_total", 0),
                "Fenwick for"  : lambda index, agent_ID: index[agent_ID]["statistics"].get("fenwick_for", 0),
                "Fenwick Total": lambda index, agent_ID: index[agent_ID]["statistics"].get("fenwick_total", 0),
                "Average Distance": lambda index, agent_ID: index[agent_ID]["statistics"].get("average_shot_distance", 0),
                "Offensive Starts" : lambda index, agent_ID: index[agent_ID]["statistics"]["starts_by_zone"].get("offensive", 0)
                # Get total number of starts
            }
        },

        "Game Summary" : {
            "Address" : "Game Summary.json",
            "Endpoints" : {
                "Goals" : lambda index, agent_ID : index[agent_ID]["statistics"]["total"].get("goals", 0),
                "Assists" : lambda index, agent_ID : index[agent_ID]["statistics"]["total"].get("assists", 0),
                "Shots" : lambda index, agent_ID: index[agent_ID]["statistics"]["total"].get("shots", 0),
                "Shots Blocked": lambda index, agent_ID: index[agent_ID]["statistics"]["total"].get("blocked_shots", 0),
                "Blocked Attempts": lambda index, agent_ID: index[agent_ID]["statistics"]["total"].get("blocked_att", 0),
                "Hits" : lambda index, agent_ID : index[agent_ID]["statistics"]["total"].get("hits", 0),

                # Time on Ice
                # "Total Shifts" : lambda index, agent_ID : index[agent_ID]["time_on_ice"].get("shifts", 0),
                # "Total TOI" : lambda index, agent_ID : index[agent_ID]["time_on_ice"].get("total", 0)
            }
        }
    }, 

    "Team" : {
        "Analytics" : {
            "Address" : "Game Analytics.json",
            "Start Date" : lambda d: d["start_time"],
            "Endpoints" : {
                "PDO": lambda index: index["statistics"].get("pdo", 0),
                "Corsi for"    : lambda index: index["statistics"].get("corsi_for", 0),
                "Corsi Total"  : lambda index: index["statistics"].get("corsi_total", 0),
                "Fenwick for"  : lambda index: index["statistics"].get("fenwick_for", 0),
                "Fenwick Total" : lambda index: index["statistics"].get("fenwick_total", 0),
                "Shots For" : lambda index: index["statistics"].get("on_ice_shots_for", 0),
                "Shots Against" : lambda index: index["statistics"].get("on_ice_shots_for", 0),
                "Average Distance" : lambda index: index["statistics"].get("average_shot_distance", 0)
            }
        },

        "Game Summary" : {
            "Address" : "Game Summary.json",
            "Endpoints" : {

                # "Result": lambda index: index["goaltending"]["total"].get("credit", 0),

                # Statistics
                "Goals": lambda index: index["statistics"]["total"].get("goals", 0),
                "Faceoff %" : lambda index: index["statistics"]["total"].get("faceoff_win_pct", 0),
                "Shots for" : lambda index: index["statistics"]["total"].get("shots", 0),
                "Shooting %" : lambda index: index["statistics"]["total"].get("shooting_pct", 0),
                "Shots Blocked" : lambda index: index["statistics"]["total"].get("blocked_shots", 0),
                "Block Attemps" : lambda index: index["statistics"]["total"].get("blocked_att", 0),
                # "Penalties for" : lambda index: ["statistics"]["total"].get("penalties", 0),
                # "Penalties Against" : lambda index: ["statistics"]["total"].get("team_penalties", 0),
                # what's the deal with "powerplays" vs "penalties" vs "team_penalties"
                "Hits" : lambda index: index["statistics"]["total"].get("hits", 0),

                # power play
                "Powerplay Opportunities" : lambda index: index["statistics"]["powerplay"].get("opportunities", 0),
                "Powerplay Faceoff %" : lambda index: index["statistics"]["powerplay"].get("faceoff_win_pct", 0),

                # Goaltending
                "Shots Against" : lambda index: index["goaltending"]["total"].get("total_shots_against", 0),
                "Goals Against" : lambda index: index["goaltending"]["total"].get("total_goals_against", 0),
                "Save %" : lambda index: index["goaltending"]["total"].get("saves_pct", 0)
            }
        }
    }
}



# checks if an agent (player or team) ID exists in a given data sheet. 
# if the agent ID exists, the side "home" or "away" is returned, else: None
def agent_exist(data_sheet, agent_ID):
    for side in ("home", "away"):
        if any(player["id"] == agent_ID for player in data_sheet[side]["players"]):
            return side   # "Home" or "Away"
        elif data_sheet[side].get("id") == agent_ID:
            return side
    else:
        return None
    
# it's probably redundant to make an index for a single player, if we also sometimes create
# an index for a team since all players are contained within the "home" or "away" team.
# handling players individually saves and, although marginally, is probably quicker.
# probably makes the code of the main function cleaner too because you wont have to worry 
# cycling through every player in the larger team index
def agent_index(data_sheet, side, agent_ID):
    with open(r"Data/League Manifest.json", "r") as f:
        manifest = json.load(f)

    if agent_ID in manifest["Players"]: 
        for p in data_sheet[side]["players"]:
            if p["id"] == agent_ID:
                return {agent_ID: p}
            
    if agent_ID in manifest["Teams"]:
        return data_sheet[side]

    return None



# if short_time_frame = 10, long_time_frame = 15
# determines the average of a metric from games -25 : -10, and from -10 to now and finds the difference. 
# this answers the question "is the player performing better in the last 10 games than in the previous 15"
# note that the reference for the long time frame is taken from the short time frame
# this momentum measuring metric is generally good for intermediate timeframes, like the timeframes used for the example
def rolling_difference_in_averages(metric_array, short_time_frame, long_time_frame):

    metric_array = np.array(metric_array)
    recent_average = np.mean(metric_array[-short_time_frame:])
    previous_average = np.mean(metric_array[-short_time_frame-long_time_frame:-short_time_frame])

    difference_in_averages = recent_average - previous_average

    return difference_in_averages



# given a specific player or team (ie agent) ID, generate their 2025 timeseries table. 
def compile_agent_data_2025(agent_ID):

    temp_storing_dict = {}  # temporary storage
    final_dict = {}         # final storage
    Games_25 = r"Data\2025 Game Data"

    with open(r"Data\League Manifest.json", "r") as f:
        league_manifest = json.load(f)
    

    # walk through all of the directories in the 2025 season data
    for subdir, dirs, _ in os.walk(Games_25):
        if not dirs:
            # print(subdir)   # use this to check which files you're looking through
            date = Path(subdir).parts[-2]       # the date of the game. we'll use this to index the time series table


            # --------- if the agent is a player ... --------- #

            if agent_ID in league_manifest["Players"]:
                 
                # cycle through the dicts covering information for each individual information sheet within Game_Metrics["Player"]
                for sheet, values in Game_Metrics["Player"].items():

                    # open the sheet addressed by values["Address"]
                    try:
                        with open(os.path.join(subdir, str(values["Address"])), "r") as f:
                            data = json.load(f)
                    except Exception as e:
                        print(os.path.join(subdir, str(values["Address"])))
                        print(e)

                    # using the Analytics sheet as a "validation" case, check if the agent ID exists in the sheet 
                    # and assign "home" or "away" to "agent_exist_Home_Away"
                    if sheet == "Analytics":
                        agent_exist_Home_Away = agent_exist(data_sheet=data, agent_ID=agent_ID)
                        # sheet_date  = datetime.fromisoformat(values["Start Date"](data)).date() 
                    
                    # if the agent doesnt exist in "analytics" break from cycling the sheets and iterate through to the next date directory 
                    if agent_exist_Home_Away == None:
                        break
                    
                    # pre-index the player's information from each sheet
                    player_index = agent_index(data_sheet=data, side=agent_exist_Home_Away, agent_ID=agent_ID)
                    
                    # store the game metrics addressed by values["Endpoints"], found in the index, and store in the temp_storing_dict
                    for Key, Value in values["Endpoints"].items():
                        temp_storing_dict[Key] = Value(index=player_index, agent_ID=agent_ID)
        
                    # store the metric values by date in the final dict 
                    final_dict[date] = pd.Series(temp_storing_dict, name=False)


            # --------- if the agent is a team ... --------- #
            # repeat the logic commented above ...
            elif agent_ID in league_manifest["Teams"]:
                for sheet, values in Game_Metrics["Team"].items():
                    try:
                        with open(os.path.join(subdir, str(values["Address"])), "r") as f:
                            data = json.load(f)
                    except Exception as e:
                        print(os.path.join(subdir, str(values["Address"])))
                        print(e)

                    if sheet == "Analytics":
                        agent_exist_Home_Away = agent_exist(data_sheet=data, agent_ID=agent_ID)
                        # sheet_date  = datetime.fromisoformat(values["Start Date"](data)).date() 
                        
                    if agent_exist_Home_Away == None:
                        break

                    team_index = agent_index(data_sheet=data, side = agent_exist_Home_Away, agent_ID=agent_ID)

                    for Key, Value in values["Endpoints"].items():
                        temp_storing_dict[Key] = Value(index=team_index)
        
                    final_dict[date] = pd.Series(temp_storing_dict, name=False)



    
    final_dict = pd.DataFrame(final_dict)
    final_dict["Season Average"] = final_dict.mean(axis=1).round(3)
    final_dict["Season Std Dev"] = final_dict.std(axis=1).round(3)
    final_dict["Average L10"] = final_dict.iloc[:, -10:].mean(axis=1).round(3)
    final_dict["Std Dev L10"] = final_dict.iloc[:,-10:].std(axis=1).round(3)
    final_dict['AvL10 - AvL30:L10'] = final_dict.apply(rolling_difference_in_averages, axis=1, args=(10, 20)).round(3)
    
    # this adds a column where we need a 
    # final_dict["Aggregate Goals"] = final_dict.loc["Goals"].cumsum() 
    
                    
    return final_dict




