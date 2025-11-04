from common import *
from logger import *

from ConcertOfNationsEngine.concertofnations_exceptions import *
import GameUtils.operations as ops

""" A dictionary where keys are player IDs and values are dictionaries, which contain key-value pairs to be used across the application """
playercache = dict()

def keyValueValidation(serverid, playerid, k = None):

    if not (serverid in playercache.keys()):
        return False

    if not (playerid in playercache[serverid].keys()):
        return False

    if ((k) and (k not in playercache[serverid][playerid].keys())):
        return False

    return True

def addKeyValue(serverid, playerid, k, v):

    if not (serverid in playercache.keys()):
        playercache[serverid] = dict()

    if not (playerid in playercache[serverid].keys()):
        playercache[serverid][playerid] = dict()

    playercache[serverid][playerid][k] = v

def getKeyValue(serverid, playerid, k):

    if (keyValueValidation(serverid, playerid, k)):
        return playercache[serverid][playerid][k]

    return False