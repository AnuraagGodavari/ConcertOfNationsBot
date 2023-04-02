from copy import copy

from database import *
from logger import *
import imgur

from GameUtils import Operations as ops

import ConcertOfNationsEngine.GameHandling as gamehandling
from ConcertOfNationsEngine.CustomExceptions import *

import ConcertOfNationsEngine.dateoperations as dates

import ConcertOfNationsEngine.Buildings as buildings

#New turn operations

def territory_togglebuilding(nation, territoryName, buildingName):

    territoryInfo = nation.get_territory(territoryName)

    if (buildingName not in territoryInfo["Buildings"]):
        return

    logInfo(f"Territory {territoryName} toggling building {buildingName} with current status {territoryInfo['Buildings'][buildingName]}")

    # Switch between Active and Inactive if the building is one or the other

    if (territoryInfo["Buildings"][buildingName] == "Active"):
        territoryInfo["Buildings"][buildingName] = "Inactive"

    elif (territoryInfo["Buildings"][buildingName] == "Inactive"):
        territoryInfo["Buildings"][buildingName] = "Active"

    logInfo(f"New building status: {territoryInfo['Buildings'][buildingName]}")

    return territoryInfo['Buildings'][buildingName]

def territory_newturnresources(territoryInfo, savegame):

    buildingsIncome = buildings.get_territories_buildingincome(territoryInfo, savegame)
            
    totalrevenue = ops.combineDicts(buildingsIncome)
    return totalrevenue

def territory_advanceconstruction(territoryInfo, savegame):

    logInfo(f"Advancing construction for buildings in {territoryInfo['Name']}")

    for building, oldstatus in territoryInfo["Savegame"]["Buildings"].items():

        if ("Constructing" not in oldstatus):
            continue

        if (dates.date_grtrThan(savegame.date, dates.date_fromstr(oldstatus.split(':')[-1]))):
            territoryInfo["Savegame"]["Buildings"][building] = "Active"
            logInfo(f"{building} now active from date {oldstatus.split(':')[-1]}")
