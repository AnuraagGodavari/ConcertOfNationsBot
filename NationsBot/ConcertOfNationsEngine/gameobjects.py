import pprint
from math import *
from copy import copy

from database import *
from logger import *
import imgur

from GameUtils import operations as ops

import ConcertOfNationsEngine.gamehandling as gamehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

import ConcertOfNationsEngine.dateoperations as dates

import ConcertOfNationsEngine.buildings as buildings
import ConcertOfNationsEngine.territories as territories


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

    #Setup
    
    def __init__(self, name, server_id, date: dict, turn, nations = None, gamestate = None):

        self.name = name
        self.server_id = server_id
        self.date = {'m': date['m'], 'y': date['y']}
        self.turn = turn

        self.nations = nations or dict()
        self.gamestate = gamestate or {
            "mapChanged": True,
            "mapNum": 0
        }

    def add_Nation(self, nation):
        """Add a nation to this savegame if it does not already exist"""

        if nation.name in self.nations.keys():
            logInfo(f"Nation {nation.name} already exists in savegame {self.name}")
            return False

        gamerule = self.getGamerule()

        #Generate an empty list of resources based on the gamerule, and make sure money is one of those included
        nation.resources = {resource: 0 for resource in gamerule["Resources"] + ["Money"]}

        #Add information to territories
        for territory in nation.territories.values():

            if ("Buildings" not in territory.keys()):
                territory["Buildings"] = {} 
        
        #Add base bureaucratic capacity

        base_bureaucracy = gamerule["Base Bureaucracy"]
        nation.bureaucracy = {category: (0, base_bureaucracy[category]) for category in base_bureaucracy.keys()}

        self.nations[nation.name] = nation
        logInfo(f"Successfully added nation {nation.name} to game {self.name}")
        return nation


    #Get outside files that define the savegame

    def getRow(self):
        """
        Get the row in the database table Savegames pertaining to this savegame
        """
        return gamehandling.dbget_saveGame_byServer(self.server_id)

    def getWorld(self):
        """Get the world object that is associated with this game"""

        return gamehandling.dbget_world_bysavegame(self.server_id)

    def getGamerule(self):
        """Get the gamerule that is associated with this game"""

        return gamehandling.dbget_gamerule(self.server_id)


    #Main operations

    def advanceTurn(self, numMonths: int):
        """Move the date forward and calculate new turn changes for each nation"""

        logInfo(f"Advancing Savegame {self.name} by {numMonths} from current date: {self.date} and current turn: {self.turn}")

        newdate_raw = self.date['m'] - 1 + (self.date['y'] * 12) + numMonths
        self.date = {'m': (newdate_raw % 12) + 1, 'y': floor(newdate_raw / 12)}

        self.turn += 1

        for nation in self.nations.values():
            
            nation.newTurn(self, numMonths)

        logInfo(f"Successfully advanced date to date: {self.date} and turn: {self.turn}!")

    #Territory operations

    def get_territory_fromworld(self, territoryName):
        
        worldmap = self.getWorld()

        if not(worldmap[territoryName]):
            return False

        return {
                "Resources": worldmap[territoryName].resources,
                "Details": worldmap[territoryName].details
            }


    def find_terrOwner(self, territoryName):
        """
        Go through each nation and find which one owns a specific territory

        Returns: The name of the owner nation or False.
        """
        for nation in self.nations.values():
            if territoryName in nation.territories.keys(): return nation.name

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
            logInfo(f"Territory {territoryName} already owned by {prevOwner}")
            return False

        #Check if territory is owned, remove it
        if (prevOwner):
            terrInfo = self.nations[prevOwner].cedeTerritory(territoryName, self)

        else:
            terrInfo = {"name": territoryName}

        if not (terrInfo):
            logInfo("Ceding territory failed")
            return False

        #Add this territory to the nation
        self.nations[targetNation.name].annexTerritory(territoryName, terrInfo, self)

        #Does a new map need to be generated?
        if not (self.gamestate["mapChanged"]):
            self.gamestate["mapNum"] += 1

        self.gamestate["mapChanged"] = True

        logInfo(f"Transferred the territory {territoryName} from {prevOwner} to {targetNation.name}!")

        return self.nations[targetNation.name].territories[territoryName]


    #Display

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

        logInfo("Creating new world map image")

        world = self.getWorld()

        colorRules = dict()

        for nation in self.nations.values():
            for territory in nation.territories:
                colorRules[territory] = tuple(nation.mapcolor)

        logInfo("Retrieved nation colors")

        filename = f"{worldsDir}/{self.name}_{self.turn}-{self.gamestate['mapNum']}"
        worldfile = world.toImage(mapScale = mapScale, colorRules = colorRules, filename = filename)

        link = imgur.upload(worldfile)

        logInfo("Created map image of the world and uploaded it")

        gamehandling.insert_worldMap(world, self, worldfile, link, None)
        
        self.gamestate["mapChanged"] = False

        logInfo("Successfully generated, uploaded and saved world map")


