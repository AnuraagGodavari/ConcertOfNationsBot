from common import *
from logger import *

import pprint
from random import *
from copy import deepcopy
import re

from GameUtils import filehandling, mapping

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.gameobjects import *

import ConcertOfNationsEngine.territories as territories
import ConcertOfNationsEngine.buildings as buildings
import ConcertOfNationsEngine.populations as populations


valid_statuspatterns = ["Active$", "Moving$", "Battling$", "Constructing:((0?[1-9])|(11)|(12))/-?[\d]*$"]

# Validations

def units_addable(baseUnit, *addedUnits):
    return all((unit.unitType == baseUnit.unitType) and (unit.home == baseUnit.home) for unit in addedUnits)

def forces_addable(baseForce, *addedForces):
    return all(
        (force["Location"] == baseForce["Location"]) 
        and (force["Status"] == baseForce["Status"])
        for force in addedForces
        )

def unit_splittable(baseUnit, *newSizes):

    if (sum(newSizes) > baseUnit.size):
        return False

    return True

def force_splittable(baseForce, *unitsToSplit):

    for unitname in unitsToSplit:
        if unitname not in baseForce["Units"].keys():
            return False
    
    return True

def validate_status(newstatus):
    
    for statuspattern in valid_statuspatterns:

        #Define the valid statuses that cannot be manually defined
        if (newstatus in ("Moving", "Battling")):
            return False

        if (re.search(statuspattern, newstatus, flags=re.ASCII)):
            return True

    return False


# Get Information

def get_allunits(gamerule):
    """ Return the information relating to all units in a savegame's gamerule """

    return gamerule["Units"]

def get_blueprint(unitType, gamerule):
    """ Get the blueprint of a unit from the gamerule """

    logInfo(f"Getting {unitType} info from gamerule")

    allunits = get_allunits(gamerule)

    if not (unitType in allunits):
        raise InputError("Could not find unit in gamerule")

    return allunits[unitType]

def get_forcespeed(force, gamerule):

    return min([get_blueprint(unit.unitType, gamerule)["Speed"] for unit in force["Units"].values()])


# Processes

def new_unitName(military_dict, name_template = "Unit", num = 1, unitnames = None):
    """ 
    Generate a name for a unit, adding the lowest possible number to the unit name_template
    
    Args:
        name_template (str): The base name which the lowest possible number is appended to to create the actual unit name.
        num (int): The number the function is checking to see if it is available
    """

    unitnames = unitnames or [unit for force in military_dict.values() for unit in force["Units"].keys()]

    if (f"{name_template} {num}" not in unitnames):
        return f"{name_template} {num}"

    return new_unitName(military_dict, name_template, num + 1, unitnames)

def new_forceName(existing_military_names, name_template = "Force"):
    """ 
    Generate a name for a force
    """

    num = 1

    while f"{name_template} {num}" in existing_military_names:
        num += 1

    return f"{name_template} {num}"

def newturn(force, savegame, gamerule, numMonths, bureaucracy):
    """ Advance unit construction and return cost of unit maintenance."""

    costs = []
    
    for unit in force["Units"].values():

        blueprint = get_blueprint(unit.unitType, gamerule)

        #advance construction
        unit.advance_construction(savegame, numMonths, bureaucracy, blueprint)

        #get resource costs
        costs.append(unit.get_resources(blueprint, numMonths))

    if ("Constructing" in force["Status"]):
        units_underconstruction = [unit for unit in force["Units"].values() if "Constructing" in unit.status]

        if not (units_underconstruction):
            force["Status"] = "Active"
            logInfo("Force is now active")

    elif ("Moving" in force["Status"]):
        move_force(force, numMonths, gamerule)

    return ops.combineDicts(*costs)

def newforcestatus(nation, forcename, newstatus, savegame, gamerule):

    oldstatus = nation.military[forcename]['Status']

    nation.military[forcename]['Status'] = newstatus

    for unit in nation.military[forcename]["Units"].values(): unit.status =  newstatus

    #Change nation bureaucratic load based on if the force is under construction or not

    if (oldstatus.startswith("Constructing:") and not newstatus.startswith("Constructing:")):
        
        for unit in nation.military[forcename]["Units"].values():

            blueprint = get_blueprint(unit.unitType, gamerule)
            
            if ("Bureaucratic Cost" in blueprint.keys()): 
                for category, val in blueprint["Bureaucratic Cost"].items(): nation.bureaucracy[category] = (round(nation.bureaucracy[category][0] - (val * unit.size), 4), nation.bureaucracy[category][1])

    elif (newstatus.startswith("Constructing:") and not oldstatus.startswith("Constructing:")):
        
        for unit in nation.military[forcename]["Units"].values():

            blueprint = get_blueprint(unit.unitType, gamerule)
        
            if ("Bureaucratic Cost" in blueprint.keys()): 
                for category, val in blueprint["Bureaucratic Cost"].items(): nation.bureaucracy[category] = (round(nation.bureaucracy[category][0] + (val * unit.size), 4), nation.bureaucracy[category][1])

    #If the old status was "Moving", delete the old path.
    if (oldstatus == "Moving" and newstatus != "Moving"):
        nation.military[forcename].pop("Path")

    #If the old status was "Battling", delete the old battle information.
    if (oldstatus == "Battling" and newstatus != "Battling"):
        nation.military[forcename].pop("Battle")

    logInfo(f"New force status: {nation.military[forcename]['Status']}")

    return nation.military[forcename]['Status']


