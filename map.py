import os
import logging
import random
from enum import IntEnum

class Tiles(IntEnum):
    PASSAGE = 0
    STONE = 1
    WALL = 2
    POWERUPS = 10
    BONUS = 11
    EXIT = 100


class Map:
    def __init__(self, level=1, size=(10, 10), mapa=None):
        self._level = level
        self._size = size
        self.hor_tiles = size[0]
        self.ver_tiles = size[1]
        self._walls = []
        if not mapa:
            self.map = [[Tiles.PASSAGE] * self.hor_tiles for i in range(self.ver_tiles)]
            for x in range(self.hor_tiles):
                for y in range(self.ver_tiles):
                    if x in [0, self.hor_tiles-1] or y in [0, self.ver_tiles-1]:
                        self.map[x][y] = Tiles.STONE
                    else:
                        if random.randint(1,4) > 3:
                            self.map[x][y] = Tiles.WALL
                            self._walls.append((x, y))
        else:
            self.map = mapa
        self._bomberman_spawn = (1,1) #TODO
        self._enemies_spawn = [(8,8)] #TODO 
    
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

    @property
    def level(self):
        return self._level

    @property
    def size(self):
        return self.hor_tiles, self.ver_tiles 

    @property
    def bomberman_spawn(self):
        return self._bomberman_spawn

    @property
    def enemies_spawn(self):
        return self._enemies_spawn

    def is_blocked(self, pos):
        x, y = pos
        if x not in range(self.hor_tiles) or y not in range(self.ver_tiles):
            return True
        if self.map[x][y] in [Tiles.STONE, Tiles.WALL]:
            return True
        return False

    def calc_pos(self, cur, direction):
        assert direction in "wasd" or direction == ""

        cx, cy = cur
        npos = cur
        if direction == 'w':
            npos = cx, cy-1
        if direction == 'a':
            npos = cx-1, cy
        if direction == 's':
            npos = cx, cy+1
        if direction == 'd':
            npos = cx+1, cy

        #test blocked
        if self.is_blocked(npos):
            return cur
   
        return npos
    
