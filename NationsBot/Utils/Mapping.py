import json, pprint, random
from PIL import Image, ImageDraw, ImageFont


class Territory:
    """
    Analogous to a Vertex in a Graph. Represents one territory in a network of territories.

    Attributes:
        pos (tuple): Represents the coordinate position of the territory
        edges (dict): Represents the adjacent territories. Keys are territory names, values are the distance to them.
        details (dict): Information used in other files. For example, resources.
    """

    def __init__(self, pos, edges = None, details = None):
        self.pos = pos
        self.edges = edges or dict()
        self.details = details or dict()


class World:
    """
    Analogous to a Graph made up of vertices. Represents a game world made up of individual territories, connected in a vast network.

    Attributes:
        territories (dict): Keys are territory names, values are the objects.
    """

    def __init__(self, name, territories = None):
        self.name = name
        self.territories = territories or dict()