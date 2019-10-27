import os
import logging
import random
from enum import IntEnum

logger = logging.getLogger("Map")
logger.setLevel(logging.DEBUG)


class Tiles(IntEnum):
    PASSAGE = 0
    STONE = 1
    WALL = 2


VITAL_SPACE = 3


class Map:
    def __init__(self, level=1, enemies=0, size=(VITAL_SPACE+10, VITAL_SPACE+10), mapa=None, enemies_spawn=None, empty=False):

        assert size[0] > VITAL_SPACE+9
        assert size[1] > VITAL_SPACE+9

        self._level = level
        self._size = size
        self.hor_tiles = size[0]
        self.ver_tiles = size[1]
        self._walls = []
        if enemies_spawn:
            self._enemies_spawn = enemies_spawn
        else:
            self._enemies_spawn = []

        if not mapa:
            logger.info("Generating a MAP")
            self.map = [[Tiles.PASSAGE] * self.ver_tiles for i in range(self.hor_tiles)]
            for x in range(self.hor_tiles):
                for y in range(self.ver_tiles):
                    if x in [0, self.hor_tiles - 1] or y in [0, self.ver_tiles - 1]:
                        self.map[x][y] = Tiles.STONE
                    elif x % 2 == 0 and y % 2 == 0:
                        self.map[x][y] = Tiles.STONE
                    elif (
                        x >= VITAL_SPACE and y >= VITAL_SPACE and not empty
                    ):  # give bomberman some room
                        if random.randint(0, 100) > 70 + 25 / level:
                            self.map[x][y] = Tiles.WALL
                            self._walls.append((x, y))

            for _ in range(enemies):
                x, y = 0, 0
                while self.map[x][y] in [
                    Tiles.STONE,
                    Tiles.WALL,
                ]:  # find empty spots to place enemies
                    x, y = (
                        random.randrange(VITAL_SPACE, self.hor_tiles),
                        random.randrange(VITAL_SPACE, self.ver_tiles),
                    )
                self._enemies_spawn.append((x, y))
                logger.debug(f"Spawn enemy at ({x}, {y})")
                # create a vital space for enemies:
                for rx, ry in [(x, y) for x in [-1, 0, 1] for y in [-1, 0, 1]]:
                    if self.map[x + rx][y + ry] in [Tiles.WALL]:
                        self.map[x + rx][y + ry] = Tiles.PASSAGE
                        self._walls.remove((x + rx, y + ry))

            if not empty:
                self.exit_door = random.choice(self._walls)
                self.powerup = random.choice(
                    [w for w in self._walls if w != self.exit_door]
                )  # hide powerups behind walls only

        else:
            logger.info("Loading MAP")
            self.map = mapa
            for x in range(self.hor_tiles):
                for y in range(self.ver_tiles):
                    if self.map[x][y] == Tiles.WALL and (x, y) != (1, 1):
                        self._walls.append((x, y))
        self._bomberman_spawn = (1, 1)  # Always true

    def __getstate__(self):
        return self.map

    def __setstate__(self, state):
        self.map = state

    @property
    def size(self):
        return self._size

    @property
    def walls(self):
        return self._walls

    @walls.setter
    def walls(self, walls):
        self._walls = [ (x, y) for x, y in walls ] 

    def remove_wall(self, wall):
        self._walls.remove(wall)

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, l):
        self._level = l

    @property
    def bomberman_spawn(self):
        return self._bomberman_spawn

    @property
    def enemies_spawn(self):
        return self._enemies_spawn

    def get_tile(self, pos):
        x, y = pos
        return self.map[x][y]

    def is_blocked(self, pos, wallpass=False):
        x, y = pos
        if x not in range(self.hor_tiles) or y not in range(self.ver_tiles):
            return True
        if self.map[x][y] in [Tiles.STONE] or (not wallpass and (x, y) in self._walls):
            return True
        return False

    def is_stone(self, pos):
        x, y = pos
        if x >= self.hor_tiles or y >= self.ver_tiles: #everything outside of map is stone
            return True
        return self.map[x][y] in [Tiles.STONE]

    def calc_pos(self, cur, direction, wallpass=False):
        assert direction in "wasd" or direction == ""

        cx, cy = cur
        npos = cur
        if direction == "w":
            npos = cx, cy - 1
        if direction == "a":
            npos = cx - 1, cy
        if direction == "s":
            npos = cx, cy + 1
        if direction == "d":
            npos = cx + 1, cy

        # test blocked
        if self.is_blocked(npos, wallpass=wallpass):
            return cur

        return npos
