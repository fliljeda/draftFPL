#!/usr/bin/env python3

from leagueinfo import *

print(f"Current gw: {league.currentGw}")
updateGameInfo(league)
for team in league.teams:
    print(f"Team: {team.name}")
    x = team.pointsTotal
    print(f"Points: {x}")
    for p in team.players:
        if not team.benched(p.id):
            print(f"\t {p.name}")
