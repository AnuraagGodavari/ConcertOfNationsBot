from copy import copy
import re

from database import *
from logger import *
import imgur

from GameUtils import operations as ops

import ConcertOfNationsEngine.gamehandling as gamehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

valid_statuspatterns = ["Active$", "Inactive$", "Constructing:((0?[1-9])|(11)|(12))/-?[\d]*$"]


#Validation

def validate_status(newstatus):
    
    for statuspattern in valid_statuspatterns:
        if re.search(statuspattern, newstatus, flags=re.ASCII):
            return True

    return False

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

    return {k: v * -1 for k, v in allbuildings[buildingName]["Maintenance"].items()}

def get_minedresources(buildingName, allbuildings, resourcesLeft = None):
    """
    Get the mineable resources from a territory for a specific building.

    Args:
        allbuildings (dict): Represents gamerule["Buildings"], holds information for all the game's buildings.
    """

    max_mineable =  copy(allbuildings[buildingName]["Mines"])

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

    return allbuildings[buildingName]["Produces"]


#Get information about the building's effects

def get_alleffects(buildingName, savegame):

    blueprint = get_blueprint(buildingName, savegame)

    if not (blueprint): return False

    if not ("Effects" in blueprint.keys()): return False

    return blueprint["Effects"]

def get_effect(buildingName, effect, savegame):

    effects = get_alleffects(buildingName, savegame)

    if not (effects): return False

    if not (effect in effects.keys()): return False

    return effects[effect]



#Calculate net income from buildings

def building_newturn(buildingName, allbuildings, resourcesLeft = None):
    """ Get the total amount of resources consumed and produced by the building """

    if not (buildingName in allbuildings):
        raise InputError(f"Could not find building {buildingName} in gamerule")

    return ops.combineDicts(
        get_maintenance(buildingName, allbuildings),
        get_minedresources(buildingName, allbuildings, resourcesLeft),
        get_producedresources(buildingName, allbuildings)
    )

def get_territories_buildingincome(territoryInfo, savegame):
    """ Get the net income of a territory from all of the buildings in it """

    logInfo(f"Getting net income from all buildings for {territoryInfo['Name']}")

    allbuildings = get_allbuildings(savegame)
    
    resourcesLeft = copy(territoryInfo["World"]["Resources"])

    buildingIncomes = {}

    for buildingName in territoryInfo["Savegame"]["Buildings"].keys():

        if (territoryInfo["Savegame"]["Buildings"][buildingName] != "Active"):
            continue

        buildingIncomes[buildingName] = building_newturn(buildingName, allbuildings, resourcesLeft)

    return ops.combineDicts(*list(buildingIncomes.values()))
