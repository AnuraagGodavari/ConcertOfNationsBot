from logger import *

import pprint
from random import *

from Utils import FileHandling, Mapping

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.GameObjects import *

def generateTestWorld(length, height, space):
    logInfo("Generating 'Test World' Worldmap...")

    world = Mapping.World("Test World")

    [
        world.addNewTerritory(f"Test ({x},{y})", (x, y), details = {"Terrain": "Plains"}) 
        for x in range(0, length, space) for y in range(0, height, space) 
    ]

    '''
    for i in range(32):
        x = randrange(0, length, space)
        y = randrange(0, height, space)
        world.addNewTerritory(f"Test ({x},{y})", (x, y), details = {"Terrain": "Plains"}) 
    '''

    world.calculateAllNeighbors(
        [
            {
                "t0": {"Terrain": "Plains"},
                "t1": {"Terrain": "Plains"},
                "maxDist": 20
            }
        ]
    )

    with open(f"{worldsDir}/Test World.json", 'w') as f:
        json.dump(FileHandling.saveObject(world), f, indent = 4)

    logInfo("Generated 'Test World'")
    return world

def generateGame():
    logInfo("Beginning game generation!")
    
    testWorld = generateTestWorld(100, 100, 20)

    savegame = Savegame(
        "TestGame",
        {"m": 1, "y": 1},
        1
    )

    savegame.add_Nation(Nation(
        "Nation01",
        (randint(0, 255), randint(0, 255), randint(0, 255)),
        territories = ["Test (0,0)", "Test (20,0)", "Test (0,20)", "Test (20,20)"]
        ))

    load_gamerule("Test Gamerule")
    
    #setupNew_saveGame(0, savegame, testWorld.name, "Test Gamerule")
    
    save_saveGame(savegame)
    savegame = load_saveGame("TestGame")

    logInfo("Generated and saved game", FileHandling.saveObject(savegame))

    savegame.world_toImage(testWorld)

    logInfo("Generated image of test world map")

    exit()