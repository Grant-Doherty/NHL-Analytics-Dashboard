
import requests
import json 
import os
import time
from datetime import date, timedelta


#
#       this is used to import data from the API. This can be run from the computer terminal. Define the start_date and end_date before running the program
#       the start and end dates are inclusive. 
#


# URL address to make API calls. we'll only really look at the Game Summary, Game Analytics, and Game Shot Zones. Each of these requiring the Game ID to be defined. 
URLs = { 
    "Team_Profiles" : "https://api.sportradar.com/nhl/trial/v7/en/teams/{TEAM_ID}/profile.json",
    "Seasonal Analytics" : "https://api.sportradar.com/nhl/trial/v7/en/seasons/{SEASON}/REG/teams/{TEAM_ID}/analytics.json",    # The SEASON value is the year the season started
    "Seasonal Statistics" : "https://api.sportradar.com/nhl/trial/v7/en/seasons/{SEASON}/REG/teams/{TEAM_ID}/statistics.json",
    "Player Profile" : "https://api.sportradar.com/nhl/trial/v7/en/players/{PLAYER_ID}/profile.json",
    "Daily Schedule" : "https://api.sportradar.com/nhl/trial/v7/en/games/{DATE}/schedule.json",
    "Game Analytics" : "https://api.sportradar.com/nhl/trial/v7/en/games/{GAME_ID}/analytics.json",
    "Game Boxscore" : "https://api.sportradar.com/nhl/trial/v7/en/games/{GAME_ID}/boxscore.json",
    "Game Faceoffs" : "https://api.sportradar.com/nhl/trial/v7/en/games/{GAME_ID}/faceoffs.json",
    "Game Shot Zones" : "https://api.sportradar.com/nhl/trial/v7/en/games/{GAME_ID}/shot_zones.json",
    "Game Summary" : "https://api.sportradar.com/nhl/trial/v7/en/games/{GAME_ID}/summary.json",
    "Game Time on Ice" : "https://api.sportradar.com/nhl/trial/v7/en/games/{GAME_ID}/time_on_ice.json",

}

# API arguments
headers = {
    "accept": "application/json",
    "x-api-key": ""                 # Authentication key sensored for licensing purposes
}

# define start and end dates to update
start_date, end_date = date(2025, 10, 14), date(2026, 1, 5)#, date(2026, 4, 18)

# the specific endpoints we'll iterate through. 
endpoints = ["Game Summary", "Game Analytics", "Game Shot Zones"]

# JSON Schedule of dates : {all game id's of this date}
with open(r"Data\2025_SEASON_SCHEDULE.json", "r") as f: 
    schedule = json.load(f)

# iterate through dates from current to end_date

# stepping through dates beginning with the defined start_date 
current = start_date
while current <= end_date:

    # array of game id's for the "current" date
    game_ids = schedule.get(current.strftime("%Y-%m-%d"), [])   # returns [] if key doesn’t exist
    
    print(f"Importing Data from {current.strftime('%Y-%m-%d')}...")


# ---------- This sucks, but we have to check if files already exist by checking if the folder is made ---------- #
# ----------   Other methods involve making an API call to make the check. I don't have enough calls   ----------#
    if os.path.isdir(fr"Data\2025 Game Data\{current.strftime('%Y-%m-%d')}"):
        print(f"Game Data from {current.strftime('%Y-%m-%d')} already complete... Skipping...")
        current += timedelta(days=1)
        continue 

    # Download process
    else:

        # iterate through the game ids from the "current" date
        for i, game in enumerate(game_ids):
            print(f"Importing Game Data {i+1}/{len(game_ids)}")


            # for each game, iterate through each endpoint and fetch the data 
            for endpoint in endpoints:
                URL = URLs[endpoint].format(GAME_ID=game)
                response = requests.get(URL, headers=headers)

                 # check for too many requests error (429), if so, wait 2s, then retry. retry until successful. 
                while response.status_code == 429:
                    print(f"Too many requests on{endpoint} for {game}. Waiting...")
                    time.sleep(2)
                    print("Retrying...")
                    response = requests.get(URL, headers=headers)

                # print if there is an error (ie, the status code is not error free (!= 200))
                if response.status_code != 200:
                    print(f"Error {response.status_code} for {endpoint} ({game})")
                    continue

                 # set the API call to "data"
                data = response.json()

                # create a game folder, only make it once. we'll iterate through all the endpoints, so we'll only create the folder when we reach the first endpoint, ie "Game Summary"
                if endpoint == "Game Summary":
                    path = fr"Data\2025 Game Data\{current.strftime('%Y-%m-%d')}\{data['away']['market']} vs {data['home']['market']}"
                    os.makedirs(path, exist_ok=True)

                # dump the data into the appropriate .json file
                with open(f"{path}\{endpoint}.json", "w") as f:
                    json.dump(data, f, indent = 4)


    # pause as to not exhaust the API, and iterate to the next day 
    time.sleep(0.2)
    current += timedelta(days=1)
    











