# encoding: utf-8
import requests
import json
import time
from collections import namedtuple

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

PointSource = namedtuple('point_source', ['action', 'count', 'pointsTotal', 'gw_match_num', 'match_id'])

class Player:
    # Static player info. Fetchable with Players.from_id(id)
    _player_repo = {}
    @classmethod
    def init_repo(cls, player_info):
        """Initializes the player repository.
            Static player info can be fetched with Player.from_id(id)
        Parameters
        ----------
        player_info : list
            List of player-objects from Premier League API
        """
        cls._player_repo = {
            data['id']: Player(**data) for data in player_info
        }

    @classmethod
    def from_id(cls, pid):
        """Fetches player object from player-id
        Parameters
        ----------
        pid : int
            FPL id of the player to be fetched
        Returns
        -------
        Player
            A player object with the given id
        """
        return Player._player_repo[pid]

    def __init__(self, **static_info):
        self.__dict__ = static_info
        self._pointsGw = 0
        self._bpsGw = 0
        self.pointsSources = []

    # Backwards compatible api
    @property
    def playerId(self):
        return self.id
    @property
    def name(self):
        return f'{self.first_name} {self.second_name}'

    @property
    def pointsTotal(self):
        return self._pointsGw or int(self.total_points)
    @pointsTotal.setter
    def pointsTotal(self, val):
        self._pointsGw = int(val)

    @property
    def playedMinutes(self):
        return self.minutes
    @property
    def totalGoals(self):
        return self.goals_scored
    @property
    def totalAssists(self):
        return self.assists

    @property
    def position(self):
        return int(self.element_type)

    @property
    def pointsGw(self):
        return self._bpsGw or int(self.event_points)
    @pointsGw.setter
    def pointsGw(self, val):
        self._bpsGw = int(val)


    def __repr__(self):
        """Class representation.
            The representation string will look like:
            >>> print(player)
            Player(id = 1, assists = 0, bonus = 3, ...)

            Properties are not included in these.
        """
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(f'{key} = {self.__dict__[key]}' for key in vars(self))
        )

Player.init_repo(static_info['elements'])

class Team:
    """Adapter class for the team information fetched from the FPL API
    
    Adapter class converting the FPL API to a nicer and easily 
    usable format. The input is the data returned from the API.
    Fields were renamed to keep backwards compatability.
    """
    def __init__(self, **static_info):
        self.__dict__ = static_info
        self.players = []
        self.player_positions = {}

        self._pointsTotal = 0
        self._pointsGw = 0
    
    # Preserving old API
    @property
    def teamId(self):
        return self.id

    @property
    def owner(self):
        return f'{self.player_first_name} {self.player_last_name}'
    
    @property
    def pointsTotal(self):
        return self._pointsTotal or self.overall_points

    @pointsTotal.setter
    def pointsTotal(self, val):
        self._overall_points = val
        
    @property
    def pointsGw(self):
        return self._pointsGw or self.event_points
    
    @pointsGw.setter
    def pointsGw(self, val):
        self._pointsGw = val

    def benched(self, pid):
        """ Checks if a player is benched or on the field.
            A player is benched if their position is > 11.
        Arguments
        ---------
        pid : int
            The id of the player
        Returns
        -------
        bool
            True if the player is benched, False otherwise
        """
        return self.player_positions[pid] > 11
        
    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(f'{key} = {self.__dict__[key]}' for key in vars(self))
        )

class LeagueInfo:
    def __init__(self):
        self.leagueId = None
        self.currentGw = None
        self.teams = list()

def sortLeague(league, gameweek = True):
    if gameweek:
        league.teams = sorted(league.teams, key=lambda x: x.pointsGw, reverse=True)
    else:
        league.teams = sorted(league.teams, key=lambda x: x.pointsTotal, reverse=True)

#Fill information about the league and the teams. Uses current gameweek for team details
def setLeagueInformation(leagueObj):
    leagueJson = fetchFplJson("api/league/" + str(leagueObj.leagueId) + "/details");
    gameJson = fetchFplJson("api/game");
    leagueObj.currentGw = gameJson["current_event"]
    for leagueEntry in leagueJson["league_entries"]:
        response = fetchFplJson(f'api/entry/{leagueEntry["entry_id"]}/public')["entry"]
        team_obj = Team(**response)
        
        teamGwJson = fetchFplJson(f'api/entry/{team_obj.teamId}/event/{leagueObj.currentGw}')
        team_obj.players = [Player.from_id(pick['element']) for pick in teamGwJson['picks']]
        team_obj.player_positions = { pick['element']: pick['position'] for pick in teamGwJson['picks'] }

        leagueObj.teams.append(team_obj)



def updateScores(league):
    liveJson = fetchFplJson("api/event/" + str(league.currentGw) + "/live")["elements"]
    for team in league.teams:

        pointsGwPlayers = 0
        for player in team.players:
            playerStats = liveJson[str(player.playerId)]["stats"]
            player.pointsGw = playerStats["total_points"]
            player.bpsGw = playerStats["bps"]

            if not team.benched(player.id):
                pointsGwPlayers += player.pointsGw
            
            explanation = liveJson[str(player.playerId)]["explain"]
            if len(explanation) == 0:
                player.pointSources = list()
            else:
                for idx, match in enumerate(explanation):
                    for sourceJson in match[0]:
                        source = PointSource(action = sourceJson['name'],
                                             count = sourceJson['value'],
                                             pointsTotal = sourceJson['points'],
                                             gw_match_num = idx,
                                             match_id = match[1])
                        player.pointsSources.append(source)


        teamPubJson = fetchFplJson("api/entry/" + str(team.teamId) + "/public")["entry"];
        pubOverallPts = teamPubJson["overall_points"] #Not live updated
        pubEventPts = teamPubJson["event_points"] #Not live updated
        
        team.pointsTotal = pointsGwPlayers  + int(pubOverallPts) - int(pubEventPts)
        team.pointsGw = pointsGwPlayers

###########################################################
####### Initialize league, teams and players ##############
###########################################################
league = LeagueInfo()
league.leagueId = "2150"
setLeagueInformation(league)


###########################################################
###########################################################
###########################################################
updateScores(league)
