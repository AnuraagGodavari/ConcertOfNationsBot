import pprint

from database import *
from logger import *
import imgur

from GameUtils import Operations as ops

import ConcertOfNationsEngine.GameHandling as gamehandling

def get_blueprint(buildingName, savegame):
    """ Return the information relating to this building in a savegame's gamerule """

    logInfo(f"Getting {buildingName} info from {savegame.name} gamerule")

    gamerule = savegame.getGamerule()

    if not (buildingName in gamerule["Buildings"]):
        raise InputError("Could not find building in gamerule")

    return gamerule["Buildings"][buildingName]

    