def combine_units(baseUnit, *addedUnits):

    baseUnit.size += sum(unit.size for unit in addedUnits)

def combine_units_inForce(force, baseUnit, *addedUnits):

    combine_units(baseUnit, *addedUnits)

    for unit in addedUnits:
        force["Units"].pop(unit.name)

def combine_forces(baseForce, *addedForces):

    for force in addedForces:
        baseForce["Units"].update(force["Units"])

    return baseForce
    

def split_unit(baseForce, baseUnit, newSize, newName):

    baseUnit.size -= newSize

    newUnit = deepcopy(baseUnit)
    newUnit.size = newSize
    newUnit.name = newName

    return newUnit

def split_unit_inForce(nation, baseForce, baseUnit, *newSizes):
    
    for size in newSizes:

        unitname = new_unitName(nation.military, name_template = f"{baseUnit.name} Division")

        baseForce["Units"][unitname] = split_unit(baseForce, baseUnit, size, unitname)

    if (baseUnit.size == 0):

        baseForce["Units"].pop(baseUnit.name)

    return baseForce

def split_force(nation, baseForce, *unitsToSplit):
    
    new_forcename = new_forceName(nation.military.keys(), f"{nation.name} Force")

    newforce = { k: v for k,v in baseForce.items() if k != "Units" }
    newforce["Units"] = { unitname: baseForce["Units"].pop(unitname) for unitname in unitsToSplit}

    nation.military[new_forcename] = newforce

    return new_forcename


def disband_unit(nation, unit):
    
    hometerr = nation.territories[unit.home]
    hometerr["Manpower"] += unit.size
    
def disband_units_inForce(nation, baseForce, unitsToDisband):

    for unitName in unitsToDisband:
        disband_unit(nation, baseForce["Units"].pop(unitName))

def disband_force(nation, forcename):
    
    force = nation.military.pop(forcename)

    disband_units_inForce(nation, force, tuple(force["Units"].keys()))


def check_intercepting_forces(nation, forcename, gamerule, savegame, numMonths):

    logInfo(f"Checking if {forcename} movement is intercepted by any enemy forces")

    baseforce = nation.military[forcename]

    if not(baseforce["Status"] == "Moving"):
        return
    
    enemy_militaries = savegame.get_enemyForces(nation)

    if not (enemy_militaries):
        return

    turn_moveDist = get_forcespeed(baseforce, gamerule) * numMonths

    for terr in baseforce["Path"]:

        # If the territory won't be reached this turn, we've moved as far as we can
        if terr["This Distance"] > turn_moveDist:
            break

        # Check intercept opportunities against stationary enemies

        for enemy_forcename, enemy_force in enemy_militaries.items():

            if (enemy_force["Location"] != terr["Name"]):
                continue

            enemy_name = savegame.find_forceOwner(enemy_forcename)

            logInfo(f"Enemy forces {forcename} and {enemy_forcename} meet at {terr['Name']} [{terr['ID']}]")
            
            # If the enemy is under construction, destroy them. This force can move past them.
            if (enemy_force["Status"].startswith("Constructing:")):
                savegame.nations[enemy_name].pop_force(enemy_forcename)
                logInfo(f"Under construction force {enemy_forcename} has been destroyed by {forcename}")
            
            else:
                baseforce["Intercept"] = {
                    "Nation": enemy_name,
                    "Force": enemy_forcename,
                    "Territory": terr["Name"],
                    "Distance": terr["This Distance"]
                }
                    
                set_battle(enemy_force, nation.name, forcename)

                return


        # If we've reached here, check intercept opportunities against moving enemies

        intercept_opportunities = {
            enemy_forcename: {
                "Terr": enemyterr,
                "Total Distance": enemy_militaries[enemy_forcename]["Path"][-1]["This Distance"]
            } 
            for enemy_forcename in enemy_militaries.keys() 
            if enemy_militaries[enemy_forcename]["Status"] == "Moving" 
            for enemyterr in enemy_militaries[enemy_forcename]["Path"] 
            if enemyterr["Name"] == terr["Name"]
        }

        for enemy_forcename, intercept in intercept_opportunities.items():

            enemy_name = savegame.find_forceOwner(enemy_forcename)
            enemy_force = savegame.nations[enemy_name].military[enemy_forcename]

            # If the enemy force is intercepted by another force at an earlier distance, we've moved too far
            if ("Intercept" in baseforce.keys()):
                if (baseforce["Intercept"]["Distance"] < terr["This Distance"]):
                    continue

            #Friendly current distance percentage
            fc = terr["This Distance"] / baseforce["Path"][-1]["This Distance"]
            #Friendly next distance percentage
            fn = terr["Next Distance"] / baseforce["Path"][-1]["This Distance"]

            #Friendly current distance percentage
            ec = intercept["Terr"]["This Distance"] / intercept["Total Distance"]
            #Friendly next distance percentage
            en = intercept["Terr"]["Next Distance"] / intercept["Total Distance"]

            #If an intercept has been found
            if (
                (ec <= fc and fc <= en)
                or (fc <= ec and ec <= fn)
                or (ec <= fn and fn <= en)
                or (fc <= en and en <= fn)
                ):

                logInfo(f"Enemy forces {forcename} and {enemy_forcename} meet at {terr['Name']} [{terr['ID']}]")
                
                baseforce["Intercept"] = {
                    "Nation": enemy_name,
                    "Force": enemy_forcename,
                    "Territory": terr["Name"],
                    "Distance": terr["This Distance"]
                }
                
                enemy_force["Intercept"] = {
                    "Nation": nation.name,
                    "Force": forcename,
                    "Territory": terr["Name"],
                    "Distance": intercept["Total Distance"]
                }

                return

            else: continue

