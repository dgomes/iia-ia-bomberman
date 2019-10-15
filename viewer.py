import os
import asyncio
import pygame
import random
from functools import partial
import json
import asyncio
import websockets
import logging
import argparse
import time
from mapa import Map, Tiles

logging.basicConfig(level=logging.DEBUG)
logger_websockets = logging.getLogger("websockets")
logger_websockets.setLevel(logging.WARN)

logger = logging.getLogger("Map")
logger.setLevel(logging.DEBUG)

BOMBERMAN = {
    "up": (3 * 16, 1 * 16),
    "left": (0, 0),
    "down": (3 * 16, 0),
    "right": (0, 1 * 16),
}
BALLOOM = {
    "up": (0, 15 * 16),
    "left": (16, 15 * 16),
    "down": (2 * 16, 15 * 16),
    "right": (3 * 16, 15 * 16),
}
ONEAL = {
    "up": (0, 16 * 16),
    "left": (16, 16 * 16),
    "down": (2 * 16, 16 * 16),
    "right": (3 * 16, 16 * 16),
}
DOLL = {
    "up": (0, 17 * 16),
    "left": (16, 17 * 16),
    "down": (2 * 16, 17 * 16),
    "right": (3 * 16, 17 * 16),
}
MINVO = {
    "up": (0, 18 * 16),
    "left": (16, 18 * 16),
    "down": (2 * 16, 18 * 16),
    "right": (3 * 16, 18 * 16),
}
KONDORIA = {
    "up": (0, 19 * 16),
    "left": (16, 19 * 16),
    "down": (2 * 16, 19 * 16),
    "right": (3 * 16, 19 * 16),
}
OVAPI = {
    "up": (0, 20 * 16),
    "left": (16, 20 * 16),
    "down": (2 * 16, 20 * 16),
    "right": (3 * 16, 20 * 16),
}
PASS = {
    "up": (0, 21 * 16),
    "left": (16, 21 * 16),
    "down": (2 * 16, 21 * 16),
    "right": (3 * 16, 21 * 16),
}
ENEMIES = {"Balloom": BALLOOM, "Oneal": ONEAL, "Doll": DOLL, "Minvo": MINVO, "Kondoria": KONDORIA, "Ovapi": OVAPI, "Pass": PASS}
POWERUPS = {"Bombs": (0, 14 * 16), "Flames": (1 * 16, 14 * 16), "Detonator": (4 * 16, 14 * 16)}
STONE = (48, 48)
WALL = (64, 48)
PASSAGE = (0, 64)
EXIT = (11 * 16, 3 * 16)
BOMB = [(32, 48), (16, 48), (0, 48)]
EXPLOSION = {
    "c": (112, 96),
    "l": (96, 96),
    "r": (128, 96),
    "u": (112, 80),
    "d": (112, 112),
    "xl": (80, 96),
    "xr": (144, 96),
    "xu": (112, 64),
    "xd": (112, 128),
}
FALLOUT = {"c": (32, 96)}

CHAR_LENGTH = 16
CHAR_SIZE = CHAR_LENGTH, CHAR_LENGTH
SCALE = 1

COLORS = {
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "pink": (255, 105, 180),
    "blue": (135, 206, 235),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "grey": (120, 120, 120),
}
BACKGROUND = (0, 0, 0)
RANKS = {
    1: "1ST",
    2: "2ND",
    3: "3RD",
    4: "4TH",
    5: "5TH",
    6: "6TH",
    7: "7TH",
    8: "8TH",
    9: "9TH",
    10: "10TH",
}

SPRITES = None


async def messages_handler(ws_path, queue):
    async with websockets.connect(ws_path) as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))

        while True:
            r = await websocket.recv()
            queue.put_nowait(r)


class GameOver(BaseException):
    pass


class Artifact(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = None, None  # postpone to update_sprite()

        x, y = kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0))))
        new_pos = scale((x, y))
        self.image = pygame.Surface(CHAR_SIZE)
        self.rect = pygame.Rect(new_pos + CHAR_SIZE)
        self.update_sprite((x, y))
        super().__init__()

    def update_sprite(self, pos=None):
        if not pos:
            pos = self.x, self.y
        else:
            pos = scale(pos)
        self.rect = pygame.Rect(pos + CHAR_SIZE)
        self.image.fill((0, 0, 230))
        self.image.blit(*self.sprite)
        # self.image = pygame.transform.scale(self.image, scale((1, 1)))
        self.x, self.y = pos

    def update(self, *args):
        self.update_sprite()


