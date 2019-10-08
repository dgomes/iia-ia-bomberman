from consts import Powerups, Speed, Smart
from enum import IntEnum
import random
import uuid

DIR = "wasd"
DEFAULT_LIVES = 3


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
        if smart in [Smart.NORMAL, Smart.HIGH]:
            self.lastdir = None
        else:
            self.lastdir = 0
        self.wander = 0

        super().__init__(*pos)

    def __str__(self):
        return f"{self._name}"

    def points(self):
        return self._points

    def move(self, mapa, bomberman, bombs):
        if not self.ready():
            return

        if self._smart == Smart.LOW:
            new_pos = mapa.calc_pos(
                self.pos, self.dir[self.lastdir]
            )  # don't bump into stones/walls
            if new_pos == self.pos:
                self.lastdir = (self.lastdir + 1) % len(self.dir)

        elif self._smart == Smart.NORMAL:
            b_x, b_y = bomberman.pos
            o_x, o_y = self.pos

            if self.lastdir:
                direction = self.lastdir
            else:
                direction = vector2dir(b_x - o_x, b_y - o_y)

            new_pos = mapa.calc_pos(self.pos, self.dir[direction])  # chase bomberman
            if new_pos == self.pos:
                self.lastdir = (direction + random.choice([-1, 1])) % len(self.dir)
                self.wander = 3
            else:
                if self.wander > 0:
                    self.wander -= 1
                else:
                    self.lastdir = None

        elif self._smart == Smart.HIGH:
            # TODO
            pass

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
