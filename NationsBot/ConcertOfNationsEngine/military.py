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

def new_unitName(military_dict, name_template = "Unit", num = 1):
    """ 
    Generate a name for a unit, adding the lowest possible number to the unit name_template
    
    Args:
        name_template (str): The base name which the lowest possible number is appended to to create the actual unit name.
        num (int): The number the function is checking to see if it is available
    """

    if (f"{name_template} {num}" not in military_dict.keys()):
        return f"{name_template} {num}"

    return new_unitName(military_dict, name_template, num + 1)


    

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