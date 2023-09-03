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
import ConcertOfNationsEngine.military as military


def generateTestWorld(gamerule, length, height, space, pos_rand = (0,0)):
    logInfo("Generating 'Test World' Worldmap...")

    world = mapping.World("Test World")

    [
        world.addNewTerritory(
            ''.join([chr(randint(97, 122)) for i in range(5)]), 
            (
                x + random() * (pos_rand[1] - pos_rand[0]) - ((pos_rand[1] - pos_rand[0])/2), 
                y + random() * (pos_rand[1] - pos_rand[0]) - ((pos_rand[1] - pos_rand[0])/2)
            ), 
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
                "maxDist": 23
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

def testPath(world, start, target):

    logInfo(f"Path from {start} to {target} territories in {world.name}", details = world.path_to(start, target))

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

def testBuildUnit(targetNation, territoryName, unitType, size, savegame):
    
    logInfo(f"Building {size} {unitType} in {territoryName} in {targetNation.name} ")

    gamerule = savegame.getGamerule()

    blueprint = military.get_blueprint(unitType, gamerule)

    if not (targetNation.can_build_unit(savegame, territoryName, unitType, blueprint, size)):
        logInfo(f"Could not build {unitType} for {targetNation.name} in {territoryName}")
        return

    new_forcename = targetNation.build_unit(territoryName, unitType, size, blueprint, savegame)

    logInfo(f"{targetNation} Military", details = filehandling.saveObject(targetNation.military))
    logInfo(f"{territoryName} Info", details = filehandling.saveObject(targetNation.territories[territoryName]))

    return new_forcename

def testCombineUnits(force, units):

    if not(military.units_addable(units[0], *units[1:])):
        raise InputError("Could not combine units")
    
    military.combine_units_inForce(force, units[0], *units[1:])

def testCombineUnitsandForces(targetNation, territoryName, numMonths, unitsDict, savegame):
    """
    Args:
        unitsDict (dict): Has the format {unitType: [unitSize]}
    """

    logInfo("Testing building and combining several created units and forces in a territory")

    newForcenames = []

    for unitType, unitSizes in unitsDict.items():
        for unitSize in unitSizes:
            newForcenames.append(testBuildUnit(targetNation, territoryName, unitType, unitSize, savegame))

    testNewTurn(savegame, numMonths = 24)

    logInfo(f"{targetNation.name} Military - Initial", details = filehandling.saveObject(targetNation.military))

    forces = [targetNation.pop_force(forcename) for forcename in newForcenames[1:]]
    baseForce = targetNation.military[newForcenames[0]]

    if not(military.forces_addable(baseForce, *forces)):
        raise InputError("Could not combine forces")

    combined_force = military.combine_forces(baseForce, *forces)
    
    logInfo(f"{targetNation.name} Military - After combining forces", details = filehandling.saveObject(targetNation.military))

    for unitType in unitsDict.keys():
        testCombineUnits(combined_force, [unit for unit in combined_force["Units"].values() if unit.unitType == unitType])

    logInfo(f"{targetNation.name} Military - After combining units", details = filehandling.saveObject(targetNation.military))

    return newForcenames[0]

def testSplitUnit(targetNation, territoryName, numMonths, unitsDict, savegame): 
    """
    Args:
        unitsDict (dict): Has the format {unitType: [unitSize, splitUnitSize_0... splitUnitSize_n]}
    """

    logInfo("Testing building and splitting several created units and forces in a territory")

    baseForce = nation.military(testCombineUnitsandForces(targetNation, territoryName, numMonths, {k: [unitsDict[k][0]] for k in unitsDict.keys()}, savegame))

    logInfo(f"{targetNation.name} Military - Initial", details = filehandling.saveObject(targetNation.military))

    for unit in list(baseForce["Units"].values()):

        newSizes = unitsDict[unit.unitType][1:]

        if not(military.unit_splittable(unit, *newSizes)):
            raise InputError("Could not split units")

        military.split_unit_inForce(targetNation, baseForce, unit, *newSizes)

    logInfo(f"{targetNation.name} Military - After splitting units", details = filehandling.saveObject(targetNation.military))

def testSplitForce(targetNation, territoryName, numMonths, unitsDict, unitsToSplit, savegame):

    baseForce = nation.military(testCombineUnitsandForces(targetNation, territoryName, numMonths, unitsDict, savegame))

    logInfo(f"{targetNation.name} Military - Initial", details = filehandling.saveObject(targetNation.military))

    if not(military.force_splittable(baseForce, *unitsToSplit)):
        raise InputError("Could not split force")

    military.split_force(targetNation, baseForce, *unitsToSplit)

    logInfo(f"{targetNation.name} Military - After splitting force", details = filehandling.saveObject(targetNation.military))

def testDisbandUnits(nation, forcename, unitsToDisband):

    logInfo("Testing disbanding units")

    if not(forcename in nation.military.keys()):
        raise InputError(f"{forcename} does not exist")

    baseForce = nation.military[forcename]
    
    if [unitname for unitname in unitsToDisband if unitname not in baseForce["Units"]]:
        raise InputError("Units do not all exist in this military force")

    logInfo(f"{nation.name} Military - Initial", details = filehandling.saveObject(nation.military))
    logInfo(f"{nation.name} Territories - Initial", details = filehandling.saveObject(nation.territories))

    military.disband_units_inForce(nation, baseForce, unitsToDisband)
    
    if not(baseForce["Units"]):
        nation.military.pop(forcename)

    logInfo(f"{nation.name} Military - After disbanding", details = filehandling.saveObject(nation.military))
    logInfo(f"{nation.name} Territories - After disbanding", details = filehandling.saveObject(nation.territories))

def testDisbandForce(nation, forcename):
    logInfo("Testing disbanding force")

    if not(forcename in nation.military.keys()):
        raise InputError(f"{forcename} does not exist")

    logInfo(f"{nation.name} Military - Initial", details = filehandling.saveObject(nation.military))
    logInfo(f"{nation.name} Territories - Initial", details = filehandling.saveObject(nation.territories))

    military.disband_force(nation, forcename)

    logInfo(f"{nation.name} Military - After disbanding", details = filehandling.saveObject(nation.military))
    logInfo(f"{nation.name} Territories - After disbanding", details = filehandling.saveObject(nation.territories))

def testMoveForce(savegame, nation, forcename, worldmap, turnadvancements, *targetTerritories):
    logInfo("Testing moving force")

    military.setmovement_force(nation, forcename, worldmap, *targetTerritories)   

    for numMonths in turnadvancements:
        savegame.advanceTurn(numMonths)

        logInfo(f"Force {forcename} after {numMonths} months of movement:", details = filehandling.saveObject(nation.military[forcename]))