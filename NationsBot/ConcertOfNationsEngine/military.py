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