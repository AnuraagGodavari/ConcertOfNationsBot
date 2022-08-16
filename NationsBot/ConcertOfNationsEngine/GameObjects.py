import pprint

from database import *

import ConcertOfNationsEngine.GameHandling as gamehandling

class Savegame:
    """
    Encapsulates everything in a game, including nations, the map, etc.
    
    Attributes:
        date (dict): Represents the ingame month (m) and year (y)
        turn (int): The turn number that the game is currently on
        nations (dict): Contains all the nations that populate the game, controlled by players.
    """
    
    def __init__(self, name, date, turn, nations = None, visibilities = None):
        self.name = name
        self.date = date
        self.turn = turn

        self.nations = nations or dict()
        self.visibilities = visibilities or dict()

    def getWorld(self):
    
        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT worldfile FROM Savegames WHERE savefile=%s LIMIT 1;"
        params = [self.name]
        cursor.execute(stmt, params)
        result = cursor.fetchone()

        if (result == None): return False
        return gamehandling.load_world(result[0])

    def add_Nation(self, nation):
        self.nations[nation.name] = nation

    def world_toImage(self):

        world = self.getWorld()

        colorRules = dict()

        for nation in self.nations.values():
            for territory in nation.territories:
                colorRules[territory] = tuple(nation.mapcolor)

        world.toImage(colorRules)
    
    
class Nation:
    """
    Represents a nation, which controls a number of territories and ingame objects such as buildings and armies, as well as having an economy, meaning resources and their production.

    Attributes:
        resources (dict): Represents the total resources available for spending by the nation.
        territories (list): Holds the name of every territory owned by the nation.
    """

    def __init__(self, name, mapcolor, resources = None, territories = None):
        self.name = name
        self.mapcolor = mapcolor
        self.resources = resources or dict()
        self.territories = territories or list()