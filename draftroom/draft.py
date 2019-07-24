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
print("Done!")
 
#CHOICES: entry->team.entry_id element->static.elements[*-1].id 
def league_team_names():
    teams = {}
    for team in details["league_entries"]:
        print(team["entry_name"])
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

def choices():
    choices = fetch_fpl_json(f"/api/draft/{league_id}/choices")
    league_teams = league_team_names()
    for pick in choices["choices"]:
        if pick["choice_time"] is None:
            break
        player_name = player_obj_fromid(pick["element"])
        league_teams[pick["entry_name"]].append(player_name)
    return league_teams

async def update_choices(websocket, path):
    print("Connection");
    league_teams = league_team_names()
    await websocket.send(json.dumps({"action":"update", "picks":league_teams}))
    pick_index = 0
    while True:
        choices = fetch_fpl_json(f"/api/draft/{league_id}/choices")["choices"]
        league_teams_update = league_team_names()
        newpicks = False
        while pick_index < len(choices):
            pick = choices[pick_index]
            if pick["choice_time"] is None:
                print("No new choices")
                break
            else:
                print("Found next pick")
                pick_index += 1
                player_name = player_obj_fromid(pick["element"])
                league_teams[pick["entry_name"]].append(player_name)
                league_teams_update[pick["entry_name"]].append(player_name)
                newpicks = True
        if newpicks:
            print("Sending through websocket..")
            message = {"action":"update", "picks":league_teams_update}
            await websocket.send(json.dumps(message))
        await asyncio.sleep(5)
    return league_teams

#print(choices())



start_server = websockets.serve(update_choices, 'localhost', 8008)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
