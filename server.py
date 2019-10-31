import requests
import argparse
import asyncio
import json
import logging
import websockets
import pickle
import os.path
import random
from collections import namedtuple
from game import Game

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
wslogger = logging.getLogger("websockets")
wslogger.setLevel(logging.WARN)

logger = logging.getLogger("Server")
logger.setLevel(logging.INFO)

Player = namedtuple("Player", ["name", "ws"])

MAX_HIGHSCORES = 10
HIGHSCORE_FILE = "highscores.json"


class Game_server:
    def __init__(self, level, lives, timeout, grading):
        self.game = Game(level, lives, timeout)
        self.players = asyncio.Queue()
        self.viewers = set()
        self.current_player = None
        self.grading = grading

        self._highscores = []
        if os.path.isfile(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r") as infile:
                self._highscores = json.load(infile)

    def save_highscores(self):
        # update highscores
        logger.debug("Save highscores")
        logger.info("FINAL SCORE <%s>: %s with %s steps", self.current_player.name, self.game.score, self.game.total_steps)

        self._highscores.append((self.current_player.name, self.game.score))
        self._highscores = sorted(self._highscores, key=lambda s: -1 * s[1])[
            :MAX_HIGHSCORES
        ]

        with open(HIGHSCORE_FILE, "w") as outfile:
            json.dump(self._highscores, outfile)

    async def incomming_handler(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                if data["cmd"] == "join":
                    if path == "/player":
                        logger.info("<%s> has joined", data["name"])
                        await self.players.put(Player(data["name"], websocket))

                    if path == "/viewer":
                        logger.info("Viewer connected")
                        self.viewers.add(websocket)
                        if self.game.running:
                            game_info = self.game.info()
                            game_info["highscores"] = self._highscores
                            await websocket.send(json.dumps(game_info))

                if data["cmd"] == "key" and self.current_player.ws == websocket:
                    logger.debug((self.current_player.name, data))
                    if len(data["key"]):
                        self.game.keypress(data["key"][0])
                    else:
                        self.game.keypress("")

        except websockets.exceptions.ConnectionClosed as c:
            logger.info(f"Client disconnected: {c}")
            if websocket in self.viewers:
                self.viewers.remove(websocket)

    async def mainloop(self):
        while True:
            logger.info("Waiting for players")
            self.current_player = await self.players.get()

            if self.current_player.ws.closed:
                logger.error(f"<{self.current_player.name}> disconnect while waiting")
                continue

            try:
                logger.info(f"Starting game for <{self.current_player.name}>")
                self.game.start(self.current_player.name)
                
                #Send game info to viewer and player
                game_info = self.game.info()
                game_info["highscores"] = self._highscores
                if self.viewers:
                    await asyncio.wait(
                        [
                            client.send(json.dumps(game_info))
                            for client in self.viewers
                        ]
                    )
                await self.current_player.ws.send(json.dumps(game_info))


                if self.grading:
                    game_rec = dict()
                    game_rec["player"] = self.current_player.name

                while self.game.running:
                    await self.game.next_frame()
                    await self.current_player.ws.send(self.game.state)
                    if self.viewers:
                        await asyncio.wait(
                            [client.send(self.game.state) for client in self.viewers]
                        )
                self.save_highscores()
                await self.current_player.ws.send(
                    json.dumps({"score": self.game.score})
                )

                logger.info(f"Disconnecting <{self.current_player.name}>")
            except websockets.exceptions.ConnectionClosed:
                self.current_player = None
            finally:
                try:
                    if self.grading:
                        game_rec["score"] = self.game.score
                        game_rec["total_steps"] = self.game.total_steps
                        game_rec["level"] = self.game.map.level
                        requests.post(self.grading, json=game_rec)
                except:
                    logger.warning("Could not save score to server")

                if self.current_player:
                    await self.current_player.ws.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", help="IP address to bind to", default="")
    parser.add_argument("--port", help="TCP port", type=int, default=8000)
    parser.add_argument("--level", help="start on level", type=int, default=1)
    parser.add_argument("--lives", help="Number of lives", type=int, default=3)
    parser.add_argument("--seed", help="Seed number", type=int, default=0)
    parser.add_argument(
        "--timeout", help="Timeout after this amount of steps", type=int, default=3000
    )
    parser.add_argument(
        "--grading-server",
        help="url of grading server",
        default="http://bomberman-aulas.ws.atnog.av.it.pt/game",
    )
    args = parser.parse_args()

    if args.seed > 0:
        random.seed(args.seed)

    g = Game_server(args.level, args.lives, args.timeout, args.grading_server)

    game_loop_task = asyncio.ensure_future(g.mainloop())

    logger.info(f"Listenning @ {args.bind}:{args.port}")
    websocket_server = websockets.serve(g.incomming_handler, args.bind, args.port)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(websocket_server, game_loop_task))
    loop.close()