class Nation:
    """
    Represents a nation, which controls a number of territories and ingame objects such as buildings and armies, as well as having an economy, meaning resources and their production.

    Attributes:
        resources (dict): Represents the total resources available for spending by the nation.
        territories (list): Holds the name of every territory owned by the nation.
        bureaucracy (dict): Represents the capacity and current load on each bureaucratic category of the nation, with values being tuples (load, capacity)
    """

    def __init__(self, name, role_id, mapcolor, resources = None, territories = None, bureaucracy = None):
        self.name = name
        self.mapcolor = mapcolor
        self.resources = resources or dict()
        self.territories = territories or dict()

        self.bureaucracy = bureaucracy or dict()
        for key, value in self.bureaucracy.items():
            self.bureaucracy[key] = tuple(value)

        self.role_id = role_id

    
    #Territory management

    def cedeTerritory(self, territoryName, savegame):
        """
        Removes a territory and all associated objects from this nation
        
        Returns:
            terrInfo(dict): Includes territory name and all associated objects
        """

        logInfo(f"Nation {self.name} ceding territory {territoryName}")

        terrInfo = copy(self.get_territory(territoryName))

        if not terrInfo: 
            logInfo(f"Nation {self.name} could not cede territory {territoryName}!")
            return False

        for buildingName, status in terrInfo["Buildings"].items():

            if status != "Active":
                continue

            self.remove_buildingeffects(buildings.get_alleffects(buildingName, savegame))

        self.territories.pop(territoryName)

        logInfo(f"Nation {self.name} successfully ceded territory {territoryName}!")
        return terrInfo

    def annexTerritory(self, territoryName, territoryInfo, savegame):
        """
        Add a territory and related objects to this nation.
        
        Args:
            territoryInfo(dict): Includes the name of the territory and all associated objects
        """

        logInfo(f"Nation {self.name} annexing territory {territoryName}")

        self.territories[territoryName] = territoryInfo

        if ("Buildings" not in self.territories[territoryName].keys()):
            self.territories[territoryName]["Buildings"] = {} 

        for buildingName, status in territoryInfo["Buildings"].items():

            if status != "Active":
                continue

            self.add_buildingeffects(buildings.get_alleffects(buildingName, savegame))

        logInfo(f"Nation {self.name} successfully annexed territory {territoryName}!")

    def get_territory(self, territoryName):
        """
        Get the nation-related information about a territory this nation owns
        """

        if not (territoryName in self.territories.keys()):
            return False

        return self.territories[territoryName]

    def getTerritoryInfo(self, territoryName, savegame):
        """Get a reference to a territory as stored in this savegame and the associated world, as well as all objects within it."""

        world_terrInfo = savegame.get_territory_fromworld(territoryName)

        nation_terrInfo = self.get_territory(territoryName)

        if not(world_terrInfo and nation_terrInfo):
            return False

        territoryInfo = {
            "Name": territoryName,
            "Savegame": nation_terrInfo,
            "World": world_terrInfo
        }

        return territoryInfo


    #Economic management
    def canBuyBuilding(self, savegame, buildingName, blueprint, territoryName):
        """
        Validate that an building with a given blueprint can be bought by this country
        """

        #Does the building already exist in this territory?
        territory = self.getTerritoryInfo(territoryName, savegame)

        if not(territory):
            logInfo(f"{self.name} does not own territory \"{territoryName}\"")
            return False

        if buildingName in territory["Savegame"]["Buildings"].keys():
            logInfo(f"Building {buildingName} already exists in territory {territoryName}")
            return False

        #Do we have enough resources to build the building?

        for resource in blueprint["Costs"].keys():
            if (blueprint["Costs"][resource] > self.resources[resource]):
                logInfo(f"Not enough resources to build {buildingName}", details = {"Costs": blueprint["Costs"], "Resources Available": self.resources})
                return False

        for category, cost in blueprint["Bureaucratic Cost"].items():
            if (cost > self.bureaucracy[category][1] - self.bureaucracy[category][0]):
                logInfo(f"Not enough bureaucratic capacity for {category}: {self.bureaucracy[category][0]}/{self.bureaucracy[category][1]}")
                return False

        return True


    #Building management

    def addBuilding(self, buildingName, territoryName, savegame):
        """ Add a building to a territory and subtract the resource cost """

        logInfo(f"Nation {self.name} purchasing {buildingName} for {territoryName}")

        blueprint = buildings.get_blueprint(buildingName, savegame)

        #Subtract resource costs
        costs = blueprint["Costs"]
        for k, v in costs.items(): self.resources[k] = self.resources[k] - v

        bureaucratic_costs = blueprint["Bureaucratic Cost"]
        for k, v in bureaucratic_costs.items(): self.bureaucracy[k] = (self.bureaucracy[k][0] + v, self.bureaucracy[k][1])

        constructiondate = dates.date_tostr(dates.date_add(savegame.date, int(blueprint['Construction Time'])))

        self.territories[territoryName]["Buildings"][buildingName] = f"Constructing:{constructiondate}"

        logInfo(f"Added {buildingName} to {territoryName}! Status: {self.territories[territoryName]['Buildings'][buildingName]}")

        return self.territories[territoryName]['Buildings'][buildingName]

    def add_buildingeffects(self, effects):
        """
        Given a building, add its effects to the nation
        """

        pass

    def remove_buildingeffects(self, effects):
        """
        Given a building, add its effects to the nation
        """

        pass

    #New turn functions
    
    def get_TurnRevenue(self, savegame, onlyestimate = False):
        """
        Get the total amount of resources that each territory this nation owns will produce.
        
        Args:
            onlyestimate (bool): Skip new turn-related operations and only return the raw information. May be useful for display purposes.
        """
        logInfo(f"Nation {self.name} getting total amount of resources produced per turn")

        totalrevenue = {}
        revenuesources = []

        worldmap = savegame.getWorld()

        for territoryName in self.territories.keys():

            territoryInfo = self.getTerritoryInfo(territoryName, savegame)

            if onlyestimate: continue
            territories.territory_advanceconstruction(territoryInfo, savegame, self.bureaucracy)

            revenuesources.append(territories.territory_newturnresources(territoryInfo, savegame))

        totalrevenue = ops.combineDicts(*revenuesources)

        return totalrevenue

    def add_newTurn_Resources(self, savegame, numMonths):
        """Get the net change in resources for this nation for the new turn"""
        logInfo(f"Nation {self.name} calculating total resource net income for this turn")

        #Add resource revenue to self.resources
        revenue = self.get_TurnRevenue(savegame)

        for resource in revenue.keys():
            revenue[resource] *= numMonths

        self.resources = ops.combineDicts(self.resources, revenue)

        logInfo(f"Successfully calculated net income for {self.name}")

    def newTurn(self, savegame, numMonths):
        """Perform tasks for the end of a current turn"""
        
        self.add_newTurn_Resources(savegame, numMonths)
