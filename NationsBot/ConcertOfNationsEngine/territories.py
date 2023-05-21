from copy import copy

from database import *
from logger import *
import imgur

from GameUtils import operations as ops
from GameUtils import filehandling

import ConcertOfNationsEngine.gamehandling as gamehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

import ConcertOfNationsEngine.dateoperations as dates

import ConcertOfNationsEngine.buildings as buildings


#Building operations

def hasbuilding(nation, territoryName, buildingName):

    territoryInfo = nation.get_territory(territoryName)

    return bool(buildingName in territoryInfo["Buildings"])

def newbuildingstatus(nation, territoryName, buildingName, newstatus, savegame):

    if (not hasbuilding(nation, territoryName, buildingName)):
        return False

    territoryInfo = nation.get_territory(territoryName)

    if (buildingName not in territoryInfo["Buildings"]):
        return False

    logInfo(f"Territory {territoryName} changing building {buildingName} status from {territoryInfo['Buildings'][buildingName]}")

    if buildings.validate_status(newstatus):

        oldstatus = territoryInfo["Buildings"][buildingName]

        territoryInfo["Buildings"][buildingName] = newstatus

        #Change whether or not the building's effects are active

        if (oldstatus != "Active" and newstatus == "Active"): 
            nation.add_buildingeffects(buildings.get_alleffects(buildingName, savegame))

        elif (oldstatus == "Active" and newstatus != "Active"): 
            nation.remove_buildingeffects(buildings.get_alleffects(buildingName, savegame))

        #Change nation bureaucratic load based on if the building is under construction or not

        blueprint = buildings.get_blueprint(buildingName, savegame)

        if (oldstatus.startswith("Constructing:") and not newstatus.startswith("Constructing:")):
            
            if ("Bureaucratic Cost" in blueprint.keys()): 
                for category, val in blueprint["Bureaucratic Cost"].items(): nation.bureaucracy[category] = (nation.bureaucracy[category][0] - val, nation.bureaucracy[category][1])

        elif (newstatus.startswith("Constructing:") and not oldstatus.startswith("Constructing:")):
            
            if ("Bureaucratic Cost" in blueprint.keys()): 
                for category, val in blueprint["Bureaucratic Cost"].items(): nation.bureaucracy[category] = (nation.bureaucracy[category][0] + val, nation.bureaucracy[category][1])

    logInfo(f"New building status: {territoryInfo['Buildings'][buildingName]}")

    return territoryInfo['Buildings'][buildingName]

def togglebuilding(nation, territoryName, buildingName, savegame):

    if (not hasbuilding(nation, territoryName, buildingName)):
        return False

    territoryInfo = nation.get_territory(territoryName)

    logInfo(f"Territory {territoryName} toggling building {buildingName} with current status {territoryInfo['Buildings'][buildingName]}")

    # Switch between Active and Inactive if the building is one or the other

    if (territoryInfo["Buildings"][buildingName] == "Active"):
        territoryInfo["Buildings"][buildingName] = "Inactive"
        nation.remove_buildingeffects(buildings.get_alleffects(buildingName, savegame))

    elif (territoryInfo["Buildings"][buildingName] == "Inactive"):
        territoryInfo["Buildings"][buildingName] = "Active"
        nation.add_buildingeffects(buildings.get_alleffects(buildingName, savegame))

    logInfo(f"New building status: {territoryInfo['Buildings'][buildingName]}")

    return territoryInfo['Buildings'][buildingName]

def destroybuilding(nation, territoryName, buildingName):

    if (not hasbuilding(nation, territoryName, buildingName)):
        return False

    territoryInfo = nation.get_territory(territoryName)

    territoryInfo["Buildings"].pop(buildingName)

    logInfo(f"Territory {territoryName} destroyed building {buildingName}")


#Population management
def add_population(nation, territoryName, population):
    nation.territories[territoryName]["Population"].append(population)

def all_populations(nation, territoryName):
    return nation[territoryName]["population"]

#New turn operations    

def newturnresources(territoryInfo, savegame):

    buildingsIncome = buildings.get_territories_buildingincome(territoryInfo, savegame)
            
    totalrevenue = ops.combineDicts(buildingsIncome)
    return totalrevenue

def advanceconstruction(territoryInfo, savegame, bureaucracy):
    """
    Enable all buildings that have completed construction by current savegame date
    """

    neweffects = []

    logInfo(f"Advancing construction for buildings in {territoryInfo['Name']}")

    for building, oldstatus in territoryInfo["Savegame"]["Buildings"].items():

        if ("Constructing" not in oldstatus):
            continue

        if (dates.date_grtrThan_EqlTo(savegame.date, dates.date_fromstr(oldstatus.split(':')[-1]))):
            territoryInfo["Savegame"]["Buildings"][building] = "Active"

            for category, cost in buildings.get_blueprint(building, savegame)["Bureaucratic Cost"].items():
                bureaucracy[category] = (bureaucracy[category][0] - cost, bureaucracy[category][1])

            logInfo(f"{building} now active from date {oldstatus.split(':')[-1]}")

            neweffects.append(buildings.get_alleffects(building, savegame))

    return ops.combineDicts(*neweffects)