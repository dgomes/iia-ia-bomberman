from consts import Powerups, Speed, Smart
from enum import IntEnum
import random
import uuid
import math

DIR = "wasd"
DEFAULT_LIVES = 3

def distance(p1, p2):
    x1,y1 = p1
    x2,y2 = p2
    return math.hypot(x1-x2, y1-y2)

def vector2dir(vx, vy):
    m = max(abs(vx), abs(vy))
    if m == abs(vx):
        if vx < 0:
            d = 1  # a
        else:
            d = 3  # d
    else:
        if vy > 0:
            d = 2  # s
        else:
            d = 0  # w
    return d


class Character:
    def __init__(self, x=1, y=1):
        self._pos = x, y
        self._spawn_pos = self._pos

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value

    @property
    def x(self):
        return self._pos[0]

    @property
    def y(self):
        return self._pos[1]

    def respawn(self):
        self.pos = self._spawn_pos


class Bomberman(Character):
    def __init__(self, pos, lives=DEFAULT_LIVES):
        super().__init__(x=pos[0], y=pos[1])
        self._lives = lives
        self._powers = []

    def to_dict(self):
        return {"pos": self.pos, "lives": self._lives}

    @property
    def powers(self):
        return self._powers

    @property
    def lives(self):
        return self._lives

    @property
    def wallpass(self):
        return Powerups.Wallpass in self._powers

    @property
    def flamepass(self):
        return Powerups.Flamepass in self._powers
    
    @property
    def bombpass(self):
        return Powerups.Bombpass in self._powers

    def flames(self):
        return len([p for p in self._powers if p == Powerups.Flames])

    def kill(self):
        self._lives -= 1

    def powerup(self, _type):
        self._powers.append(_type)


class Enemy(Character):
    def __init__(self, pos, name, points, speed, smart, wallpass):
        self._name = name
        self.id = uuid.uuid4()
        self._points = points
        self._speed = speed
        self._smart = smart
        self._wallpass = wallpass
        self.dir = DIR
        self.step = 0
        self.lastdir = 0
        self.lastpos = None
        self.wander = 0

        super().__init__(*pos)

    def __str__(self):
        return f"{self._name}"

    def points(self):
        return self._points

    def move(self, mapa, bomberman, bombs, enemies):
        if not self.ready():
            return

        if self._smart == Smart.LOW:
            new_pos = mapa.calc_pos(
                self.pos, self.dir[self.lastdir], self._wallpass
            )  # don't bump into stones/walls
            if new_pos == self.pos:
                self.lastdir = (self.lastdir + 1) % len(self.dir)

        elif self._smart == Smart.NORMAL:
            enemies_pos = [e.pos for e in enemies if e.id != self.id]
            open_pos = [pos for pos in [mapa.calc_pos(self.pos, d, self._wallpass) for d in DIR] if pos not in [self.lastpos]+enemies_pos]
            if open_pos == []:
                new_pos = self.lastpos
            else:
                next_pos = sorted(open_pos, key=lambda pos: distance(bomberman.pos, pos), reverse=True)
                new_pos = next_pos[0]

        elif self._smart == Smart.HIGH:
            enemies_pos = [e.pos for e in enemies if e.id != self.id]
            open_pos = [pos for pos in [mapa.calc_pos(self.pos, d, self._wallpass) for d in DIR] if pos not in [self.lastpos]+enemies_pos]
            if open_pos == []:
                new_pos = self.lastpos
            else:
                if len(bombs):
                    next_pos = sorted(open_pos, key=lambda pos: distance(bombs[0].pos, pos), reverse=True)
                else:
                    next_pos = sorted(open_pos, key=lambda pos: distance(bomberman.pos, pos), reverse=True)
                new_pos = next_pos[0]

        self.lastpos = self.pos
        self.pos = new_pos

    def ready(self):
        self.step += int(self._speed)
        if self.step >= int(Speed.FAST):
            self.step = 0
            return True
        return False


class Balloom(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos, self.__class__.__name__, 100, Speed.SLOW, Smart.LOW, False
        )


class Oneal(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos, self.__class__.__name__, 200, Speed.SLOWEST, Smart.NORMAL, False
        )


class Doll(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos, self.__class__.__name__, 400, Speed.NORMAL, Smart.LOW, False
        )


class Minvo(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos, self.__class__.__name__, 800, Speed.FAST, Smart.NORMAL, False
        )

class Kondoria(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos, self.__class__.__name__, 1000, Speed.SLOWEST, Smart.HIGH, True 
        )

class Ovapi(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos, self.__class__.__name__, 2000, Speed.SLOW, Smart.NORMAL, True 
        )

class Pass(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos, self.__class__.__name__, 4000, Speed.FAST, Smart.HIGH, False
        )
