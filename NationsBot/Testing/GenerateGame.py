from common import *
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
        for y in range(0, length, space) for x in range(0, height, space) 
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

def generateGame(world):

    conf = FileHandling.easyLoad("debugConf", pwdir)

    logInfo("Beginning game generation!")

    savegame = Savegame(
        "TestGame",
        conf["savegame"]["serverID"],
        {"m": 1, "y": 1},
        1
    )
    
    try:
        setupNew_saveGame(
            savegame, 
            world.name, 
            "Test Gamerule"
            )
    except Exception as e:
        logInfo("Savegame already in database, not logging as error")
    savegame.add_Nation(Nation(
        "Nation01",
        conf["Nation01"]["roleid"], 
        (randint(0, 255), randint(0, 255), randint(0, 255)),
        territories = ["Test (0,0)", "Test (20,0)", "Test (0,20)", "Test (20,20)"]
        ))

    try:
        add_Nation(
            savegame, 
            savegame.nations["Nation01"], 
            conf["Nation01"]["playerid"]
            )
    except Exception as e:
        logError(e, {"Message": "Nation 1 already in database"})
        return

    savegame.add_Nation(Nation(
        "Nation02",
        conf["Nation02"]["roleid"], 
        (randint(0, 255), randint(0, 255), randint(0, 255)),
        territories = ['Test (0,40)', 'Test (0,60)', 'Test (0,80)', 'Test (20,40)', 'Test (20,60)', 'Test (20,80)']
        ))

    try:
        add_Nation(
            savegame, 
            savegame.nations["Nation02"],
            conf["Nation02"]["playerid"]
            )
    except Exception as e:
        logError(e, {"Message": "Nation 2 already in database"})
        return

    load_gamerule("Test Gamerule")
    
    save_saveGame(savegame)
    savegame = load_saveGame("TestGame")

    logInfo("Generated and saved game", FileHandling.saveObject(savegame))

    savegame.world_toImage(mapScale = (100, 100))

    logInfo("Generated image of test world map")

    return savegame

def testTerritoryTransfer(savegame, territoryName, targetNation):

    logInfo(f"Testing transfer of territory {territoryName}")

    prevOwner = savegame.find_terrOwner(territoryName)

    if (prevOwner == targetNation):
        logInfo(f"Territory {territoryName} already owned by {prevOwner}")
        return

    terrInfo = savegame.nations[prevOwner].cedeTerritory(territoryName)

    savegame.nations[targetNation].annexTerritory(terrInfo)


def testSuite():
    
    savegame = generateGame(
        generateTestWorld(100, 100, 20)
    )

    testTerritoryTransfer(savegame, "Test (20,20)", "Nation02")

