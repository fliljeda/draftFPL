#!/usr/bin/python3
# encoding: utf-8
import json
import time
import os
import shutil
from pathlib import Path

class Vars:
    db_path = "dbdraft"
    curr_gw = 38
    static_info = None
def get_json(filename):
    path = os.path.join(Vars.db_path, filename)
    f = open(path, "r")
    contents = f.read()
    f.close()
    obj = json.loads(contents)
    return obj

###############################  Draft league functions  ##############################################

#Gets the entry ids for the league. Used for identifying points each GW
def get_league_ids():
    league = get_json("league")
    return [team["entry_id"] for team in league["league_entries"]]

# Gets the id (not entry id) for a team by submitting the entry id. Used in the league JSON for some reason
def team_league_entry_id(team_id):
    league = get_json("league")
    for x in league["league_entries"]:
        if team_id == x["id"]:
            return x["entry_id"]


# Gets the id (not entry id) for a team by submitting the entry id. Used in the league JSON for some reason
def team_league_id(team_id):
    league = get_json("league")
    for x in league["league_entries"]:
        if team_id == x["entry_id"]:
            return x["id"]
#######################################################################################################

# param team is value of the identifier to loook at
# param identifier is the identifier to comapre to
# param ret is the team value to return
#   Four identifiers for team (three used): 
#   id: (used as 1-20 as identifiers of players)>
#   name: full name (ex Arsenal, Wolves)
#   short_name: (ex ARS, MCI, BUR)
# Example get_team("MCI", "short_name", "name") returns the name of Manchester City which is Man City
def get_team_static(team, identifier, ret = None):
    for x in Vars.static_info["teams"]:
        if x[identifier] == team:
            return x if ret == None else x[ret]

# param player is value of the identifier to loook at
# param identifier is the identifier to comapre to
# param ret is the player value to return, None if return whole player object
# values: "bonus","web_name","in_dreamteam","influence","element_type","draft_rank","form","penalties_missed","chance_of_playing_this_round","first_name","news_return","news","dreamteam_count","event_points","goals_scored","red_cards","news_updated","chance_of_playing_next_round","assists","creativity","yellow_cards","minutes","goals_conceded","own_goals","status","bps","clean_sheets","news_added","team","total_points","ict_index","threat","saves","penalties_saved","id","ep_next","points_per_game","code","ep_this","second_name","squad_number","added"
def get_player_static(player, identifier, ret = None):
    for x in Vars.static_info["elements"]:
        if x[identifier] == player:
            return x if ret == None else x[ret]

# same as get_player_static but makes a list of all matches instead of first match
def get_players_static(player, identifier, ret = None):
    players = list()
    for x in Vars.static_info["elements"]:
        if x[identifier] == player:
            players.append(x if ret == None else x[ret])
    return players

# id_tup is a tuple of the identifier, example ("short-name", "HUD"). Returns the id of the team
def real_team_id(id_tup):
    if len(id_tup) < 2:
        return -1
    get_team_static(id_tup[0], id_tup[1], "id")


def get_player_average_points(p_id):
    return get_player_static(int(p_id), "id", "points_per_game")


def get_player_name(p_id):
    player = get_player_static(int(p_id), "id")

    name = player["first_name"] + " " + player["second_name"]
    return name
    team_name = get_team_static(player['team'], 'id', 'name')

def get_player_teamname(p_id):
    player = get_player_static(int(p_id), "id")

    team_name = get_team_static(player['team'], 'id', 'name')
    return team_name

def get_team_owner(team_id):
    league = get_json("league")
    for team in league["league_entries"]:
        if team["entry_id"] == team_id:
            return team["player_first_name"] + " " + team["player_last_name"]

def print_first(l, n):
    for x in l:
        if n > 0:
            print(x)
        else:
            return
        n -= 1


def print_list(l):
    for x in l:
        print(x)

