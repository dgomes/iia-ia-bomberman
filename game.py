import asyncio
import json
import logging
import math
import os

import requests

from characters import Balloom, Bomberman, Character, Doll, Minvo, Oneal
from consts import Powerups
from mapa import Map, Tiles

logger = logging.getLogger("Game")
logger.setLevel(logging.DEBUG)

LIVES = 3
INITIAL_SCORE = 0
TIMEOUT = 3000
GAME_SPEED = 10
MIN_BOMB_RADIUS = 3
MAP_SIZE = (51, 31)

LEVEL_ENEMIES = {
    1: [Balloom] * 6,
    2: [Balloom] * 3 + [Oneal] * 3,
    3: [Balloom] * 2 + [Oneal] * 2 + [Doll] * 2,
    4: [Balloom] + [Oneal] + [Doll] * 2 + [Minvo] * 2,
    5: [Oneal] * 4 + [Doll] * 3,
}

LEVEL_POWERUPS = {
    1: Powerups.Flames,
    2: Powerups.Bombs,
    3: Powerups.Detonator,
    4: Powerups.Speed,
    5: Powerups.Bombs,
}


class Bomb:
    def __init__(self, pos, mapa, radius, detonator=False):
        self._pos = pos
        self._timeout = radius + 1  # TODO fine tune
        self._radius = radius
        self._detonator = detonator
        self._map = mapa

    def detonate(self):
        if self._detonator:
            self._timeout = 0

    @property
    def pos(self):
        return self._pos

    @property
    def timeout(self):
        return self._timeout

    @property
    def radius(self):
        return self._radius

    def update(self):
        if not self._detonator:
            self._timeout -= 1 / 2

    def exploded(self):
        return not self._timeout > 0

    def in_range(self, character):
        bx, by = self._pos
        if isinstance(character, Character):
            cx, cy = character.pos
        else:
            cx, cy = character

        if by == cy:
            for r in range(self._radius + 1):
                if self._map.is_stone((bx + r, by)):
                    break  # protected by stone to the right
                if (cx, cy) == (bx + r, by):
                    return True
            for r in range(self._radius + 1):
                if self._map.is_stone((bx - r, by)):
                    break  # protected by stone to the left 
                if (cx, cy) == (bx - r, by):
                    return True
        if bx == cx:
            for r in range(self._radius + 1):
                if self._map.is_stone((bx, by + r)):
                    break  # protected by stone in the bottom
                if (cx, cy) == (bx, by + r):
                    return True
            for r in range(self._radius + 1):
                if self._map.is_stone((bx, by - r)):
                    break  # protected by stone in the top
                if (cx, cy) == (bx, by - r):
                    return True

        return False

    def __repr__(self):
        return self._pos