class BomberMan(Artifact):
    def __init__(self, *args, **kw):
        self.direction = "left"
        self.sprite = (SPRITES, (0, 0), (*BOMBERMAN[self.direction], *scale((1, 1))))
        super().__init__(*args, **kw)

    def update(self, new_pos):
        x, y = scale(new_pos)

        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        self.sprite = (SPRITES, (0, 0), (*BOMBERMAN[self.direction], *scale((1, 1))))
        self.update_sprite(tuple(new_pos))


class Enemy(Artifact):
    def __init__(self, *args, **kw):
        self.direction = "left"
        self.name = kw.pop("name")
        self.sprite = (
            SPRITES,
            (0, 0),
            (*ENEMIES[self.name][self.direction], *scale((1, 1))),
        )
        super().__init__(*args, **kw)

    def update(self, new_pos):
        x, y = scale(new_pos)

        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        self.sprite = (
            SPRITES,
            (0, 0),
            (*ENEMIES[self.name][self.direction], *scale((1, 1))),
        )
        self.update_sprite(new_pos)


class Bomb(Artifact):
    def __init__(self, *args, **kw):
        self.index = 0
        self.sprite = (SPRITES, (0, 0), (*BOMB[self.index], *scale((1, 1))))
        self.exploded = False
        self.timeout = kw.pop("timeout", -1)
        self.radius = kw.pop("radius", 0)
        super().__init__(*args, **kw)

    def update(self, bombs_state):
        for pos, timeout, radius in bombs_state:
            if scale(pos) == (self.x, self.y):
                # It's me!
                self.timeout = int(timeout)
                self.radius = radius
                self.index = (self.index + 1) % len(BOMB)
                self.sprite = (SPRITES, (0, 0), (*BOMB[self.index], *scale((1, 1))))
                self.update_sprite()
        if self.timeout == 0:
            self.exploded = True
            self.sprite = ()

            self.rect.inflate_ip(
                self.radius * 2 * CHAR_LENGTH, self.radius * 2 * CHAR_LENGTH
            )

            self.image = pygame.Surface(
                (
                    self.radius * 2 * CHAR_LENGTH + CHAR_LENGTH,
                    self.radius * 2 * CHAR_LENGTH + CHAR_LENGTH,
                )
            )
            self.image.blit(
                SPRITES,
                scale((self.radius, self.radius)),
                (*EXPLOSION["c"], *scale((1, 1))),
            )
            for r in range(1, self.radius):
                self.image.blit(
                    SPRITES,
                    scale((self.radius - r, self.radius)),
                    (*EXPLOSION["l"], *scale((1, 1))),
                )
                self.image.blit(
                    SPRITES,
                    scale((self.radius + r, self.radius)),
                    (*EXPLOSION["r"], *scale((1, 1))),
                )
                self.image.blit(
                    SPRITES,
                    scale((self.radius, self.radius - r)),
                    (*EXPLOSION["u"], *scale((1, 1))),
                )
                self.image.blit(
                    SPRITES,
                    scale((self.radius, self.radius + r)),
                    (*EXPLOSION["d"], *scale((1, 1))),
                )
            self.image.blit(
                SPRITES, scale((0, self.radius)), (*EXPLOSION["xl"], *scale((1, 1)))
            )
            self.image.blit(
                SPRITES,
                scale((2 * self.radius, self.radius)),
                (*EXPLOSION["xr"], *scale((1, 1))),
            )
            self.image.blit(
                SPRITES, scale((self.radius, 0)), (*EXPLOSION["xu"], *scale((1, 1)))
            )
            self.image.blit(
                SPRITES,
                scale((self.radius, 2 * self.radius)),
                (*EXPLOSION["xd"], *scale((1, 1))),
            )


class Wall(Artifact):
    def __init__(self, *args, **kw):
        self.sprite = (SPRITES, (0, 0), (*WALL, *scale((1, 1))))
        super().__init__(*args, **kw)


