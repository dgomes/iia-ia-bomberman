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
from map import Map, Tiles

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('websockets')
logger.setLevel(logging.WARN)

BOMBERMAN = {'up': (0, 0), 'left': (0, 0), 'down': (0, 0), 'right': (0, 0)}

CHAR_LENGTH = 16
CHAR_SIZE= CHAR_LENGTH, CHAR_LENGTH 
SCALE = None 

COLORS = {'white':(255,255,255), 'red':(255,0,0), 'pink':(255,105,180), 'blue':(135,206,235), 'orange':(255,165,0), 'yellow':(255,255,0)}
BACKGROUND = (0, 0, 0)
RANKS = {1:"1ST", 2:"2ND", 3:"3RD", 4:"4TH", 5:"5TH", 6:"6TH", 7:"7TH", 8:"8TH", 9:"9TH", 10:"10TH"}

async def messages_handler(ws_path, queue):
    async with websockets.connect(ws_path) as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))

        while True:
            r = await websocket.recv()
            queue.put_nowait(r)

class GameOver(BaseException):
    pass

class BomberMan(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.images = kw["images"]
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
        self.direction = "left"
        self.image.blit(*self.sprite_pos())
        self.image = pygame.transform.scale(self.image, scale((1,1)))
        super().__init__()
   
    def sprite_pos(self, new_pos=(0,0)):
        CROP = 16 
        x, y = new_pos 
        
        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        x, y = BOMBERMAN[self.direction]
        return (self.images, (0,0), (x, y, x+CROP, y+CROP))

    def update(self, state):
        if 'bomberman' in state:
            x, y = state['bomberman']
            sx, sy = scale((x, y))
            self.rect = pygame.Rect((sx, sy) + CHAR_SIZE)
            self.image = pygame.Surface(CHAR_SIZE)
            self.image.fill((0,0,230))
            self.image.blit(*self.sprite_pos((sx, sy)))
            self.image = pygame.transform.scale(self.image, scale((1, 1)))

            self.x, self.y = sx, sy

class Enemy(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.index = kw.pop("index", 0)
        self.images = kw["images"]
        self.direction = "left"
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
        self.image.blit(*self.sprite_pos((self.x, self.y)))
        self.image = pygame.transform.scale(self.image, scale((1,1)))
        super().__init__()
   
    def sprite_pos(self, new_pos):
        CROP = 22 
        x, y = new_pos 

        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        x, y = ENEMIES[self.index][self.direction] 

        return (self.images, (2,2), (x, y, x+CROP, y+CROP))

    def update(self, state):
        if 'enemies' in state:
            (x, y), zombie, z_timeout = state['enemies'][self.index]
            sx, sy = scale((x, y))
            self.rect = pygame.Rect((sx, sy) + CHAR_SIZE)
            self.image = pygame.Surface(CHAR_SIZE)
            self.image.fill((0,0,0))
            self.image.blit(*self.sprite_pos((sx, sy), zombie))
            self.image = pygame.transform.scale(self.image, scale((1,1)))

            self.x, self.y = sx, sy


def clear_callback(surf, rect):
    color = 0, 250, 0
    surf.fill(color, rect)

def scale(pos):
    x, y = pos
    return int(x * CHAR_LENGTH / SCALE), int(y * CHAR_LENGTH / SCALE)

def draw_background(mapa, SCREEN):
    for x in range(int(mapa.size[0])):
        for y in range(int(mapa.size[1])):
            if mapa.is_blocked((x,y)):
                draw_wall(SCREEN, x, y)
        
def draw_wall(SCREEN, x, y):
    wx, wy = scale((x, y))
    wall_color = (255,0,0)
    pygame.draw.rect(SCREEN, wall_color,
                       (wx,wy,*scale((1,1))), 0)

def draw_info(SCREEN, text, pos, color=(0,0,0), background=None):
    myfont = pygame.font.Font(None, int(30/SCALE))
    textsurface = myfont.render(text, True, color, background)

    erase = pygame.Surface(textsurface.get_size())
    erase.fill((200,200,200))

    if pos[0] > SCREEN.get_size()[0]:
        pos = SCREEN.get_size()[0] - textsurface.get_size()[0], pos[1]
    if pos[1] > SCREEN.get_size()[1]:
        pos = pos[0], SCREEN.get_size()[1] - textsurface.get_size()[1]

    SCREEN.blit(erase,pos)
    SCREEN.blit(textsurface,pos)

async def main_loop(q):
    main_group = pygame.sprite.OrderedUpdates()
    images = pygame.image.load("data/nes.png")
   
    logging.info("Waiting for map information from server") 
    state = await q.get() #first state message includes map information
    print(state)
    newgame_json = json.loads(state)
    mapa = Map(newgame_json['level'], newgame_json['size'], newgame_json['map'])
    for entry in newgame_json["highscores"]:
        print(entry)
    GAME_SPEED = newgame_json["fps"]
    SCREEN = pygame.display.set_mode(scale(mapa.size))
   
    draw_background(mapa, SCREEN)
    main_group.add(BomberMan(pos=scale(mapa.bomberman_spawn), images=images))
    # for i in range(newgame_json["enemies"]):
    #     main_group.add(Enemy(pos=scale(mapa.ghost_spawn), images=images, index=i))
    
    state = {"score": 0, "player": "player1", "bomberman": (0, 0)}
    newstate = dict()
    SCREEN2 = SCREEN.copy()
    blit = 0
    start_time = time.process_time()
    while True:
        pygame.event.pump()
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            asyncio.get_event_loop().stop() 
 
        main_group.clear(SCREEN, clear_callback)
        
        if "score" in state:
            if blit == 1:
                SCREEN.blit(SCREEN2, scale((0,0)))
                blit = 0
                counter = 0
            text = str(state["score"])
            draw_info(SCREEN, text.zfill(6), (0,0))
            text = str(state["player"]).rjust(32)
            draw_info(SCREEN, text, (4000,0))
        # if "energy" in state:
        #     for x, y in state["energy"]:
        #         draw_energy(SCREEN, x, y)
        # if "boost" in state:
        #     for x, y in state["boost"]:
        #         draw_energy(SCREEN, x, y, True)

        main_group.draw(SCREEN)

        #Highscores Board
        elapsed_time = (time.process_time() - start_time) * 100
        print(state,newstate)
        if elapsed_time >= 200 or state == {}:
            start_time = time.process_time()

            if newstate == state:
                highscores = newgame_json["highscores"]
                if blit == 0:
                    SCREEN.blit(pygame.Surface(scale((20,40))), scale((0,0)))
                    blit = 1
                    state = dict()
                draw_info(SCREEN, "THE 10 BEST PLAYERS", scale((5,2)), COLORS['white'], BACKGROUND)
                draw_info(SCREEN, "RANK", scale((2,4)), COLORS['orange'], BACKGROUND)
                draw_info(SCREEN, "SCORE", scale((6,4)), COLORS['orange'], BACKGROUND)
                draw_info(SCREEN, "NAME", scale((11,4)), COLORS['orange'], BACKGROUND)
                    
                for i, highscore in enumerate(highscores):
                    c = (i % 5) + 1
                    draw_info(SCREEN, RANKS[i+1], scale((2,i+6)), list(COLORS.values())[c], BACKGROUND)
                    draw_info(SCREEN, str(highscore[1]), scale((6,i+6)), list(COLORS.values())[c], BACKGROUND)
                    draw_info(SCREEN, highscore[0], scale((11,i+6)), list(COLORS.values())[c], BACKGROUND)


        newstate = state

        main_group.update(state)
       
        pygame.display.flip()
        
        try:
            state = json.loads(q.get_nowait())
        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(1./GAME_SPEED)
            continue 
        

if __name__ == "__main__":
    SERVER = os.environ.get('SERVER', 'localhost')
    PORT = os.environ.get('PORT', '8000')
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="IP address of the server", default=SERVER)
    parser.add_argument("--scale", help="reduce size of window by x times", type=int, default=1)
    parser.add_argument("--port", help="TCP port", type=int, default=PORT)
    args = parser.parse_args()
    SCALE = args.scale

    LOOP = asyncio.get_event_loop()
    pygame.font.init()
    q = asyncio.Queue()
    
    ws_path = 'ws://{}:{}/viewer'.format(args.server, args.port)

    try:
        LOOP.run_until_complete(asyncio.gather(messages_handler(ws_path, q), main_loop(q)))
    finally:
        LOOP.stop()
        pygame.quit()