def setmovement_force(nation, forcename, worldmap, gamerule, savegame, *targetTerritories):
    """ Plot a path for a force based on its location and a target territory. """
    
    baseforce = nation.military[forcename]

    path = list()
    start = baseforce["Location"]

    for target in targetTerritories:
        path += worldmap.path_to(start, target, min_dist = get_forcespeed(baseforce, gamerule))
        start = target

    if not (path):
        return False

    baseforce["Path"] = path
    baseforce["Status"] = "Moving"

    return path

def move_force(force, numMonths, gamerule):
    """ Move the force to the furthest extent possible for the end of this turn. """
    
    # If this force intercepts another force, move to the territory where they intercept and stop all movement

    force_speed = get_forcespeed(force, gamerule) * numMonths
    movement_total = 0

    while(force_speed - movement_total > force["Path"][0]["Distance"]):

        movement_total += force["Path"][0]["Distance"]
        force["Location"] = force["Path"][0]["Name"]
        force["Path"] = force["Path"][1:]

        if not(force["Path"]):
            force.pop("Path")
            force["Status"] = "Active"
            break

        if ("Intercept" in force.keys() and force["Intercept"]["Territory"] == force["Path"][0]["Name"]):

            force["Location"] = force["Intercept"]["Territory"]
            set_battle(force, force["Intercept"]["Nation"], force["Intercept"]["Force"])
            break

    if (movement_total == 0):

        force["Location"] = force["Path"][0]["Name"]
        force["Path"] = force["Path"][1:]

        if not(force["Path"]):
            force.pop("Path")
            force["Status"] = "Active"

    if ("Path" in force.keys()):
        recalculate_path_distances(force, movement_total)

def recalculate_path_distances(force, subtract_dist):
    """ Change the absolute distances recorded in each path node for this force. """
    
    for terr in force["Path"]:
        terr["This Distance"] = round(terr["This Distance"] - subtract_dist, 2)
        terr["Next Distance"] = round(terr["Next Distance"] - subtract_dist, 2)


# Battle management

def set_battle(force, enemy_nation_name, enemy_force_name):
    """ Designate a force as being in battle """

    force["Battle"] = {
        "Nation": enemy_nation_name,
        "Force": enemy_force_name
    }
    if ("Intercept" in force.keys()):
        force.pop("Intercept")
    force["Status"] = "Battling"


class Unit:
    """
    Represents a division of a military force with a certain size and type.

    Args:
        name (str): The unique name of this unit
        status (str): Describes the state of this unit
        unitType(str): The type of unit this is; the name of this unit's blueprint in the gamerule
        size (int): The number of soldiers in this unit
        home (str): The name of the territory from which this unit was recruited
    """

    def __init__(self, name: str, status:str, unitType: str, size: int, home: str):
        
        self.name = name
        self.status = status
        self.unitType = unitType
        self.size = size
        self.home = home

    def get_resources(self, blueprint, numMonths = 1):
        
        return {k: round(v * numMonths * -1 * self.size, 4) for k, v in blueprint["Maintenance"].items()} 

    def advance_construction(self, savegame, numMonths, bureaucracy, blueprint):
        
        if ("Constructing" not in self.status):
            return

        oldstatus = self.status

        if (dates.date_grtrThan_EqlTo(savegame.date, dates.date_fromstr(self.status.split(':')[-1]))):
            self.status = "Active"

            for category, cost in blueprint["Bureaucratic Cost"].items():
                bureaucracy[category] = (round(bureaucracy[category][0] - (cost * self.size), 4), bureaucracy[category][1])

        logInfo(f"Unit {self.name} now active from date {oldstatus.split(':')[-1]}")

        