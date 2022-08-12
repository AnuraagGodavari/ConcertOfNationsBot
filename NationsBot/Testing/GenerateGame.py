from logger import *

import pprint
from random import randrange

from Utils import FileHandling, Mapping

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.GameObjects import *

def generateTestWorld(length, height, space):
    logInfo("Generating 'Test World' Worldmap...")

    world = Mapping.World("Test World")

    '''
    [
        world.addNewTerritory(f"Test ({x},{y})", (x, y), details = {"Terrain": "Plains"}) 
        for x in range(0, length, space) for y in range(0, height, space) 
    ]
    '''

    for i in range(32):
        x = randrange(0, length, space)
        y = randrange(0, height, space)
        world.addNewTerritory(f"Test ({x},{y})", (x, y), details = {"Terrain": "Plains"}) 

    world.calculateAllNeighbors(
        [
            {
                "t0": {"Terrain": "Plains"},
                "t1": {"Terrain": "Plains"},
                "maxDist": 40
            }
        ]
    )

    with open(f"{worldsDir}/Test World.json", 'w') as f:
        json.dump(FileHandling.saveObject(world), f, indent = 4)

    world.toImage()

    logInfo("Generated 'Test World'")
    return world

def generateGame():
    logInfo("Beginning game generation!")
    
    testWorld = generateTestWorld(150, 150, 7)

    savegame = Savegame(
        "TestGame",
        {"m": 1, "y": 1},
        1,
        nations = {
            "Nation01": Nation("Nation01")
        }
    )

    load_gamerule("Test Gamerule")
    
    #setupNew_saveGame(0, savegame, testWorld.name, "Test Gamerule")
    
    save_saveGame(savegame)
    savegame = load_saveGame("TestGame")

    logInfo("Generated and saved game", FileHandling.saveObject(savegame))

    exit()