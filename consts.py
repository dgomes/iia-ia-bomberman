from enum import IntEnum

class Powerups(IntEnum):
    Bombs = 1,
    Flames = 2,
    Speed = 3,
    Wallpass = 4,
    Detonator = 5,
    Bombpass = 6,
    Flamepass = 7,
    Mystery = 8  

class Speed(IntEnum):
    SLOWEST = 1,
    SLOW = 2,
    NORMAL = 3,
    FAST = 4

class Smart(IntEnum):
    LOW = 1,
    NORMAL = 2,
    HIGH = 3