def get_players(tokens):
    if len(tokens) <= 1:
        print("What players")

    if tokens[0] == "in":
        team = get_team_static(tokens[1], "short_name", "id")
        print_list([(x["first_name"] + " " + x["second_name"]) for x in get_players_static(team, "team")])
    elif tokens[0] == "id":
        if len(tokens) < 2:
            print("Need id for player")
            return
        player = get_player_static(int(tokens[1]), "id")

        name = player["first_name"] + " " + player["second_name"]
        team_name = get_team_static(player['team'], 'id', 'name')
        print(f"Player: {name} in {team_name}")
    

def cmd_get(tokens):
    if len(tokens) == 0:
        print("Gimme arguments man")
        return
    if tokens[0] == "teams":
        print_list([x["entry_name"] for x in league["league_entries"]])
    elif tokens[0] == "players":
        get_players(tokens[1:])


def fpl_team_points_total(fpl_team_id):
   league = get_json("league") 
   for x in league["standings"]:
       if x["league_entry"] == fpl_team_id:
           return x["total"]

def player_benched(gw_player, gw_team):
    pos = gw_player["position"]
    subbed_in = False
    subbed_out = False
    for sub in gw_team["subs"]:
        if pos == sub["element_out"]:
            subbed_out = True
            break
        elif pos == sub["element_in"]:
            subbed_in = True
            break
            

    if (pos <= 11 and not subbed_out) or (subbed_in):
        return False
    else:
        return True


#Gets the json objects of the benched players from the gameweek's team
def get_benched_players(gw_team):
    players = list()
    for p in gw_team["picks"]:
        if player_benched(p, gw_team):
            players.append(p)

    return players

#Gets the json objects of the playing players from the gameweek's team
def get_playing_players(gw_team):
    players = list()
    for p in gw_team["picks"]:
        if not player_benched(p, gw_team):
            players.append(p)
    return players

# type id: (1,goalkeeper) (2,defender) (3,midfielder) (4,forward)
# Param player_filter is a lambda that 
def points_from_players(team_id, print_trace = False, player_filter = lambda x: True, playing_players = True):
    points = 0
    for gw in range(1, Vars.curr_gw+1):
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        players = get_playing_players(gw_team) if playing_players else get_benched_players(gw_team)
        selected_players = [p["element"] for p in players if (player_filter(p["element"]))]
        gw_event = get_json(f"event-{gw}")
        if print_trace:
            print(f"Gw: {gw}")
        for p in selected_players:
            stats = gw_event["elements"][str(p)]["stats"]
            p_points = stats["total_points"]
            points += p_points
            if print_trace:
                print("\t", get_player_name(p), f" {p_points}p", f" adding to total {points}p")
    return points



def points_from_team_quota(fpl_team, real_team, trace = False):
    points_tot = fpl_team_points_total(team_league_id(fpl_team))
    #points_team = team_points_from_team(fpl_team, real_team, print_trace)
    fil = lambda x: get_player_static(x, "id", "team") == real_team
    points_team = points_from_players(fpl_team, print_trace = trace, player_filter = fil)
    print(points_team, "/", points_tot)

def median_points(team_id):
    point_list = list()
    for gw in range(1, Vars.curr_gw+1):
        gw_points = 0
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        players = get_playing_players(gw_team) 
        selected_players = [p["element"] for p in players]
        gw_event = get_json(f"event-{gw}")
        for p in selected_players:
            stats = gw_event["elements"][str(p)]["stats"]
            p_points = stats["total_points"]
            gw_points += p_points
        point_list.append(gw_points)

    point_list.sort()
    print(point_list)
    median1 = point_list[int(len(point_list)/2)-1]
    median2 = point_list[int(len(point_list)/2)]
    return (median1+median2)/2

def draft_snf_points(team_id):
    gw1_team = get_json(f"team-{str(team_id)}-1")
    players = gw1_team["picks"]
    points = {}
    for gw in range(1, Vars.curr_gw+1):
        gw_points = 0
        selected_players = [p["element"] for p in players]
        gw_event = get_json(f"event-{gw}")
        for p in selected_players:
            stats = gw_event["elements"][str(p)]["stats"]
            p_points = stats["total_points"]
            points[p] = points.get(p, 0) + p_points
    return points