class Game:
    def __init__(self, level=1, lives=LIVES, timeout=TIMEOUT, size=MAP_SIZE):
        logger.info(f"Game(level={level}, lives={lives})")
        self.initial_level = level
        self._running = False
        self._timeout = timeout
        self._score = 0
        self._state = {}
        self._initial_lives = lives
        self.map = Map(size=size, empty=True)
        self._enemies = []

    def info(self):
        return {
            "size": self.map.size,
            "map": self.map.map,
            "fps": GAME_SPEED,
            "timeout": TIMEOUT,
            "lives": LIVES,
            "score": self.score,
        }

    @property
    def running(self):
        return self._running

    @property
    def score(self):
        return self._score

    def start(self, player_name):
        logger.debug("Reset world")
        self._player_name = player_name
        self._running = True
        self._score = INITIAL_SCORE
        self._bomberman = Bomberman(self.map.bomberman_spawn, self._initial_lives)

        self.next_level(self.initial_level)

    def stop(self):
        logger.info("GAME OVER")
        self._running = False

    def next_level(self, level):
        if level > len(LEVEL_ENEMIES):
            logger.info("You WIN!")
            self.stop()
            return

        logger.info("NEXT LEVEL")
        self.map = Map(level=level, size=self.map.size, enemies=len(LEVEL_ENEMIES[level]))
        self._bomberman.respawn()
        self._step = 0
        self._bombs = []
        self._powerups = []
        self._bonus = []
        self._exit = []
        self._lastkeypress = ""
        self._enemies = [
            t(p) for t, p in zip(LEVEL_ENEMIES[level], self.map.enemies_spawn)
        ]
        logger.debug(self._enemies)

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def keypress(self, key):
        self._lastkeypress = key

    def update_bomberman(self):
        try:
            if self._lastkeypress.isupper():
                # Parse action
                if self._lastkeypress == "A" and len(self._bombs) > 0:
                    self._bombs[0].detonate()  # always detonate the oldest bomb
                elif (
                    self._lastkeypress == "B"
                    and len(self._bombs)
                    < self._bomberman.powers.count(Powerups.Bombs) + 1
                ):
                    self._bombs.append(
                        Bomb(
                            self._bomberman.pos,
                            self.map,
                            MIN_BOMB_RADIUS + self._bomberman.flames(),
                            detonator=Powerups.Detonator in self._bomberman.powers,
                        )
                    )  # must be dependent of powerup
            else:
                # Update position
                new_pos = self.map.calc_pos(
                    self._bomberman.pos, self._lastkeypress
                )  # don't bump into stones/walls
                if new_pos not in [b.pos for b in self._bombs]:  # don't pass over bombs
                    self._bomberman.pos = new_pos
                for pos, _type in self._powerups:  # consume powerups
                    if new_pos == pos:
                        self._bomberman.powerup(_type)
                        self._powerups.remove((pos, _type))

        except AssertionError:
            logger.error(
                "Invalid key <%s> pressed. Valid keys: w,a,s,d A B", self._lastkeypress
            )
        finally:
            self._lastkeypress = ""  # remove inertia

        if len(self._enemies) == 0 and self._bomberman.pos == self._exit:
            logger.info(f"Level {self.map.level} completed")
            #self._score += self._timeout - self._step
            self.next_level(self.map.level + 1)

    def kill_bomberman(self):
        logger.info(f"bomberman has died on step: {self._step}")
        self._bomberman.kill()
        logger.debug(f"bomberman has now {self._bomberman.lives} lives")
        if self._bomberman.lives > 0:
            logger.debug("RESPAWN")
            self._bomberman.respawn()
        else:
            self.stop()

    def collision(self):
        for e in self._enemies:
            if e.pos == self._bomberman.pos:
                self.kill_bomberman()
                e.respawn()

    def explode_bomb(self):
        for bomb in self._bombs[:]:
            bomb.update()
            if bomb.exploded():
                logger.debug("BOOM")
                if bomb.in_range(self._bomberman):
                    self.kill_bomberman()

                for wall in self.map.walls[:]:
                    if bomb.in_range(wall):
                        logger.debug(f"Destroying wall @{wall}")
                        self.map.remove_wall(wall)
                        if self.map.exit_door == wall:
                            self._exit = wall
                        if self.map.powerup == wall:
                            self._powerups.append(
                                (wall, LEVEL_POWERUPS[self.map.level])
                            )

                for enemy in self._enemies[:]:
                    if bomb.in_range(enemy):
                        logger.debug(f"killed enemy @{enemy}")
                        self._score += enemy.points()
                        self._enemies.remove(enemy)

                self._bombs.remove(bomb)

    async def next_frame(self):
        await asyncio.sleep(1.0 / GAME_SPEED)

        if not self._running:
            logger.info("Waiting for player 1")
            return

        self._step += 1
        if self._step == self._timeout:
            self.stop()

        if self._step % 100 == 0:
            logger.debug(
                f"[{self._step}] SCORE {self._score} - LIVES {self._bomberman.lives}"
            )

        self.explode_bomb()
        self.update_bomberman()
        self.collision()

        if (
            self._step % (self._bomberman.powers.count(Powerups.Speed) + 1) == 0
        ):  # increase speed of bomberman by moving enemies less often
            for enemy in self._enemies:
                enemy.move(self.map, self._bomberman, self._bombs)
            self.collision()

        self._state = {
            "level": self.map.level,
            "step": self._step,
            "timeout": self._timeout,
            "player": self._player_name,
            "score": self._score,
            "lives": self._bomberman.lives,
            "bomberman": self._bomberman.pos,
            "bombs": [(b.pos, b.timeout, b.radius) for b in self._bombs],
            "enemies": [{"name": str(e), "id": str(e.id), "pos": e.pos} for e in self._enemies],
            "walls": self.map.walls,
            "powerups": [(p, Powerups(n).name) for p, n in self._powerups],
            "bonus": self._bonus,
            "exit": self._exit,
        }

    @property
    def state(self):
        # logger.debug(self._state)
        return json.dumps(self._state)
