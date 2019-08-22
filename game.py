import math
import os
import asyncio
import json
import logging
from enum import Enum

from map import Map, Tiles
from characters import Bomberman, Character

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

LIVES = 3
INITIAL_SCORE = 0
TIMEOUT = 3000 
MAX_HIGHSCORES = 10
GAME_SPEED = 10 
MIN_BOMB_RADIUS = 3

class Powerups(Enum):
    Bombs = 1,
    Flames = 2,
    Speed = 3,
    Wallpass = 4,
    Detonator = 5,
    Bombpass = 6,
    Flamepass = 7,
    Mystery = 8  

class Bomb:
    def __init__(self, pos, radius, detonator=False):
        self._pos = pos
        self._timeout = radius+1
        self._radius = radius

    @property
    def pos(self):
        return self._pos

    @property
    def timeout(self):
        return self._timeout

    def update(self):
        self._timeout-=1/2

    def exploded(self):
        return not self._timeout > 0

    def in_range(self, character):
        px, py = self._pos
        if isinstance(character, Character):
            gx, gy = character.pos
        else:
            gx, gy = character

        return (px == gx or py == gy) and\
            (abs(px - gx) + abs(py - gy)) < self._radius #we share a line/column and we are in distance d
    
    def __repr__(self):
        return self._pos


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
        self._bomberman = Bomberman(self.map.bomberman_spawn, self._initial_lives)
        self._bombs = []
        self._walls = self.map.walls
        self._powerups = []
        self._bonus = []
        self._exit = []
        self._lastkeypress = "" 
        self._score = INITIAL_SCORE 
        self._bomb_radius = 3

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
    
        with open(f"{self.map._level}.score", 'w') as outfile:
            json.dump(self._highscores, outfile)

    def keypress(self, key):
        self._lastkeypress = key

    def update_bomberman(self):
        try:
            if self._lastkeypress.isupper():
                #Parse action
                if self._lastkeypress == 'B' and len(self._bombs) == 0: #TODO powerups for >1 bomb
                    self._bombs.append(Bomb(self._bomberman.pos, MIN_BOMB_RADIUS)) # must be dependent of powerup
            else:
                #Update position
                new_pos = self.map.calc_pos(self._bomberman.pos, self._lastkeypress) #don't bump into stones/walls
                if new_pos not in [b.pos for b in self._bombs]: #don't pass over bombs
                    self._bomberman.pos = new_pos
                for pos, _type in self._powerups:
                    if new_pos == pos:
                        self._bomberman.powerup(_type)
                        self._powerups.remove((pos, _type))

        except AssertionError:
            logger.error("Invalid key <%s> pressed", self._lastkeypress)
        finally:
            self._lastkeypress = "" #remove inertia

        if len(self._enemies) == 0 and self.map.get_tile(self._bomberman) == Tiles.EXIT:
            logger.info("Level completed")
            self.stop()

    def kill_bomberman(self):
        logger.info("bomberman has died on step: {}".format(self._step))
        self._bomberman.kill()
        print(self._bomberman.lives)
        if self._bomberman.lives > 0:
            logger.debug("RESPAWN")
            self._bomberman.respawn()
            #TODO respawn enemies avoiding enemies being at the spawn position of bomberman
        else:
            self.stop()

    def collision(self):
        for e in self._enemies:
            if e == self._bomberman.pos:
                self.kill_bomberman()

    def explode_bomb(self):
        for bomb in self._bombs[:]:
            bomb.update()
            if bomb.exploded():
                logger.debug("BOOM")
                if bomb.in_range(self._bomberman):
                    self.kill_bomberman()

                #TODO clear walls and enemies and show stuff beneath walls
                for wall in self.map.walls:
                    if bomb.in_range(wall):
                        self._walls.remove(wall)
                        if self.map.exit_door == wall:
                            self._exit = wall
                        if self.map.powerup == wall:
                            self._powerups.append((wall, Powerups.Flames))

                self._bombs.remove(bomb)
                print(self._bomberman.pos)

    async def next_frame(self):
        await asyncio.sleep(1./GAME_SPEED)

        if not self._running:
            logger.info("Waiting for player 1")
            return

        self._step += 1
        if self._step == self._timeout:
            self.stop()

        if self._step % 100 == 0:
            logger.debug("[{}] SCORE {} - LIVES {}".format(self._step, self._score, self._bomberman.lives))

        self.explode_bomb()  
        self.update_bomberman()

#   TODO: move enemies
#         for enemy in self._enemies:
#            enemy.update(self._state, self._enemies)

        self.collision()
        self._state = {"step": self._step,
                       "player": self._player_name,
                       "score": self._score,
                       "lives": self._bomberman.lives,
                       "bomberman": self._bomberman.pos,
                       "bombs": [(b.pos, b.timeout) for b in self._bombs],
                       "enemies": self._enemies,
                       "walls": self._walls,
                       "powerups": self._powerups, # [(pos, name)]
                       "bonus": self._bonus,
                       "exit": self._exit,
                       }

    @property
    def state(self):
        print(self._state)
        return json.dumps(self._state)