class Exit(Artifact):
    def __init__(self, *args, **kw):
        self.sprite = (SPRITES, (0, 0), (*EXIT, *scale((1, 1))))
        super().__init__(*args, **kw)


class Powerups(Artifact):
    def __init__(self, *args, **kw):
        self.type = kw.pop("name")
        self.sprite = (SPRITES, (0, 0), (*POWERUPS[self.type], *scale((1, 1))))
        super().__init__(*args, **kw)


def clear_callback(surf, rect):
    """beneath everything there is a passage."""
    surf.blit(SPRITES, (rect.x, rect.y), (*PASSAGE, rect.width, rect.height))


def scale(pos):
    x, y = pos
    return int(x * CHAR_LENGTH / SCALE), int(y * CHAR_LENGTH / SCALE)


def draw_background(mapa):
    background = pygame.Surface(scale((int(mapa.size[0]), int(mapa.size[1]))))
    for x in range(int(mapa.size[0])):
        for y in range(int(mapa.size[1])):
            wx, wy = scale((x, y))
            if mapa.map[x][y] == Tiles.STONE:
                background.blit(SPRITES, (wx, wy), (*STONE, *scale((1, 1))))
            else:
                background.blit(SPRITES, (wx, wy), (*PASSAGE, *scale((1, 1))))
    return background


def draw_info(SCREEN, text, pos, color=(0, 0, 0), background=None):
    myfont = pygame.font.Font(None, int(22 / SCALE))
    textsurface = myfont.render(text, True, color, background)

    x, y = pos
    if x > SCREEN.get_width():
        pos = SCREEN.get_width() - textsurface.get_width(), y
    if y > SCREEN.get_height():
        pos = x, SCREEN.get_height() - textsurface.get_height()

    if background:
        SCREEN.blit(background, pos)
    else:
        erase = pygame.Surface(textsurface.get_size())
        erase.fill(COLORS["grey"])
        # SCREEN.blit(erase, pos)

    SCREEN.blit(textsurface, pos)


async def main_loop(q):
    while True:
        await main_game()


