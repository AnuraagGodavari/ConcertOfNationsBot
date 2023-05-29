from common import *
from logger import *

import pprint
from random import *

from GameUtils import filehandling, mapping

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.gameobjects import *

import ConcertOfNationsEngine.territories as territories
import ConcertOfNationsEngine.buildings as buildings
import ConcertOfNationsEngine.populations as populations


def generateTestWorld(gamerule, length, height, space):
    logInfo("Generating 'Test World' Worldmap...")

    world = mapping.World("Test World")

    [
        world.addNewTerritory(
            ''.join([chr(randint(97, 122)) for i in range(5)]), 
            (x, y), 
            details = {"Terrain": "Plains"},
            resources = {resource: 1 for resource in gamerule["Resources"]}
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

    conf = filehandling.easyLoad("debugConf", pwdir)

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

    logInfo("Generated and saved game", filehandling.saveObject(savegame))

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
    
    logInfo(f"Testing getting {targetNation.name}'s total resource income per turn:", details = targetNation.get_TurnRevenue(savegame)) 

def testNewTurn(savegame, numMonths):

    logInfo(f"Advancing the turn for savegame {savegame.name} by {numMonths} months")

    savegame.advanceTurn(numMonths)

    logInfo(f"Turn has been advanced!")

def testBuyBuilding(targetNation, buildingName, territoryName, savegame):

    logInfo(f"Testing buying building {buildingName} for {targetNation.name} territory {territoryName}")

    if not (targetNation.canBuyBuilding(savegame, buildingName, buildings.get_blueprint(buildingName, savegame), territoryName)):
        logInfo(f"Could not build {buildingName} for {targetNation.name} in {territoryName}")

    targetNation.addBuilding(buildingName, territoryName, savegame)

def testAddPopulation(gamerule, targetNation, territoryName, size, occupation, identifiers, growth = 0):
    
    if not(populations.validate_population(gamerule, size, occupation, identifiers, growth)):
        return

    population = populations.Population(size, growth, occupation, identifiers)

    territories.add_population(targetNation, territoryName, population)

def testRecruitManpower(targetNation, territoryName, recruitment_size):
    
    if (territories.get_totalpopulation(targetNation, territoryName) <= 0):
        raise InputError(f"{territoryName} is not populated")

    logInfo(f"Recruiting {recruitment_size} manpower from {territoryName}", details = filehandling.saveObject(targetNation.get_territory(territoryName)))

    territories.recruit_manpower(targetNation, territoryName, recruitment_size)

    logInfo(f"Recruited {recruitment_size} manpower from {territoryName}", details = filehandling.saveObject(targetNation.get_territory(territoryName)))

def testDisbandManpower(targetNation, territoryName, disband_size):

    logInfo(f"Disbanding {disband_size} manpower from {territoryName}", details = filehandling.saveObject(targetNation.get_territory(territoryName)))

    territories.disband_manpower(targetNation, territoryName, disband_size)

    logInfo(f"Disbanded {disband_size} manpower from {territoryName}", details = filehandling.saveObject(targetNation.get_territory(territoryName)))





