#!/usr/bin/env python3

# WS server that sends messages at random intervals

import asyncio
import datetime
import random
import websockets
import ssl
import requests
import json
import time

session = requests.session()
base_url = 'https://draft.premierleague.com/'
def fetch_fpl_json(uri):
    url = base_url + uri
    resp = session.get(url)
    return resp.json()

league_id = "305"
inp = input(f"League ID (default noslack @ {league_id}): ")
if(inp != ""):
    league_id = inp

print("Fetching and parsing static information...")
static_info = fetch_fpl_json("/api/bootstrap-static")
details = fetch_fpl_json(f"/api/league/{league_id}/details")
choices_global = fetch_fpl_json(f"/api/draft/{league_id}/choices")["choices"]
print("Done!")

# timestamp used to avoid fetching choices when unnecessary
timestamp = time.time()
def update_timestamp():
    global timestamp
    timestamp = time.time()
 
#CHOICES: entry->team.entry_id element->static.elements[*-1].id 
def league_team_names():
    teams = {}
    for team in details["league_entries"]:
        teams[team["entry_name"]] = []
    return teams

def team_name_fromid(team_id):
    team = static_info["teams"][team_id-1]
    name = f'{team["short_name"]}'
    return name

def team_code_fromid(team_id):
    team = static_info["teams"][team_id-1]
    code = f'{team["code"]}'
    return code

def pos_from_type(t):
    if t == 1:
        return "GK"
    elif t == 2:
        return "DEF"
    elif t == 3:
        return "MID"
    elif t == 4:
        return "FWD"
    else:
        return "UNKNOWN"

def player_obj_fromid(player_id):
    player = static_info["elements"][player_id-1]
    m_player = {}
    m_player["name"] = player["web_name"]
    m_player["id"] = player["id"]
    m_player["team"] = team_name_fromid(player["team"])
    m_player["pos"] = pos_from_type(player["element_type"])
    m_player["team_code"] = team_code_fromid(player["team"])
    return m_player


# Sends the picked players over the websocket
async def serve_picks(websocket, path):
    print("Connection");
    league_teams = league_team_names()

    # Send initial, will provide the teams even if no picks has been made yet
    await websocket.send(json.dumps({"action":"update", "picks":league_teams}))

    pick_index = 0
    while True:
        #choices = fetch_fpl_json(f"/api/draft/{league_id}/choices")["choices"]
        ts = await websocket.ping()
        await ts
        print("Ok")

        #Update the global timestamp to 
        update_timestamp()

        league_teams_update = league_team_names()
        newpicks = False

        # Continue from last checked index to not send duplicates
        while pick_index < len(choices_global):

            # Choices obj is global cache of choices fetched elsewhere
            pick = choices_global[pick_index]

            # Stop when choice has not been made
            if pick["choice_time"] is None:
                break
            else:
                pick_index += 1
                player_name = player_obj_fromid(pick["element"])
                team_entry_name = pick["entry_name"]
                league_teams[team_entry_name].append(player_name)
                league_teams_update[team_entry_name].append(player_name)
                newpicks = True

        # If one or more non-duplicate picks have been found, send message to client
        if newpicks:
            message = {
                    "action":"update", 
                    "picks":league_teams_update
                    }
            await websocket.send(json.dumps(message))

        # Sleep to avoid overload
        await asyncio.sleep(1)
    return league_teams


async def update_choices():
    global timestamp
    last_timestamp = timestamp
    while True:
        print("checking timestamp..")
        if last_timestamp < timestamp:
            print("Timestamp newer, fetching choices")
            choices_global = fetch_fpl_json(f"/api/draft/{league_id}/choices")["choices"]
            last_timestamp = timestamp
        await asyncio.sleep(5)


update_task = asyncio.get_event_loop().create_task(update_choices())
start_server = websockets.serve(serve_picks, 'localhost', 8008)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_until_complete(update_task)

asyncio.get_event_loop().run_forever()
