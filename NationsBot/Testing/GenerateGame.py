from logger import *
from Utils import FileHandling

import pprint

from ConcertOfNationsEngine.GameObjects import *

def generateGame():
	logInfo("Beginning game generation!")
	
	savegame = Savegame(
		"TestGame",
		{"m": 1, "y": 1}
	)
	
	savegame.nations = {
		"Nation01": Nation("Nation01")
	}
	
	logInfo("Generated game", FileHandling.saveObject(savegame))