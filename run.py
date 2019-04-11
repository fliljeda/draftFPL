import requests
import json
import time

session = requests.session()

base_url = 'https://draft.premierleague.com/'


def fetchFplJson(uri):
    url = base_url + uri
    resp = session.get(url)
    return json.loads(resp.text)

print("Fetching and parsing static information...")
static_info = fetchFplJson("/api/bootstrap-static")
print("Done!")

class PointSource:
    action = None
    count = None
    pointsTotal = None

class Player:
    #team based
    position = None #Position in teamselection I think. 1-11 on pitch, 12-15 on bench

    #static
    name = None
    playerId = None
    pointsTotal = None
    form = None
    playedMinutes = None
    totalGoals = None
    totalAssists = None


    #gw
    pointsGw = None
    bonusPointsGw = None
    pointsSources = list() 


class Team:
    teamId = None
    name = None
    owner = None
    players = list()
    pointsGw = None
    pointsTotal = None

class LeagueInfo:
    leagueId = None
    currentGw = None
    teams = list()


#Assumes correct player id. Else it crashes or returns wrong player
def getStaticPlayerJson(playerId):
    player_info = static_info["elements"][playerId-1]
    if player_info["id"] != playerId:
        #Heuristic of 1-indexed entry->player does not match. Search for correct 
        for player_element in static_info["elements"]:
            if player_element["id"] == playerId:
                player_info = player_element
                break
    return player_info


def setPlayerInformation(playerObj, playerId):
    playerJson = getStaticPlayerJson(playerId)
    playerObj.playerId = playerId
    playerObj.name = playerJson["first_name"] + " " + playerJson["second_name"]
    playerObj.pointsTotal = playerJson["total_points"]
    playerObj.pointsGw = playerJson["event_points"]
    playerObj.playedMinutes = playerJson["minutes"]
    playerObj.totalGoals = playerJson["assists"]
    playerObj.totalAssists = playerJson["goals_scored"]

    playerObj.form = playerJson["form"]


#Sets initial team information, such as current players and the total points 
#(note that points may not be updated during matches)
def setTeamInformation(teamObj, teamId, gw):
    teamPubJson = fetchFplJson("api/entry/" + str(teamId) + "/public")["entry"];
    teamObj.name = teamPubJson["name"]
    teamObj.teamId = teamPubJson["id"]
    teamObj.owner = teamPubJson["player_first_name"] + " " + teamPubJson["player_last_name"]

    teamObj.pointsTotal = teamPubJson["overall_points"] #Not live updated
    teamObj.pointsGw = teamPubJson["event_points"] #Not live updated

    teamGwJson = fetchFplJson("api/entry/" + str(teamObj.teamId) + "/event/" + str(gw));
    for pick in teamGwJson["picks"]:
        player = Player()
        setPlayerInformation(player, pick["element"])
        teamObj.players.append(player)

#Fill information about the league and the teams. Uses current gameweek for team details
def setLeagueInformation(leagueObj):
    leagueJson = fetchFplJson("api/league/" + str(leagueObj.leagueId) + "/details");
    gameJson = fetchFplJson("api/game");
    leagueObj = LeagueInfo()
    leagueObj.currentGw = gameJson["current_event"]
    for leagueEntry in leagueJson["league_entries"]:
        tmp = Team()
        #Set team meta-information
        setTeamInformation(tmp, leagueEntry["entry_id"],leagueObj.currentGw)

        leagueObj.teams.append(tmp)


league = LeagueInfo
league.leagueId = "2150"
setLeagueInformation(league)

league.teams = sorted(league.teams, key=lambda x: x.pointsTotal, reverse=True)
for x in league.teams:
    print(str(x.name) + " - " + str(x.pointsTotal))
