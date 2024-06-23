import pprint
from math import *
from copy import copy

from database import *
from logger import *
import imgur

from GameUtils import operations as ops
import GameUtils.filehandling as filehandling

import ConcertOfNationsEngine.gamehandling as gamehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

import ConcertOfNationsEngine.dateoperations as dates

import ConcertOfNationsEngine.buildings as buildings
import ConcertOfNationsEngine.territories as territories
import ConcertOfNationsEngine.populations as populations
import ConcertOfNationsEngine.military as military
import ConcertOfNationsEngine.diplomacy as diplomacy


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

    # Setup
    
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
        world = self.getWorld()

        #Generate an empty list of resources based on the gamerule, and make sure money is one of those included
        nation.resources = {resource: 0 for resource in gamerule["Resources"] + ["Money"]}

        #Add information to territories
        for territoryName, territory in nation.territories.items():

            if ("Buildings" not in territory.keys()):
                territory["Buildings"] = dict()

            if ("Population" not in territory.keys()):
                territory["Population"] = list()
        
            if ("Manpower" not in territory.keys()):
                territory["Manpower"] = 0
 
            if ("Nodes" not in territory.keys()):
                territory["Nodes"] = {resource: [0, capacity] for resource, capacity in world[territoryName].nodes.items()}
        #Add base bureaucratic capacity

        base_bureaucracy = gamerule["Base Bureaucracy"]
        nation.bureaucracy = {category: (0, base_bureaucracy[category]) for category in base_bureaucracy.keys()}

        self.nations[nation.name] = nation
        logInfo(f"Successfully added nation {nation.name} to game {self.name}")
        return nation


    # Get outside files that define the savegame

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


    # Get information from all nations

    def get_enemyForces(self, nation):
        """ Given a nation, return a combination of every military belonging to every other nation which is enemies with the current one. """
        enemy_militaries = ops.combineDicts(*[
            othernation.military 
            for othernation in self.nations.values() 
            if othernation.name in nation.diplomacy.keys() 
            and nation.diplomacy[othernation.name] == "Enemy"
            ])

        return enemy_militaries


    # Main operations

    def check_all_intercepting_forces(self, gamerule, numMonths):
        """ Check all the forces of each nation for any movements that will be intercepted by enemies """

        for nation in self.nations.values():
            for forcename in nation.military.keys():

                military.check_intercepting_forces(nation, forcename, gamerule, self, numMonths)

    def advanceTurn(self, numMonths: int):
        """Move the date forward and calculate new turn changes for each nation"""

        logInfo(f"Advancing Savegame {self.name} by {numMonths} from current date: {self.date} and current turn: {self.turn}")

        gamerule = self.getGamerule()

        newdate_raw = self.date['m'] - 1 + (self.date['y'] * 12) + numMonths
        self.date = {'m': (newdate_raw % 12) + 1, 'y': floor(newdate_raw / 12)}

        self.turn += 1

        self.check_all_intercepting_forces(gamerule, numMonths)

        for nation in self.nations.values():
            
            nation.newTurn(self, gamerule, numMonths)

        #New turn, so new map.
        self.gamestate["mapNum"] += 1
        self.gamestate["mapChanged"] = True

        logInfo(f"Successfully advanced date to date: {self.date} and turn: {self.turn}!")


    # Territory operations

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
        self.nations[targetNation.name].annexTerritory(territoryName, terrInfo, worldTerr, self)

        #Does a new map need to be generated?
        if not (self.gamestate["mapChanged"]):
            self.gamestate["mapNum"] += 1

        self.gamestate["mapChanged"] = True

        logInfo(f"Transferred the territory {territoryName} from {prevOwner} to {targetNation.name}!")

        return self.nations[targetNation.name].territories[territoryName]


    # Military operations

    def find_forceOwner(self, forcename):
        """
        Go through each nation and find which one owns a specific military force

        Returns: The name of the owner nation or False.
        """
        for nation in self.nations.values():
            if forcename in nation.military.keys(): return nation.name

        return False


    # Display

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


nationmodifiers_template = {
    "Tax": 0
}

