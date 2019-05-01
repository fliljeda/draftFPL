#!/usr/bin/env python

# WS server that sends messages at random intervals

from leagueinfo import *
import asyncio
import datetime
import random
import websockets
import json
import ssl

async def updateInfoAsync():
    while True:
        updateScores(league)
        sortLeague(league, gameweek=False)
        await asyncio.sleep(15)

async def sendScores(websocket, path):
    while True:
        print("Sending scores")
        msg = json.dumps([1,2,3,4,5,6])

        obj = []
        for x in league.teams:
            tmp = {"name":x.name, "points-total":x.pointsTotal, "points-gw":x.pointsGw}
            obj.append(tmp)
            
        msg = json.dumps(obj)
        await websocket.send(msg)
        await asyncio.sleep(5)


updateTask = asyncio.get_event_loop().create_task(updateInfoAsync())
start_server = websockets.serve(sendScores, 'localhost', 8008)


asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_until_complete(updateTask)

asyncio.get_event_loop().run_forever()