async def main_game():
    global SPRITES, SCREEN

    main_group = pygame.sprite.LayeredUpdates()
    bombs_group = pygame.sprite.OrderedUpdates()
    enemies_group = pygame.sprite.OrderedUpdates()
    walls_group = pygame.sprite.OrderedUpdates()

    logging.info("Waiting for map information from server")
    state = await q.get()  # first state message includes map information
    logging.debug("Initial game status: %s", state)
    newgame_json = json.loads(state)

    GAME_SPEED = newgame_json["fps"]
    mapa = Map(size=newgame_json["size"], mapa=newgame_json["map"])
    TIMEOUT = newgame_json["timeout"]
    SCREEN = pygame.display.set_mode(scale(mapa.size))
    SPRITES = pygame.image.load("data/nes.png").convert_alpha()

    BACKGROUND = draw_background(mapa)
    SCREEN.blit(BACKGROUND, (0, 0))
    main_group.add(BomberMan(pos=mapa.bomberman_spawn))

    state = {"score": 0, "player": "player1", "bomberman": (1, 1)}

    while True:
        pygame.event.pump()
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            asyncio.get_event_loop().stop()

        main_group.clear(SCREEN, clear_callback)
        bombs_group.clear(SCREEN, BACKGROUND)
        enemies_group.clear(SCREEN, clear_callback)

        if "score" in state and "player" in state:
            text = str(state["score"])
            draw_info(SCREEN, text.zfill(6), (0, 0))
            text = str(state["player"]).rjust(32)
            draw_info(SCREEN, text, (4000, 0))

        if "bombs" in state:
            for bomb in bombs_group:
                if bomb.exploded:
                    bombs_group.remove(bomb)
            if len(bombs_group.sprites()) < len(state["bombs"]):
                pos, timeout, radius = state["bombs"][-1]
                bombs_group.add(Bomb(pos=pos, timeout=timeout, radius=radius))
            bombs_group.update(state["bombs"])

        if "enemies" in state:
            enemies_group.empty()
            for enemy in state["enemies"]:
                enemies_group.add(Enemy(name=enemy["name"], pos=enemy["pos"]))

        if "walls" in state:
            walls_group.empty()
            for wall in state["walls"]:
                walls_group.add(Wall(pos=wall))

        if "exit" in state and len(state["exit"]):
            if not [p for p in main_group if isinstance(p, Exit)]:
                logger.debug("Add Exit")
                ex = Exit(pos=state["exit"])
                main_group.add(ex)
                main_group.move_to_back(ex)

        if "powerups" in state:
            for pos, name in state["powerups"]:
                if name not in [p.type for p in main_group if isinstance(p, Powerups)]:
                    logger.debug(f"Add {name}")
                    p = Powerups(pos=pos, name=name)
                    main_group.add(p)
                    main_group.move_to_back(p)
            for powerup in main_group:
                if isinstance(powerup, Powerups):
                    name = powerup.type
                    if name not in [p[1] for p in state["powerups"]]:
                        logger.debug(f"Remove {name}")
                        main_group.remove(powerup)

        walls_group.draw(SCREEN)
        main_group.draw(SCREEN)
        enemies_group.draw(SCREEN)
        bombs_group.draw(SCREEN)

        # Highscores Board
        if (
            ("lives" in state and state["lives"] == 0)
            or ("step" in state and state["step"] >= TIMEOUT)
            or (
                "bomberman" in state
                and "exit" in state
                and state["bomberman"] == state["exit"]
                and "enemies" in state
                and state["enemies"] == []
            )
        ):
            highscores = newgame_json["highscores"]

            HIGHSCORES = pygame.Surface(scale((20, 16)))
            HIGHSCORES.fill(COLORS["grey"])

            draw_info(HIGHSCORES, "THE 10 BEST PLAYERS", scale((5, 1)), COLORS["white"])
            draw_info(HIGHSCORES, "RANK", scale((2, 3)), COLORS["orange"])
            draw_info(HIGHSCORES, "SCORE", scale((6, 3)), COLORS["orange"])
            draw_info(HIGHSCORES, "NAME", scale((11, 3)), COLORS["orange"])

            for i, highscore in enumerate(highscores):
                c = (i % 5) + 1
                draw_info(
                    HIGHSCORES,
                    RANKS[i + 1],
                    scale((2, i + 5)),
                    list(COLORS.values())[c],
                )
                draw_info(
                    HIGHSCORES,
                    str(highscore[1]),
                    scale((6, i + 5)),
                    list(COLORS.values())[c],
                )
                draw_info(
                    HIGHSCORES,
                    highscore[0],
                    scale((11, i + 5)),
                    list(COLORS.values())[c],
                )

            SCREEN.blit(
                HIGHSCORES,
                (
                    (SCREEN.get_width() - HIGHSCORES.get_width()) / 2,
                    (SCREEN.get_height() - HIGHSCORES.get_height()) / 2,
                ),
            )

        if "bomberman" in state:
            main_group.update(state["bomberman"])

        pygame.display.flip()

        try:
            state = json.loads(q.get_nowait())

            if (
                "step" in state
                and state["step"] == 1
                or "level" in state
                and state["level"] != mapa.level
            ):

                # New level! lets clean everything up!
                SCREEN.blit(BACKGROUND, (0, 0))

                walls_group.empty()
                main_group.empty()
                enemies_group.empty()
                bombs_group.empty()
                main_group.add(BomberMan(pos=mapa.bomberman_spawn))
                mapa.level = state["level"]

        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(1.0 / GAME_SPEED)
            continue


if __name__ == "__main__":
    SERVER = os.environ.get("SERVER", "localhost")
    PORT = os.environ.get("PORT", "8000")

    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="IP address of the server", default=SERVER)
    parser.add_argument(
        "--scale", help="reduce size of window by x times", type=int, default=1
    )
    parser.add_argument("--port", help="TCP port", type=int, default=PORT)
    args = parser.parse_args()
    SCALE = args.scale

    LOOP = asyncio.get_event_loop()
    pygame.font.init()
    q = asyncio.Queue()

    ws_path = f"ws://{args.server}:{args.port}/viewer"

    try:
        LOOP.run_until_complete(
            asyncio.gather(messages_handler(ws_path, q), main_loop(q))
        )
    finally:
        LOOP.stop()
