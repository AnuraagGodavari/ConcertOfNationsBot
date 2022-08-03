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

    def calculateAllNeighbors(self, neighborRules):
        """
        Calculates which territories are connecte to which others based on a ruleset.

        Args:
            neighborRules (dict): Follows the format:
                {
                    "t0": {values for some keys in t0.details},
                    "t1": {values for some keys in t1.details},
                    "maxDist": Maximum distance the two territories can be from each other and be connected.
                }
        """

        for t0name, t0 in self.territories.items():
            for t1name, t1 in self.territories.items():

                if t0name == t1name: continue

                for rule in neighborRules:

                    for key, value in rule["t0"].items():
                        if (t0.details[key] != value):
                            continue

                    for key, value in rule["t1"].items():
                        if (t1.details[key] != value):
                            continue

                    pointDist = (((t0.pos[0] - t1.pos[0])**2) + ((t0.pos[1] - t1.pos[1])**2))**0.5
                    if (pointDist <= rule["maxDist"]):
                        t0.edges[t1name] = pointDist
                        t1.edges[t0name] = pointDist

                    continue