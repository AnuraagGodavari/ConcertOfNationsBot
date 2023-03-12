from common import *
from logger import *

import pprint
from random import *

from GameUtils import FileHandling, Mapping

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.GameObjects import *

def generateTestWorld(gamerule, length, height, space):
    logInfo("Generating 'Test World' Worldmap...")

    world = Mapping.World("Test World")

    [
        world.addNewTerritory(
            ''.join([chr(randint(97, 122)) for i in range(5)]), 
            (x, y), 
            details = {"Terrain": "Plains"},
            resources = {resource: randint(0,5) for resource in gamerule["Resources"]}
            ) 
        for y in range(0, length, space) for x in range(0, height, space) 
    ]

    '''
    for i in range(32):
        x = randrange(0, length, space)
        y = randrange(0, height, space)
        world.addNewTerritory(f"Test_({x},{y})", (x, y), details = {"Terrain": "Plains"}) 
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

    try:
        setupNew_world(world)
    except Exception as e:
        logInfo("World already in database, not logging as error")
        save_world(world)

    logInfo("Generated 'Test World'")
    return world

def generateGame(gamerule, world):

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
    except CustomException as e:
        logError(e)
    except Exception as e:
        logInfo("Savegame already in database, not logging as error")
        
    savegame.add_Nation(Nation(
        "Nation01",
        conf["Nation01"]["roleid"], 
        (randint(0, 255), randint(0, 255), randint(0, 255)),
        territories = {
            world.territories[0].name: 
            {

            }, 
            world.territories[1].name:
            {
                
            },  
            world.territories[5].name:
            {
                
            },  
            world.territories[6].name:
            {
                
            } 
            }
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
        territories = {
            world.territories[2].name:
            {
                
            },  
            world.territories[3].name:
            {
                
            }, 
            world.territories[4].name:
            {
                
            }, 
            world.territories[7].name:
            {
                
            }, 
            world.territories[8].name:
            {
                
            }, 
            world.territories[9].name:
            {
                
            }
            }
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
    
    save_saveGame(savegame)
    savegame = load_saveGame("TestGame")

    logInfo("Generated and saved game", FileHandling.saveObject(savegame))

    #savegame.world_toImage(mapScale = (100, 100))
    #logInfo(dbget_worldMap(world, savegame, savegame.turn))

    logInfo("Generated image of test world map")

    return savegame

def testTerritoryTransfer(savegame, territoryName, targetNation):

    logInfo(f"Testing transfer of territory {territoryName}")

    if not(savegame.transfer_territory(territoryName, targetNation)):
        logInfo("Could not transfer territory")
        return

    logInfo(f"Territory transfer successful!")

def testResourceRevenue(savegame, targetNation):
    
    logInfo("Testing getting {targetNation.name}'s total resource income per turn:", details = targetNation.get_TurnRevenue(savegame)) 

def testNewTurn(savegame, numMonths):

    logInfo(f"Advancing the turn for savegame {savegame.name} by {numMonths} months")

    savegame.advanceTurn(numMonths)

    logInfo(f"Turn has been advanced!")

def testBuyBuilding(targetNation, buildingName, territoryName, savegame):

    logInfo(f"Testing buying building {buildingName} for {targetNation.name} territory {territoryName}")

    targetNation.addBuilding(buildingName, territoryName, savegame)

def testSuite():

    gamerule = load_gamerule("Test Gamerule")
    
    testWorld = generateTestWorld(gamerule, 100, 100, 20)

    savegame = generateGame(gamerule, testWorld)

    testNewTurn(savegame, numMonths = 12)

    testResourceRevenue(savegame, savegame.nations["Nation01"])
    testResourceRevenue(savegame, savegame.nations["Nation02"])

    testTerritoryTransfer(savegame, testWorld.territories[-1].name, savegame.nations["Nation02"])

    savegame.nations["Nation01"].resources["Money"] = 100

    testBuyBuilding(savegame.nations["Nation01"], "TestBarracks", next(iter(savegame.nations["Nation01"].territories.keys())), savegame)

