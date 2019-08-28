from consts import Powerups
from enum import IntEnum

class Speed(IntEnum):
    SLOWEST = 1,
    SLOW = 2,
    NORMAL = 3,
    FAST = 4

class Smart(IntEnum):
    LOW = 1,
    NORMAL = 2,
    HIGH = 3

DEFAULT_LIVES = 3

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
        return {"pos": self.pos,
                "lives": self._lives}

    @property 
    def powers(self):
        return self._powers

    @property
    def lives(self):
        return self._lives

    def flames(self):
        return len([p for p in self._powers if p == Powerups.Flames])

    def kill(self):
        self._lives-=1

    def powerup(self, _type):
        self._powers.append(_type)

class Enemy(Character):
    def __init__(self, pos, name, points, speed, smart, wallpass):
        self._name = name
        self._points = points
        self._speed = speed
        self._smart = smart
        self._wallpass = wallpass
        self.dir = 'wasd'
        self.step = 0
        super().__init__(*pos)
    
    def __str__(self):
        return f"{self._name}"
    
    def points(self):
        return self._points

    def move(self, mapa): #TODO implement movements
        raise NotImplementedError

    def ready(self):
        self.step += int(self._speed)
        if self.step == 4:
            self.step = 0
            return False
        return True
    
class Balloom(Enemy):
    def __init__(self, pos):
        super().__init__(pos, self.__class__.__name__,
            100, Speed.SLOW, 1, False)
        self.lastdir = 0
    
    def move(self, mapa):
        if self.ready():
            new_pos = mapa.calc_pos(self.pos, self.dir[self.lastdir]) #don't bump into stones/walls      
            if new_pos == self.pos:
                self.lastdir = (self.lastdir + 1) % len(self.dir)
            self.pos = new_pos

class Oneal(Enemy):
    def __init__(self, pos):
        super().__init__(pos, self.__class__.__name__,
            200, Speed.NORMAL, 2, False)

  