class Nation:
    """
    Represents a nation, which controls a number of territories and ingame objects such as buildings and armies, as well as having an economy, meaning resources and their production.

    Attributes:
        resources (dict): Represents the total resources available for spending by the nation.
        territories (list): Holds the name of every territory owned by the nation.
        bureaucracy (dict): Represents the capacity and current load on each bureaucratic category of the nation, with values being tuples (load, capacity)
        tax_modifier (float): Added onto the base national tax rate and used to calculate the tax revenue from the national population
    """

    def __init__(self, name, role_id, mapcolor, resources = None, territories = None, bureaucracy = None, military = None, diplomacy = None, modifiers = None):
        self.name = name
        self.mapcolor = mapcolor
        self.resources = resources or dict()
        self.territories = territories or dict()
        self.military = military or dict()

        self.bureaucracy = bureaucracy or dict()
        for key, value in self.bureaucracy.items():
            self.bureaucracy[key] = tuple(value)

        self.role_id = role_id

        self.diplomacy = diplomacy or dict()
        
        self.modifiers = modifiers or copy(nationmodifiers_template)

    
    # Territory management

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

        for buildingName, statuses in terrInfo["Buildings"].items():

            for status in statuses:

                logInfo("statuses", details = statuses)

                if status == "Active":
                    self.remove_national_buildingeffects(buildings.get_alleffects(buildingName, savegame)["Nation"])

        self.territories.pop(territoryName)

        #Remove the effects on this territory of all buildings across the nation.
        blueprint = self.get_all_buildingeffects(savegame)
        if ("Nation" in blueprint.keys()):
            territories.add_buildingeffects(terrInfo, blueprint["Nation"], remove_modifiers = True)

        logInfo(f"Nation {self.name} successfully ceded territory {territoryName}!")
        return terrInfo

    def annexTerritory(self, territoryName, territoryInfo, worldTerritory, savegame):
        """
        Add a territory and related objects to this nation.
        
        Args:
            territoryInfo(dict): Includes the name of the territory and all associated objects
        """

        logInfo(f"Nation {self.name} annexing territory {territoryName}")

        #Add the effects on this territory of all buildings across the nation.
        blueprint = self.get_all_buildingeffects(savegame)
        if ("Nation" in blueprint.keys()):
            territories.add_buildingeffects(territoryInfo, blueprint["Nation"])

        self.territories[territoryName] = territoryInfo

        if ("Buildings" not in self.territories[territoryName].keys()):
            self.territories[territoryName]["Buildings"] = dict()

        if ("Population" not in self.territories[territoryName].keys()):
            self.territories[territoryName]["Population"] = list()

        if ("Manpower" not in self.territories[territoryName].keys()):
            self.territories[territoryName]["Manpower"] = 0

        if ("Nodes" not in self.territories[territoryName].keys()):
            self.territories[territoryName]["Nodes"] = {resource: [0, capacity] for resource, capacity in worldTerritory.nodes.items()}

        for buildingName, statuses in territoryInfo["Buildings"].items():

            for status in statuses:

                if status != "Active":
                    continue

                self.add_national_buildingeffects(buildings.get_alleffects(buildingName, savegame)["Nation"])

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


    # Economic management

    def validate_prerequisites(self, prerequisites, territoryName, only_active = False):
        """
        A blueprint may have prerequisites for being built, for example the existence of another building. If any prerequisite is not met, return False. Else return True
        Args:
            only_active (bool): True if we only want to validate with active buildings
        """
        
        if ("Buildings" in prerequisites):

            if ("Nation" in prerequisites["Buildings"]):

                allbuildings = [
                    building for territory in self.territories.values()
                     for building in territory["Buildings"].keys() 
                     if (not(only_active) or (territory["Buildings"][building] == "Active"))]

                for prerequisite in prerequisites["Buildings"]["Nation"]:
                    if prerequisite not in allbuildings:
                        raise InputError(f"Prerequisite {prerequisite} not available in nation")

            if ("Territory" in prerequisites["Buildings"]):

                territory = self.territories[territoryName]

                allbuildings = [
                    building for building in territory["Buildings"].keys()
                     if (not(only_active) or (territory["Buildings"][building] == "Active"))]

                for prerequisite in prerequisites["Buildings"]["Territory"]:
                    if prerequisite not in allbuildings:
                        raise InputError(f"Prerequisite {prerequisite} not available in territory")
                

        return True

    def can_buyBlueprint(self, blueprintName, blueprint, territoryName, active_prerequisites = False):
        """
        Check if a blueprint's resource and bureaucratic costs are affordable by a nation and the prerequisites are met.
        """
        #Do we have enough resources to build this?

        for resource in blueprint["Costs"].keys():
            if (blueprint["Costs"][resource] > self.resources[resource]):
                raise InputError(f"Not enough {resource} to build {blueprintName}")

        for category, cost in blueprint["Bureaucratic Cost"].items():
            if (cost > self.bureaucracy[category][1] - self.bureaucracy[category][0]):
                raise InputError(f"Not enough bureaucratic capacity for {category}: {self.bureaucracy[category][0]}/{self.bureaucracy[category][1]}")

        if ("Prerequisites" in blueprint.keys()):
            if not (self.validate_prerequisites(blueprint["Prerequisites"], territoryName, active_prerequisites)):
                return False

        return True

    def canHoldBuilding(self, buildingName, blueprint, territory):
        """ 
        Validate that a territory has enough space for a building.
        """

        if not (buildingName in territory["Savegame"]["Buildings"].keys()):
            return True

        # Check if this territory can hold one more of this building 
        if ("Territory Maximum" in blueprint):
            num_buildings = len(territory["Savegame"]["Buildings"][buildingName])
            
            if (num_buildings >= blueprint["Territory Maximum"]):
                return False

        elif (buildingName in territory["Savegame"]["Buildings"].keys()):
                return False

        return True

    def enoughNodesForBuilding(self, blueprint, territory):
        """ 
        Validate that a territory has enough nodes for a building.
        """

        # Check if this territory has enough available resource nodes
        if ("Node Costs" in blueprint):
            for nodeType in blueprint["Node Costs"].keys():

                available_nodes = territory["Savegame"]["Nodes"]

                if not(nodeType in available_nodes):
                    return False

                if (blueprint["Node Costs"][nodeType] + available_nodes[nodeType][0] > available_nodes[nodeType][1]):
                    return False

        return True

    def canBuyBuilding(self, savegame, buildingName, blueprint, territoryName):
        """
        Validate that an building with a given blueprint can be bought by this country
        """

        #Does the building already exist in this territory?
        territory = self.getTerritoryInfo(territoryName, savegame)

        if not(territory):
            raise InputError(f"{self.name} does not own territory \"{territoryName}\"")

        if not (self.canHoldBuilding(buildingName, blueprint, territory)):

            max_num = 1
            if ("Territory Maximum" in blueprint.keys()): max_num = blueprint['Territory Maximum'] 

            raise InputError(f"{len(territory['Savegame']['Buildings'][buildingName])} of Building {buildingName} already exist in territory {territoryName}, maximum is {max_num}")

        if not (self.enoughNodesForBuilding(blueprint, territory)):

            raise InputError(f"{buildingName} requires nodes: {blueprint['Node Costs']} and territory {territoryName} only has nodes: {territory['Savegame']['Nodes']}")

        return self.can_buyBlueprint(buildingName, blueprint, territoryName)


    # Building management

    def addBuilding(self, buildingName, territoryName, savegame):
        """ Add a building to a territory and subtract the resource cost """

        logInfo(f"Nation {self.name} purchasing {buildingName} for {territoryName}")

        blueprint = buildings.get_blueprint(buildingName, savegame)

        territory = self.get_territory(territoryName)

        #Subtract resource costs
        costs = blueprint["Costs"]
        for k, v in costs.items(): self.resources[k] = self.resources[k] - v

        #Add Bureaucratic Costs
        bureaucratic_costs = blueprint["Bureaucratic Cost"]
        for k, v in bureaucratic_costs.items(): self.bureaucracy[k] = (self.bureaucracy[k][0] + v, self.bureaucracy[k][1])

        constructiondate = dates.date_tostr(dates.date_add(savegame.date, int(blueprint['Construction Time'])))

        territories.add_building(self, territoryName, buildingName, f"Constructing:{constructiondate}", blueprint)

        logInfo(f"Added {buildingName} to {territoryName}! Status: {self.territories[territoryName]['Buildings'][buildingName]}")

        return self.territories[territoryName]['Buildings'][buildingName]

    def get_all_buildingeffects(self, savegame):
        """
        Get the combined effects of all buildings in this nation
        """
        all_effects = list()

        #Remove the effects on this territory of all buildings across the nation.
        for owned_territory in self.territories.values():
            for buildingName, statuses in owned_territory["Buildings"].items():
                for status in statuses:
                    if status == "Active": all_effects.append(buildings.get_alleffects(buildingName, savegame))

        return ops.combineDicts(*all_effects)

    def add_populationeffects(self, effects, remove_modifiers = False):
        """
        Add all effects and modifiers from a source to all populations in the nation
        """

        for territory in self.territories.values():
            territories.apply_population_modifiers(territory, effects, remove_modifiers)


    def add_national_buildingeffects(self, effects):
        """
        Given a building, add its effects to this nation
        """

        logInfo("Adding national building effects")

        #Add bureaucracy values
        if ("Bureaucracy" in effects.keys()):
            for category, val in effects["Bureaucracy"].items(): self.bureaucracy[category] = (self.bureaucracy[category][0], self.bureaucracy[category][1] + val)

        if ("National Modifiers" in effects.keys()):
            self.modifiers = ops.combineDicts(self.modifiers, effects["National Modifiers"])

        if ("Population" in effects.keys()):
            self.add_populationeffects(effects["Population"])
        
    def add_buildingeffects(self, effects, territoryInfo):
        """
        Given a building, add its effects to both the nation and territory
        """

        if ("Nation" in effects.keys()):
            self.add_national_buildingeffects(effects["Nation"])

        if ("Territory" in effects.keys()):
            territories.add_buildingeffects(territoryInfo, effects["Territory"])
                

    def remove_national_buildingeffects(self, effects):
        """
        Given a building, add its effects to the nation
        """

        logInfo("Removing national building effects")

        #Remove bureaucracy values
        if ("Bureaucracy" in effects.keys()):
            for category, val in effects["Bureaucracy"].items(): self.bureaucracy[category] = (self.bureaucracy[category][0], self.bureaucracy[category][1] - val)

        if ("National Modifiers" in effects.keys()):
            self.modifiers = ops.combineDicts(self.modifiers, effects["National Modifiers"], subtractDicts = True)

        if ("Population" in effects.keys()):
            self.add_populationeffects(effects["Population"], remove_modifiers = True)
                
    def remove_buildingeffects(self, effects, territoryInfo):
        """
        Given a building, remove its effects both from the nation and territory
        """

        if ("Nation" in effects.keys()):
            self.remove_national_buildingeffects(effects["Nation"])

        if ("Territory" in effects.keys()):
            territories.add_buildingeffects(territoryInfo, effects["Territory"], remove_modifiers = True)


    # Military management

    def can_build_unit(self, savegame, territoryName, unitType, blueprint, size):
        """ Validate whether a territory can build a unit """

        #Does the building already exist in this territory?
        territory = self.getTerritoryInfo(territoryName, savegame)

        if not(territory):
            raise InputError(f"{self.name} does not own territory \"{territoryName}\"")

        if (size > territories.get_manpower(self, territoryName)):
            raise InputError(f"{territoryName} has too little manpower to recruit {size} {unitType}")

        return self.can_buyBlueprint(unitType, blueprint, territoryName, active_prerequisites = True)

    def can_build_vehicle(self, savegame, territoryName, unitType, blueprint, size):
        """ Validate whether a territory can build a vehicle; wrapper for can_build_unit. """

        return self.can_build_unit(savegame, territoryName, unitType, ops.combineDicts(*[blueprint]*size), blueprint["Crew"] * size)

    def build_unit(self, territoryName, unitType, size, blueprint, savegame):
        """ Build a unit of a specified size in a territory """

        logInfo(f"{self.name} creating {unitType} of size {size} in territory {territoryName}")

        territory = self.get_territory(territoryName)
        name = military.new_unitName(self.military, name_template = f"{self.name} {territoryName} {unitType}")

        #Subtract resource costs
        costs = blueprint["Costs"]
        for k, v in costs.items(): self.resources[k] = self.resources[k] - round((v * size), 4)

        bureaucratic_costs = blueprint["Bureaucratic Cost"]
        for k, v in bureaucratic_costs.items(): self.bureaucracy[k] = (round(self.bureaucracy[k][0] + (v * size), 4), self.bureaucracy[k][1])

        constructiondate = dates.date_tostr(dates.date_add(savegame.date, int(blueprint['Construction Time'])))
        constructionstatus = f"Constructing:{constructiondate}"

        newunit = military.load_fromBlueprint(name, blueprint, constructionstatus, unitType, size, territoryName)

        territory["Manpower"] -= size
        forcename = military.new_forceName([name for nation in savegame.nations.values() for name in nation.military.keys()], name_template = f"{self.name} Force")
        self.military[forcename] = {
            "Status": constructionstatus,
            "Location": territoryName,
            "Units": {name: newunit}
        }

        return forcename

    def build_vehicle(self, territoryName, vehicleType, size, blueprint, savegame):
        """ Build a vehicle in a specified amount in a territory; wrapper for build_unit. """

        forcenames = [
            self.build_unit(territoryName, vehicleType, blueprint["Crew"], blueprint, savegame)
            for num in range(size)
        ]

        baseForcename = forcenames[0]

        baseForce = self.military[baseForcename]

        forces  = [self.pop_force(forcename) for forcename in forcenames[1:]]

        self.combine_forces(
            baseForce,
            *forces
        )

        return baseForcename
    
    def combine_forces(self, base_force, added_forces):

        military.combine_forces(base_force, added_forces)

        return base_force

    def pop_force(self, forcename):

        return self.military.pop(forcename)


    # Population management

    def all_populations(self):
        """Get a list of all the populations in all of this nation's territories"""

        return {territoryName: territoryInfo["Population"] for territoryName, territoryInfo in self.territories.items()}


    # New turn functions
    
    def get_taxrate(self, gamerule):
        return gamerule["Base National Modifiers"]["Tax"] + self.modifiers["Tax"]

    def get_taxincome(self, gamerule):
        return sum([min(pop.size - pop.manpower, pop.size) for popslist in self.all_populations().values() for pop in popslist]) * self.get_taxrate(gamerule)

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
        gamerule = savegame.getGamerule()

        for territoryName in self.territories.keys():

            territoryInfo = self.getTerritoryInfo(territoryName, savegame)

            if (not onlyestimate):
                neweffects = territories.advanceconstruction(territoryInfo, savegame, self.bureaucracy)

                if (neweffects): 
                    self.add_buildingeffects(neweffects, territoryInfo["Savegame"])

            territories.validate_building_requirements(territoryName, self, savegame)

            revenuesources.append(territories.newturnresources(territoryInfo, savegame))

        if (onlyestimate):
            for force in self.military.values():
                for unit in force["Units"].values(): revenuesources.append(unit.get_resources(military.get_blueprint(unit.unitType, gamerule)))

        totalrevenue = ops.combineDicts(*revenuesources)

        return totalrevenue

    def add_newTurn_Resources(self, savegame, numMonths):
        """Get the net change in resources for this nation for the new turn"""
        logInfo(f"Nation {self.name} calculating total resource net income for this turn")

        gamerule = savegame.getGamerule()

        #Add resource revenue to self.resources
        revenue = self.get_TurnRevenue(savegame)

        for resource in revenue.keys():
            revenue[resource] *= numMonths

        self.resources = ops.combineDicts(self.resources, revenue)
        self.resources["Money"] = (self.resources["Money"] + self.get_taxincome(gamerule) * numMonths)

        logInfo(f"Successfully calculated net income for {self.name}")

    def grow_population(self, gamerule, numMonths):
        """Grow the population of each territory in this nation"""

        logInfo(f"Nation {self.name} growing population")

        for territoryName, territoryInfo in self.territories.items():

            territories.grow_all_populations(territoryInfo, numMonths)

            logInfo(f"Territory {territoryName} grew population")

        logInfo(f"Nation {self.name} successfully grew population")

    def military_newTurn(self, savegame, gamerule, numMonths):
        """Get military costs and advance unit construction for this nation"""

        logInfo(f"Nation {self.name} doing new turn military functions")

        resourcecosts = []

        for force in self.military.values():
            resourcecosts.append(military.newturn(force, savegame, gamerule, numMonths, self.bureaucracy))

        self.resources = ops.combineDicts(self.resources, *resourcecosts)

    def newTurn(self, savegame, gamerule, numMonths):
        """Perform tasks for the end of a current turn"""

        self.grow_population(gamerule, numMonths)

        self.add_newTurn_Resources(savegame, numMonths)

        self.military_newTurn(savegame, gamerule, numMonths)
