import json

from logger import *

from database import *
from common import *
from Utils import FileHandling

from ConcertOfNationsEngine.GameObjects import *


def setupNew_saveGame(server_id, savegame, world, gamerule):
	"""
	Given a new savegame object, create a savefile for it and save it to the database.
	"""
	logInfo("Setting up a new savegame in the savefiles and database")
	
	#Update database
	'''
	cursor = getdb().cursor()

	stmt = "INSERT INTO Savegames (server_id, savefile, worldfile) VALUES (%s, %s, %s"
	'''

	#Generate savefile for the game
	
	pass

def save_saveGame(savegame):
	"""
	Save the savegame to its file based on its id
	"""
	with open(f"{savesDir}/{savegame.name}.json", 'w') as savefile:
		json.dump(FileHandling.saveObject(savegame), savefile, indent = 4)
	logInfo(f"Saved {savegame.name} to file: {savesDir}/{savegame.name}.json")

def load_saveGame(savegame_name):
	"""
	Load a savegame object from its savefile
	"""


def load_gamerule(gamerule_name):
	"""
	Load a dictionary from a .json file representing a game's ruleset
	"""
	logInfo(f"Loading Gamerule {gamerule_name} from file: {gameruleDir}/{gamerule_name}.json")

	with open(f"{gameruleDir}/{gamerule_name}.json", 'r') as gameruleFile:
		logInfo("Gamerule successfully loaded")
		return json.load(gameruleFile)

def load_world(world_name):
	"""
	Load a world from a .json file representing a map without nations, buildings etc; only terrain, resources etc.
	"""
	pass


def add_Nation(savegame, nation_name, roleID):
	"""
	Add a nation as a role to the database
	"""
	pass

