this folder was created using the following source code

!!!! The name of the folder was changed
##----------------------------------------------------##


URLs = { 
    "Team_Profiles" : "https://api.sportradar.com/nhl/trial/v7/en/teams/{TEAM_ID}/profile.json",
}

TEAM_IDs = {
    
    "COL": "4415ce44-0f24-11e2-8525-18a905767e44",
    # "CHI": "4416272f-0f24-11e2-8525-18a905767e44",

... }

Auth_Key = "L1nM7TmUhyYdeuUAOs1uqZD6z7lmWvlOG446YNFP"
headers = {
    "accept": "application/json",
    "x-api-key": Auth_Key
}


for KEY, VALUEs in TEAM_IDs.items():
    
    url = URLs["Team_Profiles"].format(TEAM_ID=TEAM_IDs[KEY])
    response = requests.get(url, headers=headers)
    with open(f"2024_TEAM_PROFILES/{KEY}.json", "w") as f:
        json.dump(response.json(), f, indent=4)

    time.sleep(1)
