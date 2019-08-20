import math
import os
import asyncio
import json
import logging
import pickle
from map import Map, Tiles

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

LIVES = 3
INITIAL_SCORE = 0
TIMEOUT = 3000 
MAX_HIGHSCORES = 10
GAME_SPEED = 10 

class Game:
    def __init__(self, level=1, lives=LIVES, timeout=TIMEOUT):
        logger.info("Game({}, {})".format(level, lives))
        self._running = False
        self._timeout = timeout
        self._score = 0
        self._state = {}
        self._initial_lives = lives
        self.map = Map()
        self._enemies = self.map.enemies_spawn
        
        self._highscores = [] 
        if os.path.isfile(f"{level}.score"):
            with open(f"{level}.score", 'r') as infile:
                self._highscores = json.load(infile)

    def info(self):
        return json.dumps({"level": self.map.level,
                           "size": self.map.size,
                           "map": self.map.map,
                           "enemies": self._enemies,
                           "fps": GAME_SPEED,
                           "timeout": TIMEOUT,
                           "lives": LIVES,
                           "score": self.score,
                           "highscores": self.highscores,
                            })

    def consume(self, pos):
        """Update map at position."""
        if pos in self._powerups:
            self._powerups.remove(pos)
            return Tiles.POWERUPS 
        if pos in self._bonus:
            self._bonus.remove(pos)
            return Tiles.BONUS

    @property
    def running(self):
        return self._running

    @property
    def score(self):
        return self._score

    @property
    def highscores(self):
        return self._highscores

    def start(self, player_name):
        logger.debug("Reset world")
        self._player_name = player_name
        self._running = True
        
        self.map = Map()
        self._step = 0
        self._bomberman = self.map.bomberman_spawn
        self._walls = self.map.walls
        self._powerups = []
        self._bonus = []
        self._lastkeypress = "" 
        self._score = INITIAL_SCORE 
        self._lives = self._initial_lives 

    def stop(self):
        logger.info("GAME OVER")
        self.save_highscores()
        self._running = False

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def save_highscores(self):
        #update highscores
        logger.debug("Save highscores")
        logger.info("FINAL SCORE <%s>: %s", self._player_name, self.score)
        self._highscores.append((self._player_name, self.score))
        self._highscores = sorted(self._highscores, key=lambda s: -1*s[1])[:MAX_HIGHSCORES]
    
        with open(self.map._filename+".score", 'w') as outfile:
            json.dump(self._highscores, outfile)

    def keypress(self, key):
        self._lastkeypress = key

    def update_bomberman(self):
        try:
            self._bomberman = self.map.calc_pos(self._bomberman, self._lastkeypress) 
        except AssertionError:
            logger.error("Invalid key <%s> pressed", self._lastkeypress)

        c = self.consume(self._bomberman)
        #process consume

        if len(self._enemies) == 0: #and c == Tiles.EXIT
            logger.info("Level completed")
            self._score += ((self._timeout - self._step) // TIME_BONUS_STEPS) * POINT_TIME_BONUS 
            self.stop()

    def in_range(self, p1, p2, d):
        px, py = p1
        gx, gy = p2
        distance = math.hypot(px-gx, py-gy)
        return distance <= d

    def collision(self):
        for e in self._enemies:
            if e.pos == self._bomberman:
                logger.info("bomberman has died")
                if self._lives:
                    self._lives -= 1
                    self._bomberman = self.map.bomberman_spawn
                    self._enemies = self.map.enemies #TODO don't respawn everyone
                else:
                    self.stop()
                    return

    async def next_frame(self):
        await asyncio.sleep(1./GAME_SPEED)

        if not self._running:
            logger.info("Waiting for player 1")
            return

        self._step += 1
        if self._step == self._timeout:
            self.stop()

        if self._step % 100 == 0:
            logger.debug("[{}] SCORE {} - LIVES {}".format(self._step, self._score, self._lives))
  
        self.update_bomberman()
        self.collision()
       
        for enemy in self._enemies:
            enemy.update(self._state, self._enemies)
        self.collision()
        
        self._state = {"step": self._step,
                       "player": self._player_name,
                       "score": self._score,
                       "lives": self._lives,
                       "bomberman": self._bomberman,
                       "enemies": self._enemies,
                       "walls": self._walls,
                       "powerups": self._powerups,
                       "bonus": self._bonus
                       }

    @property
    def state(self):
        return json.dumps(self._state)
