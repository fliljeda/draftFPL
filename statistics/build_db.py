#!/usr/bin/python3
# encoding: utf-8
import requests
import json
import time
import os
import shutil
from pathlib import Path
from collections import namedtuple


class fpl_api:

    session = requests.session()
    base_url = 'https://draft.premierleague.com/api/'

    def fetch(uri):
        url = fpl_api.base_url + uri
        resp = fpl_api.session.get(url)
        if resp.status_code == 404:
            print(f"Endpoint {url} does not exist")
            return None
        return json.loads(resp.text)

    def fetch_join(*args):
        uri = ""
        joinSlash = False
        for component in args:
            if joinSlash:
                uri += "/"
            else:
                joinSlash = True
            uri += component
        return fpl_api.fetch(uri)

    def fetch_raw(uri):
        url = fpl_api.base_url + uri
        resp = fpl_api.session.get(url)
        if resp.status_code == 404:
            print(f"Endpoint {url} does not exist")
            return None
        return resp.text

# Asks user for confirmation to continue, aborts if none is given
def yes_or_no(question = "Continue?", tries = 3):
    ready = False
    for x in range(tries):
        inp = input(f"({x+1}/{tries}) {question} (y/N): ")
        inp = inp.strip()
        if inp == "n" or inp == "N":
            ready = False
            print("Ok. Aborting...")
            exit(0)
        elif inp == "y" or inp == "Y":
            ready = True
            break
    return ready


# Removes path if it already exists. Create path
def prepare_dbpath(path):
    if path.exists():
        remove = yes_or_no(f"{path} already exists. Remove? (abort otherwise)")
        if not remove:
            print("Aborting...")
            exit(0)

        if path.is_dir():
            shutil.rmtree(path)
        else:
            os.remove(path)
    os.mkdir(path)

# Resolves the location for the database and returns it
def resolve_database_location():
    print("Resolve")
    dir_default = "dbdraft"
    rel_path = input(f"Name of folder to store dabase in (default {dir_default}): ")
    if rel_path == "":
        rel_path = dir_default
    path = Path(rel_path)
    print(f"Chosen path: {os.path.abspath(path)}")
    
    prepare_dbpath(path)
    return path
        
    

def write_file(db_path, name, contents):
    filename = os.path.join(db_path, name)
    print(f"Writing {filename}")
    f= open(filename,"w+")
    f.write(contents)
    f.close()


def build_static_data(db_path):
    json_text = fpl_api.fetch_raw("bootstrap-static")
    write_file(db_path, "static", json_text)

def build_game_data(db_path):
    json_text = fpl_api.fetch_raw("game")
    write_file(db_path, "game", json_text)

def build_transactions_data(db_path, league_id):
    json_text = fpl_api.fetch_raw(f"draft/league/{league_id}/transactions")
    write_file(db_path, "transactions", json_text)

def build_events_data(db_path):
    curr_gw = fpl_api.fetch("game")["current_event"]
    for x in range(1, curr_gw+1):
        json_text = fpl_api.fetch_raw(f"event/{str(x)}/live")
        write_file(db_path, f"event-{str(x)}", json_text)

    return curr_gw

def build_league_details(db_path, league_id):
    json_text = fpl_api.fetch_raw(f"league/{league_id}/details")
    write_file(db_path, "league", json_text)

    #extract league teams
    teams_json = json.loads(json_text)
    teams = list()
    for team_json in teams_json["league_entries"]:
        teams.append(team_json["entry_id"])
    return teams


def build_team_details(db_path, teams, gameweeks):
    for team_id in teams:
        for gw in range(1, gameweeks+1):
            json_text = fpl_api.fetch_raw(f"entry/{str(team_id)}/event/{str(gw)}")
            write_file(db_path, f"team-{str(team_id)}-{str(gw)}", json_text)
    return 0

def build_database(db_path, league_id):
    build_static_data(db_path)
    build_transactions_data(db_path, league_id)
    build_game_data(db_path)
    gameweeks = build_events_data(db_path)
    teams = build_league_details(db_path, league_id)
    build_team_details(db_path, teams, gameweeks)

    

# Initial setup
def start_build_database():
    league_id = input("Enter League ID: ")
    s = fpl_api.fetch(f"league/{league_id}/details")
    if s == None:
        print("Could not fetch league details. Aborting...")
        exit(0)
    else:
        print(f"League: {s['league']['name']}")

    ready = yes_or_no("Are you ready to begin building database?", tries = 3)

    if not ready:
        print("Aborting...")
        exit(0)
    db_path = resolve_database_location()
    print(f"Placing database in {db_path}")
    print("OK, lets build")


    build_database(db_path, league_id)

start_build_database()