def scouting_points(team_id):
    avg_sum_points = 0
    for gw in range(1, Vars.curr_gw+1):
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        players = get_playing_players(gw_team) 
        selected_players = [p["element"] for p in players]
        gw_event = get_json(f"event-{gw}")
        for p in selected_players:
            avg_player_points = float(get_player_average_points(p))
            stats = gw_event["elements"][str(p)]["stats"]
            p_points = stats["total_points"]
            diff = p_points - avg_player_points
            avg_sum_points += diff
            #if "never" in get_player_name(p):
            #    print(f"{gw}", get_player_name(p), avg_player_points, p_points)

    return avg_sum_points

def points_per_minute(team_id):
    total = fpl_team_points_total(team_league_id(team_id))
    minutes = 0
    for gw in range(1, Vars.curr_gw+1):
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        players = get_playing_players(gw_team) 
        selected_players = [p["element"] for p in players]
        gw_event = get_json(f"event-{gw}")
        for p in selected_players:
            stats = gw_event["elements"][str(p)]["stats"]
            played_minutes = stats["minutes"]
            minutes += played_minutes
            #print(f"{gw}", get_player_name(p), played_minutes)

    return (total/(minutes/90))

def bonus_points_total(team_id):

    bps = 0
    for gw in range(1, Vars.curr_gw+1):
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        players = get_playing_players(gw_team) 
        selected_players = [p["element"] for p in players]
        gw_event = get_json(f"event-{gw}")
        for p in selected_players:
            stats = gw_event["elements"][str(p)]["stats"]
            bps += stats["bps"]
            #print(f"{gw}", get_player_name(p), played_minutes)

    return bps

def yellow_cards(team_id):
    yellows = 0
    for gw in range(1, Vars.curr_gw+1):
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        players = get_playing_players(gw_team) 
        selected_players = [p["element"] for p in players]
        gw_event = get_json(f"event-{gw}")
        for p in selected_players:
            stats = gw_event["elements"][str(p)]["stats"]
            yellows += stats["yellow_cards"]
            #print(f"{gw}", get_player_name(p), played_minutes)

    return yellows

def total_from_team(team_id, stat, player_filter = lambda x: True):
    tot = 0
    for gw in range(1, Vars.curr_gw+1):
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        players = get_playing_players(gw_team) 
        selected_players = [p["element"] for p in players if (player_filter(p["element"]))]
        gw_event = get_json(f"event-{gw}")
        for p in selected_players:
            stats = gw_event["elements"][str(p)]["stats"]
            tot += stats[stat]
            #print(f"{gw}", get_player_name(p), played_minutes)

    return tot

def points_against_team(team_id, real_team_tup = ("HUD","short_name")):
    real_team = get_team_static(real_team_tup[0], real_team_tup[1], "id")
    tot = 0
    for gw in range(1, Vars.curr_gw+1):
        gw_team = get_json(f"team-{str(team_id)}-{gw}")
        gw_event = get_json(f"event-{gw}")
        players = get_playing_players(gw_team) 
        selected_players = [p["element"] for p in players]
        for p in selected_players:
            if get_player_static(p, "id", "team") == real_team:
                continue
            p_fixtures = gw_event["elements"][str(p)]["explain"]
            gw_fixtures = gw_event["fixtures"]
            for p_fix in p_fixtures:
                for gw_fix in gw_fixtures:
                    if (gw_fix["team_a"] == real_team or gw_fix["team_h"] == real_team) and p_fix[1] == gw_fix["id"]:
                        #sum the points from that player that game
                        for pts_src in p_fix[0]:
                            tot += pts_src["points"]


    return tot


