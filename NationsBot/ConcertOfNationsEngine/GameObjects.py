import pprint

from database import *
from logger import *
import imgur

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
        logInfo(f"Getting world for savegame {self.name} from database")
        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT Worlds.* FROM Savegames JOIN Worlds ON Savegames.world_id = Worlds.id WHERE savefile=%s LIMIT 1;"
        params = [self.name]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result):
            return False

        logInfo("Got worldfile info")
        return gamehandling.load_world(result["name"])

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

        worldfile = world.toImage(mapScale = mapScale, colorRules = colorRules)
        link = imgur.upload(f"{worldsDir}/{worldfile}")

        gamehandling.insert_worldMap(world, self, worldfile, link, None)

    def find_terrOwner(self, territoryName):
        """
        Go through each nation and find which one owns a specific territory

        Returns: The name of the owner nation.
        """
        for nation in self.nations.values():
            if territoryName in nation.territories: return nation.name

        return False


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

    def cedeTerritory(self, territoryName):

        logInfo(f"Nation {self.name} ceding territory {territoryName}")        

        terrInfo = dict()

        terrInfo["name"] = territoryName
        self.territories.remove(territoryName)

        logInfo(f"Nation {self.name} successfully ceded territory {territoryName}!")
        return terrInfo

    def annexTerritory(self, territoryInfo):
        
        logInfo(f"Nation {self.name} annexing territory {territoryInfo['name']}")

        self.territories.append(territoryInfo["name"])

        logInfo(f"Nation {self.name} successfully annexed territory {territoryInfo['name']}!")