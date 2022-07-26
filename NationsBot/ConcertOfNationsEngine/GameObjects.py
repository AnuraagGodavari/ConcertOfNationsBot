class Savegame:
	"""
	Encapsulates everything in a game, including nations, the map, etc.
	
	Attributes:
		nations (list): The set of all the nations that exist in the game.
		date (dict): Represents the ingame month (m) and year (y)
	"""
	
	def __init__(self, name, date, nations = None):
		self.name = name
		self.date = date
		self.nations = nations or dict()
	
	
class Nation:
	
	def __init__(self, name):
		self.name = name