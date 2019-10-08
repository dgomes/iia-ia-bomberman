import pytest
from game import *
from mapa import *
from characters import *

#columns x lines
mapa13x13 =  [[Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.WALL,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.PASSAGE,Tiles.STONE], 
            [Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE,Tiles.STONE]] 

def test_game():
    game = Game()
    assert not game._running 
    
    game.start("John Doe")
    assert game._running

    assert game.score == 0 

def test_map():
    game = Game()
    game.start("John Doe")

    game.map = Map(enemies=0, size=(13,13), mapa=mapa13x13, enemies_spawn=[(8,8), (7,8), (8,7)]) 

    print(game.map.map)

    assert game.map.is_stone((0,0))
    assert not game.map.is_blocked((1,1))
    assert game.map.is_blocked((1,2))

    # test directions
    assert game.map.calc_pos((4,4), 'w') == (4,3)
    assert game.map.calc_pos((4,4), 's') == (4,5)
    assert game.map.calc_pos((4,4), 'a') == (3,4)
    assert game.map.calc_pos((4,4), 'd') == (5,4)
   
    # test wall blocked / wallpass
    assert game.map.calc_pos((1,1), 's') == (1,1)
    assert game.map.calc_pos((1,1), 's', wallpass=True) == (1,2)


def test_bomb():
    LEVEL_ENEMIES[-1] = [Balloom, Balloom, Balloom]
    game = Game(level=-1)
    game.start("John Doe")

    # Hammer down a wellknown map with 3 enemies
    game.map = Map(enemies=3, size=(13,13), mapa=mapa13x13, enemies_spawn=[(4,2), (2,4), (10,10)])
    game._enemies = [ t(p) for t, p in zip(LEVEL_ENEMIES[-1], game.map.enemies_spawn) ]

    game._bombs = [Bomb((4,4), game.map, 3)]
    
    #Timeout is 2*(RADIUS + 1)
    game.explode_bomb()
    assert len(game._bombs) == 1

    game._bombs.append(Bomb((4,1), game.map, 3))

    for _ in range(2*3):
        game.explode_bomb()
    assert len(game._bombs) == 2

    for t in [(1,4), (2,4), (3,4), (5,4), (6,4), (7,4), (4,1), (4,2), (4,3), (4,5), (4,6), (4,7)]:
        assert game._bombs[0].in_range(t)

    for f in [(1,1), (1,2), (1,3), (1,5), (1,6), (1,7), (2,1), (3,1), (5,1), (6,1), (7,1), (2,7), (3,7), (5,7), (6,7), (7,7), (7,2), (7,3), (7,5), (7,6), (2,2), (3,2), (2,3), (3,3)]:
        assert not game._bombs[0].in_range(f)

    game._bomberman = Bomberman((1,1), 2)
    assert game._bomberman.lives == 2 
    
    # final tick for older bomb
    game.explode_bomb()
    assert len(game._bombs) == 1 

    game.explode_bomb()
    assert game._bomberman.lives == 1

    for e in game._enemies:
        print(e)

    assert len(game._enemies) == 1

    #destroy enemy in a corner (edge test)
    game._bombs.append(Bomb((10,11), game.map, 3))

    for _ in range(3*3):
        game.explode_bomb()

    assert len(game._enemies) == 0
