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
