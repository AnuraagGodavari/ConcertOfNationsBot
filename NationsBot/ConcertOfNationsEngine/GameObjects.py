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

        gamestate (dict): Describes seperate aspects of the game as it presently exists. Format:
        [
            {
                "mapChanged": (bool) Has the map changed since the last time an image was generated?,
                "mapNum": (int) Which number map we are on for this turn
            }
        ]
    """
    
    def __init__(self, name, server_id, date, turn, nations = None, gamestate = None):
        self.name = name
        self.server_id = server_id
        self.date = date
        self.turn = turn

        self.nations = nations or dict()
        self.gamestate = gamestate or {
            "mapChanged": True,
            "mapNum": 0
        }

    def getRow(self):
        """
        Get the row in the database table Savegames pertaining to this savegame
        """
        return gamehandling.dbget_saveGame_byServer(self.server_id)

    def getWorld(self):
        """Get the world object that is associated with this game"""
        
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
        """Add a nation to this savegame if it does not already exist"""

        if nation.name in self.nations.keys():
            raise Exception(f"Nation {nation.name} already exists in savegame {self.name}")

        self.nations[nation.name] = nation
        logInfo(f"Successfully added nation {nation.name} to game {self.name}")

    def world_toImage(self, mapScale = None):
        """
        Given this savegame and it's associated world, get an image of that world based on the game state this turn.

        Args:
            mapScale(tuple): Format (x,y). Multiply literal distances between territories by these dimensions to enlarge the map image.
        """

        #Check if the map has changed since the last time an image was generated
        if (not self.gamestate["mapChanged"]):
            logInfo("Tried to create world image but one should already exist.")
            return

        world = self.getWorld()

        colorRules = dict()

        for nation in self.nations.values():
            for territory in nation.territories:
                colorRules[territory] = tuple(nation.mapcolor)

        logInfo("Retrieved nation colors")

        filename = f"{worldsDir}/{self.name}_{self.turn}-{self.gamestate['mapNum']}"
        worldfile = world.toImage(mapScale = mapScale, colorRules = colorRules, filename = filename)

        link = imgur.upload(f"{worldsDir}/{worldfile}")

        logInfo("Created map image of the world and uploaded it")

        gamehandling.insert_worldMap(world, self, worldfile, link, None)
        
        self.gamestate["mapChanged"] = False

        logInfo("Successfully generated, uploaded and saved world map")

    def find_terrOwner(self, territoryName):
        """
        Go through each nation and find which one owns a specific territory

        Returns: The name of the owner nation.
        """
        for nation in self.nations.values():
            if territoryName in nation.territories: return nation.name

        return False

    def transfer_territory(self, territoryName, targetNation):
        
        #Check if territory exists
        worldTerr = self.getWorld()[territoryName]
        if not (worldTerr):
            raise InputError(f"Territory {territoryName} does not exist")
            return False

        territoryName = worldTerr.name

        #Check territory owner
        prevOwner = self.find_terrOwner(territoryName)

        if not (prevOwner):
            logInfo(f"Territory {territoryName} is unowned")

        if (prevOwner == targetNation.name):
            raise NonFatalError(f"Territory {territoryName} already owned by {prevOwner}")
            return False

        try: 
            #Check if territory is owned, remove it
            if (prevOwner):
                terrInfo = self.nations[prevOwner].cedeTerritory(territoryName)

            else:
                terrInfo = {"name": territoryName}

            #Add this territory to the nation
            self.nations[targetNation.name].annexTerritory(territoryName, terrInfo)

        except Exception as e:
            raise InputError(f"Could not transfer the territory {territoryName} from {prevOwner} to {targetNation.name}")
            logError(e)
            return False

        #Does a new map need to be generated?
        if not (self.gamestate["mapChanged"]):
            self.gamestate["mapNum"] += 1

        self.gamestate["mapChanged"] = True

        logInfo(f"Transferred the territory {territoryName} from {prevOwner} to {targetNation.name}!")

        return True

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
        self.territories = territories or dict()

        self.role_id = role_id

    def cedeTerritory(self, territoryName):
        """
        Removes a territory and all associated objects from this nation
        
        Returns:
            terrInfo(dict): Includes territory name and all associated objects
        """

        logInfo(f"Nation {self.name} ceding territory {territoryName}")

        terrInfo = self.territories.pop(territoryName, False)

        logInfo(f"Nation {self.name} successfully ceded territory {territoryName}!")
        return terrInfo

    def annexTerritory(self, territoryName, territoryInfo):
        """
        Add a territory and related objects to this nation.
        
        Args:
            territoryInfo(dict): Includes the name of the territory and all associated objects
        """

        logInfo(f"Nation {self.name} annexing territory {territoryName}")

        self.territories[territoryName] = territoryInfo

        logInfo(f"Nation {self.name} successfully annexed territory {territoryName}!")

    def getTerritoryInfo(self, territory):
        """Get a territory and all objects associated with that territory."""

        if (territory in self.territories.values()):
            return self.territories[territory]

        return False