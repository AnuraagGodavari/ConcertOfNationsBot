import json, pprint, random
from PIL import Image, ImageDraw, ImageFont

from logger import *
from common import *

class Territory:
    """
    Analogous to a Vertex in a Graph. Represents one territory in a network of territories.

    Attributes:
        pos (tuple): Represents the coordinate position of the territory
        edges (dict): Represents the adjacent territories. Keys are territory names, values are the distance to them.
        details (dict): Information used in other files. For example, resources.
    """

    def __init__(self, id, pos, edges = None, details = None):
        self.id = id
        self.pos = pos
        self.edges = edges or dict()
        self.details = details or dict()


class World:
    """
    Analogous to a Graph made up of vertices. Represents a game world made up of individual territories, connected in a vast network.

    Attributes:
        territories (dict): Keys are territory names, values are the objects.
    """

    def __init__(self, name, territories = None, numTerritories = 0):
        self.name = name
        self.territories = territories or dict()
        self.numTerritories = numTerritories

    def addNewTerritory(self, name, pos, edges = None, details = None):
        self.territories[name] = Territory(self.numTerritories, pos, edges, details)
        self.numTerritories += 1

    def calculateAllNeighbors(self, neighborRules):
        """
        Calculates which territories are connecte to which others based on a ruleset.

        Args:
            neighborRules (list): A list of rules, represented as dictionaries following the format:
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

    def toImage(self):
        
        #Represents the extra space between min/max X/Y and the borders of the image.
        coordOffset = (75, 75)
        mapScale = (400, 400)
        terrSize = (32, 32)

        #Represents the max render length of an edge.#If an edge is more than edgeDrawLimits[1], then shrink the map so it draws it as long as edgeDrawLimits[1] would before.
        #If an edge is less than edgeDrawLimits[0], then inflate the map so it draws it as long as edgeDrawLimits[0] would before.
        edgeDrawLimits = (1, 2)

        courierFont = ImageFont.truetype(f"{fontsDir}/courier.ttf", 24)

        #Initialize min and max X and Y values to the X and Y coords of the first territory in the dict of territories
        firstT = self.territories[next(iter(self.territories))]
        minX, maxX, minY, maxY = firstT.pos[0], firstT.pos[0], firstT.pos[1], firstT.pos[1]
        minEdge = float('inf')
        maxEdge = -1
        
        for t in self.territories.values():
            minX = min(minX, t.pos[0])
            maxX = max(maxX, t.pos[0])
            minY = min(minY, t.pos[1])
            maxY = max(maxY, t.pos[1])
            if t.edges:
                minEdge = min(minEdge, min(t.edges.values()))
                maxEdge = max(maxEdge, max(t.edges.values()))

        mapScale = (
            int(mapScale[0] * min(1, edgeDrawLimits[1] / maxEdge)),
            int(mapScale[1] * min(1, edgeDrawLimits[1] / maxEdge))
        )

        dim = (maxX-minX, maxY-minY)
        #Where the territories are placed on the map relative to 0 is measured by coordinates minus offset
        terrOffset = (0 - minX + coordOffset[0], 0 - minY + coordOffset[0])

        out_img = Image.new("RGBA", (
            (dim[0] * mapScale[0]) + (coordOffset[0]*2), 
            (dim[1] * mapScale[1]) + (coordOffset[1]*2)
            ),
            (200, 200, 200)
        )
        imgDraw = ImageDraw.Draw(out_img)

        #Draw territories on the map
        for terr in self.territories.values():

            #Draw territory edges on the map
            for neighborName, neighbor in terr.edges.items():
                neighbor = self.territories[neighborName]

                if neighbor.id < terr.id:

                    imgDraw.line(
                        [
                            ((terr.pos[0] * mapScale[0]) + terrOffset[0],
                            (terr.pos[1] * mapScale[1]) + terrOffset[1]),
                            ((neighbor.pos[0] * mapScale[0]) + terrOffset[0],
                            (neighbor.pos[1] * mapScale[1]) + terrOffset[1])
                        ],
                        fill = "black"
                    )

            #Now draw the territory as a circle
            imgDraw.ellipse(
                (
                    (terr.pos[0] * mapScale[0]) + terrOffset[0] - (terrSize[0]/2),
                    (terr.pos[1] * mapScale[1]) + terrOffset[1] - (terrSize[0]/2),
                    (terr.pos[0] * mapScale[0]) + terrOffset[0] + (terrSize[0]/2),
                    (terr.pos[1] * mapScale[1]) + terrOffset[1] + (terrSize[0]/2)
                ), 
            fill = (255,255,255),
            outline = (0,0,0))

            #Draw the territory's ID number nearby
            imgDraw.text(
                (
                    (terr.pos[0] * mapScale[0]) + (terrSize[0]/2) + terrOffset[0],
                    (terr.pos[1] * mapScale[1]) - terrSize[1] + terrOffset[1]
                ),
                str(terr.id), font=courierFont, fill="black")

        out_img.save(f"{worldsDir}/{self.name}.png")

        logInfo(f"Successfully saved world {self.name}!")