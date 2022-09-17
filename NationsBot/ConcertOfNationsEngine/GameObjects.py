import pprint

from database import *
from logger import *

import ConcertOfNationsEngine.GameHandling as gamehandling

class Savegame:
    """
    Encapsulates everything in a game, including nations, the map, etc.
    
    Attributes:
        date (dict): Represents the ingame month (m) and year (y)
        turn (int): The turn number that the game is currently on
        nations (dict): Contains all the nations that populate the game, controlled by players.
    """
    
    def __init__(self, name, server_id, date, turn, nations = None, visibilities = None):
        self.name = name
        self.date = date
        self.turn = turn

        self.nations = nations or dict()
        self.visibilities = visibilities or dict()
        self.server_id = server_id

    def getRow(self):
        """
        Get the row in the database table Savegames pertaining to this savegame
        """
        return gamehandling.dbget_saveGame_byServer(self.server_id)

    def getWorld(self):
        logInfo("")
        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT worldfile FROM Savegames WHERE savefile=%s LIMIT 1;"
        params = [self.name]
        cursor.execute(stmt, params)
        result = cursor.fetchone()

        if not (result):
            return False

        logInfo("Got worldfile info")
        return gamehandling.load_world(result[0])

    def add_Nation(self, nation):

        if nation.name in self.nations.keys():
            raise Exception(f"Nation {nation.name} already exists in savegame {self.name}")

        self.nations[nation.name] = nation

    def world_toImage(self, mapScale = None):

        world = self.getWorld()

        colorRules = dict()

        for nation in self.nations.values():
            for territory in nation.territories:
                colorRules[territory] = tuple(nation.mapcolor)

        world.toImage(mapScale = mapScale, colorRules = colorRules)
    
    
class Nation:
    """
    Represents a nation, which controls a number of territories and ingame objects such as buildings and armies, as well as having an economy, meaning resources and their production.

    Attributes:
        resources (dict): Represents the total resources available for spending by the nation.
        territories (list): Holds the name of every territory owned by the nation.
    """

    def __init__(self, name, role_id, mapcolor, resources = None, territories = None):
        self.name = name
        self.mapcolor = mapcolor
        self.resources = resources or dict()
        self.territories = territories or list()

        self.role_id = role_id

    def getRow(self):
        """
        Get the row in the database table Roles pertaining to this savegame
        """

        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT * FROM Savegames WHERE discord_id=%s LIMIT 1;"
        params = [self.role_id]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False
        return result