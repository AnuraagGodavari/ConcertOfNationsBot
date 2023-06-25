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

def new_unitName(military_dict, name_template = "Unit", num = 1, unitnames = None):
    """ 
    Generate a name for a unit, adding the lowest possible number to the unit name_template
    
    Args:
        name_template (str): The base name which the lowest possible number is appended to to create the actual unit name.
        num (int): The number the function is checking to see if it is available
    """

    unitnames = unitnames or [unit.name for force in military_dict for unit in unitnames]

    if (f"{name_template} {num}" not in unitnames):
        return f"{name_template} {num}"

    return new_unitName(military_dict, name_template, num + 1, unitnames)

def new_forceName(military_dict, name_template = "Force"):
    """ 
    Generate a name for a force
    """

    num = 1

    while f"{name_template} {num}" in military_dict.keys():
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

    return ops.combineDicts(*costs)


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
        
        return {k: v * numMonths * -1 for k, v in blueprint["Maintenance"].items()} 

    def advance_construction(self, savegame, numMonths, bureaucracy, blueprint):
        
        if ("Constructing" not in self.status):
            return

        oldstatus = self.status

        if (dates.date_grtrThan_EqlTo(savegame.date, dates.date_fromstr(self.status.split(':')[-1]))):
            self.status = "Active"

            for category, cost in blueprint["Bureaucratic Cost"].items():
                bureaucracy[category] = (bureaucracy[category][0] - cost, bureaucracy[category][1])

        logInfo(f"Unit {self.name} now active from date {oldstatus.split(':')[-1]}")

        