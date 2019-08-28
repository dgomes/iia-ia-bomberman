import random
import sys
import json
import asyncio
import websockets
import pygame
import os
from mapa import Map

import pygame
pygame.init()

async def agent_loop(server_address = "localhost:8000", agent_name="student"):
    async with websockets.connect("ws://{}/player".format(server_address)) as websocket:

        # Receive information about static game properties 
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg) 
         
        mapa = Map(size = game_properties['size'], mapa = game_properties['map'])

        while True:
            try:
                state = json.loads(await websocket.recv()) #receive game state
                print(state)
                key = ""
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or not state['lives']:
                        pygame.quit() #sys.exit() if sys is imported
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            key = 'w'
                        elif event.key == pygame.K_LEFT:
                            key = 'a'
                        elif event.key == pygame.K_DOWN:
                            key = 's'
                        elif event.key == pygame.K_RIGHT:
                            key = 'd'
                        elif event.key == pygame.K_z:
                            key = 'A'
                        elif event.key == pygame.K_x:
                            key = 'B'

                        #send new key
                        await websocket.send(json.dumps({"cmd": "key", "key": key}))
                        break
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

loop = asyncio.get_event_loop()
SERVER = os.environ.get('SERVER', 'localhost')
PORT = os.environ.get('PORT', '8000')
NAME = os.environ.get('NAME', 'student')
loop.run_until_complete(agent_loop("{}:{}".format(SERVER,PORT), NAME))
