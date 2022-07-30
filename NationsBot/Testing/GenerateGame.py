from logger import *

import pprint

from Utils import FileHandling, Mapping

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.GameObjects import *

def generateTestWorld():
	logInfo("Generating 'Test World' Worldmap...")

	world = Mapping.World("Test World")

	world.territories = {
		"Test (1,1)": Mapping.Territory((1, 1)),
		"Test (2,2)": Mapping.Territory((2, 2))
	}

	with open(f"{worldsDir}/Test World.json", 'w') as f:
		json.dump(FileHandling.saveObject(world), f, indent = 4)

	logInfo("Generated 'Test World'")
	return world

def generateGame():
	logInfo("Beginning game generation!")
	
	testWorld = generateTestWorld()

	savegame = Savegame(
		"TestGame",
		{"m": 1, "y": 1},
		1,
		"Test Gamerule",
		"Test World",
		nations = {
			"Nation01": Nation("Nation01")
		}
	)

	load_gamerule("Test Gamerule")
	
	setupNew_saveGame(0, savegame, "Test World", "Test Gamerule")
	save_saveGame(savegame)
	
	logInfo("Generated and saved game", FileHandling.saveObject(savegame))