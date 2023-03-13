import pprint
from copy import copy

from database import *
from logger import *
import imgur

from GameUtils import Operations as ops

import ConcertOfNationsEngine.GameHandling as gamehandling
from ConcertOfNationsEngine.CustomExceptions import *

#Get information from the gamedict

def get_allbuildings(savegame):
    """ Return the information relating to all buildings in a savegame's gamerule """

    logInfo(f"Getting all building blueprints from {savegame.name} gamerule")

    gamerule = savegame.getGamerule()

    return gamerule["Buildings"]

def get_blueprint(buildingName, savegame):
    """ Return the information relating to this building in a savegame's gamerule """

    logInfo(f"Getting {buildingName} info from {savegame.name} gamerule")

    allbuildings = get_allbuildings(savegame)

    if not (buildingName in allbuildings):
        raise InputError("Could not find building in gamerule")

    return allbuildings[buildingName]

def get_maintenance(buildingName, allbuildings):
    """
    Get the maintenance costs for a specific building, with all resources in the negative.

    Args:
        allbuildings (dict): Represents gamerule["Buildings"], holds information for all the game's buildings.
    """

    return {k: v * -1 for k, v in allbuildings[buildingName]["maintenance"].items()}

def get_minedresources(buildingName, allbuildings, resourcesLeft = None):
    """
    Get the mineable resources from a territory for a specific building.

    Args:
        allbuildings (dict): Represents gamerule["Buildings"], holds information for all the game's buildings.
    """

    max_mineable =  copy(allbuildings[buildingName]["mines"])

    if not resourcesLeft:
        return max_mineable

    for resource in max_mineable.keys():
        
        if resource in resourcesLeft:
            max_mineable[resource] = min(max_mineable[resource], resourcesLeft[resource])
            resourcesLeft[resource] = resourcesLeft[resource] - max_mineable[resource]

        else: max_mineable[resource] = 0

    return max_mineable
    

def get_producedresources(buildingName, allbuildings):
    """
    Get the resources produced for a specific building.

    Args:
        allbuildings (dict): Represents gamerule["Buildings"], holds information for all the game's buildings.
    """

    return allbuildings[buildingName]["produces"]


#Calculate net income from buildings

def get_building_netincome(buildingName, territoryInfo, territoryName, allbuildings, resourcesLeft = None):
    """ Get the total amount of resources consumed and produced by the building """

    if not (buildingName in allbuildings):
        raise InputError(f"Could not find building {buildingName} in gamerule")

    return ops.combineDicts(
        get_maintenance(buildingName, allbuildings),
        get_minedresources(buildingName, allbuildings, resourcesLeft),
        get_producedresources(buildingName, allbuildings)
    )

def get_territories_buildingincome(territoryInfo, territoryName, savegame):
    """ Get the net income of a territory from all of the buildings in it """

    logInfo(f"Getting net income from all buildings for {territoryName}")

    allbuildings = get_allbuildings(savegame)
    
    resourcesLeft = copy(territoryInfo["Resources"])

    buildingIncomes = {}

    for buildingName in territoryInfo["Buildings"].keys():
        buildingIncomes[buildingName] = get_building_netincome(buildingName, territoryInfo, territoryName, allbuildings, resourcesLeft)

    return ops.combineDicts(*list(buildingIncomes.values()))