def over_tenners():
    obj = dict()
    for gw in range(1, Vars.curr_gw+1):
        gw_event = get_json(f"event-{gw}")
        for key,player in gw_event["elements"].items():
            p_id = key
            p_score = player["stats"]["total_points"]
            if p_score >= 10:
                obj[p_id] = obj.get(p_id, 0) + 1
    return sorted(obj.items(), key=lambda x: x[1], reverse = True)

def transactions_per_team():
    transactions = get_json("transactions")["transactions"]
    obj = dict()
    for ta in transactions:
        t_id = ta["entry"]
        if ta["result"] == "a":
            obj[t_id] = obj.get(t_id, 0) + 1
    return sorted(obj.items(), key = lambda x : x[1], reverse = True)

    

######################## CUSTOMIZED COMMANDS ########################################

def run(commands):
    if len(commands) == 0:
        print("Give me more arguments man")
        return
    cmd = commands[0]
    league_ids = get_league_ids()
    if cmd == "oskar":
        for x in league_ids:
            print(f"{get_team_owner(x)}")
            if x == 7523:
                points_from_team_quota(x, get_team_static("LIV", "short_name", "id"), True)
            else:
                points_from_team_quota(x, get_team_static("LIV", "short_name", "id"))

    elif cmd == "defenders":
        is_defender = lambda x: get_player_static(x, "id", "element_type") <= 2
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            pts = points_from_players(team_id, print_trace = False, player_filter = is_defender)
            print(pts)
    elif cmd == "benched":
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            points_tot = fpl_team_points_total(team_league_id(team_id))
            pts = points_from_players(team_id, print_trace = False, playing_players = False)
            print(pts)
            print(str(pts/(pts+points_tot)) + "%", "of total")
            print("")
    elif cmd == "median":
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            median = median_points(team_id)
            print("median:",median)
            print("")
    elif cmd == "draft":
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            points = draft_snf_points(team_id)
            draft_points = 0
            for k,v in points.items():
                print(get_player_name(k), str(v))
                draft_points += v
            print("Draft total:",draft_points)
            print("")
    elif cmd == "scout":
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            scout_pts = scouting_points(team_id)
            print(scout_pts)
    elif cmd == "ppm":
        print("points per 90min")
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            ppm = points_per_minute(team_id)
            print(ppm)
    elif cmd == "bps":
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            bps = bonus_points_total(team_id)
            print(bps)
    elif cmd == "yellow":
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            yellows = yellow_cards(team_id)
            print(yellows)
    elif cmd == "cs":
        yields_cs_points = lambda x: get_player_static(x, "id", "element_type") <= 3
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            cs = total_from_team(team_id, "clean_sheets", lambda x: yields_cs_points(x))
            print(cs)
    elif cmd == "hud":
        #facing_huddersfield = lambda x: get_player_static(x, "id", "element_type") == real_team_id(("short_name","HUD"))
        for team_id in league_ids:
            print(f"{get_team_owner(team_id)}")
            pts = points_against_team(team_id, ("HUD", "short_name"))
            print(pts)
    elif cmd == "over10":
        print("Most over tenners (>=10 pts):")
        print_first([str(get_player_name(x[0]) + " " + str(x[1])) for x in over_tenners()], 15)
        
    elif cmd == "transactions":
        print("Successful Transactions")
        print_list([str(get_team_owner(x[0]) + " " + str(x[1])) for x in transactions_per_team()])
        
    elif cmd == "null":
        print("Do nothing")
        return
    else:
        print("OK")


###########################################################################################



def print_commands():
    print("Commands:")
    
def main():
    Vars.static_info = get_json("static")
    Vars.curr_gw = get_json("game")["current_event"]
    
    while True:
        inp = input(">")
        cmd_tokens = inp.split()
        if len(cmd_tokens) == 0:
            continue
        cmd = cmd_tokens[0]
        if cmd == "help":
            print_commands()
        elif cmd == "exit" or cmd == "quit" or cmd == "q":
            return
        elif cmd == "get":
            cmd_get(cmd_tokens[1:])
        elif cmd == "run":
            run(cmd_tokens[1:])
        else:
            print("LOL")

main()
