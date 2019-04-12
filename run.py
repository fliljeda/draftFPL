import requests
import json
import time

session = requests.session()

base_url = 'https://draft.premierleague.com/'


def fetchFplJson(uri):
    url = base_url + uri
    resp = session.get(url)
    return json.loads(resp.text)

########################################################
######        Create the static info     ###############
########################################################
print("Fetching and parsing static information...")
static_info = fetchFplJson("/api/bootstrap-static")
print("Done!")
########################################################
########################################################
########################################################

class PointSource:
    def __init__(self):
        self.action = None
        self.count = None
        self.pointsTotal = None

class Player:
    def __init__(self):
        #team based
        self.position = None #Position in teamselection I think. 1-11 on pitch, 12-15 on bench

        #static
        self.name = None
        self.playerId = None
        self.pointsTotal = None
        self.form = None
        self.playedMinutes = None
        self.totalGoals = None
        self.totalAssists = None


        #gw
        self.pointsGw = None
        self.bpsGw = None
        self.pointsSources = list() 


class Team:
    def __init__(self):
        self.teamId = None
        self.name = None
        self.owner = None
        self.players = list()
        self.pointsGw = None
        self.pointsTotal = None

class LeagueInfo:
    def __init__(self):
        self.leagueId = None
        self.currentGw = None
        self.teams = list()

def sortLeague(league):
    league.teams = sorted(league.teams, key=lambda x: x.pointsTotal, reverse=True)


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
    leagueObj.currentGw = gameJson["current_event"]
    for leagueEntry in leagueJson["league_entries"]:
        tmp = Team()
        #Set team meta-information
        setTeamInformation(tmp, leagueEntry["entry_id"],leagueObj.currentGw)

        leagueObj.teams.append(tmp)

###########################################################
####### Initialize league, teams and players ##############
###########################################################
league = LeagueInfo()
league.leagueId = "2150"
setLeagueInformation(league)

sortLeague(league)

###########################################################
###########################################################
###########################################################


def updateScores(league):
    liveJson = fetchFplJson("api/event/" + str(league.currentGw) + "/live")["elements"]
    for team in league.teams:
        pointsGw = 0
        for player in team.players:
            playerStats = liveJson[str(player.playerId)]["stats"]
            player.pointsGw = playerStats["total_points"]
            player.bpsGw = playerStats["bps"]

            pointsGw += int(player.pointsGw)
            
            explanation = liveJson[str(player.playerId)]["explain"]
            if len(explanation) == 0:
                player.pointSources = list()
            else:
                for sourceJson in explanation[0][0]:
                    source = PointSource()
                    source.action = sourceJson["name"]
                    source.count = sourceJson["value"]
                    source.pointsTotal = sourceJson["points"]
                    player.pointsSources.append(source)
        team.pointsGw = pointsGw


updateScores(league)

writer.pra(league)


html_base = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/css/bootstrap.min.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/js/bootstrap.min.js"></script>

    <script>
        setTimeout(function(){
           window.location.reload(1);
        }, 5000);
    </script>
    <title>
        No Slack Draft Current GW Standings
    </title>
</head>
<body> 

"""

html_end = """
</body>
"""


def buildHtmlTeam(team):
    html_text = """
    <div class="panel panel-default">
        <div class="panel-heading"> 
        <p><font size="8">
    """
    html_text+= str(team.name) + " - " + str(team.pointsGw)

    html_text += """
        </font></p> 
        </div>
    <div class="panel-body">
    """
    for player in team.players:
        html_text += "<p>" + str(player.name) + " - " + str(player.pointsGw) + "p" + "</p>"

    html_text += """        
        </div>
    </div>
    """
    return html_text

html_final = html_begin
for team in league.teams:
    html_final += buildHtmlTeam(team)

html_final += html_end



#for t in league.teams:
#    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
#    print("Team: " + str(t.name))
#    print("Owner: " + str(t.owner))
#    print("Players:")
#    for p in t.players:
#        print("------------------------")
#        print("\t Name: " + str(p.name))
#        print("\t Points GW: " + str(p.pointsGw))
#        if len(p.pointsSources) == 0:
#            continue
#        print("\t Sources for points: ")
#        for s in p.pointsSources:
#            print("\t\t " + str(s.count) + " " + str(s.action) + " for " + str(s.pointsTotal) + " points")
#    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")


