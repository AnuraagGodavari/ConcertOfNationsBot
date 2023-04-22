import json, pprint, random
from PIL import Image, ImageDraw, ImageFont

from logger import *
from common import *

from ConcertOfNationsEngine.concertofnations_exceptions import *

class Territory:
    """
    Analogous to a Vertex in a Graph. Represents one territory in a network of territories.

    Attributes:
        pos (tuple): Represents the coordinate position of the territory
        edges (dict): Represents the adjacent territories. Keys are territory names, values are the distance to them.
        details (dict): Information used in other files. For example, resources.
    """

    def __init__(self, name, id, pos, edges = None, details = None, resources = None):
        self.name = name
        self.id = id
        self.pos = pos
        self.edges = edges or dict()
        self.details = details or dict()
        self.resources = resources or dict()


class World:
    """
    Analogous to a Graph made up of vertices. Represents a game world made up of individual territories, connected in a vast network.

    Attributes:
        territories (dict): Keys are territory names, values are the objects.
    """

    def __init__(self, name, territories = None):
        self.name = name
        self.territories = territories or list()

    def addNewTerritory(self, name, pos, edges = None, details = None, resources = None):
        
        self.territories.append(Territory(name, len(self.territories), pos, edges, details, resources))

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

        for t0 in self.territories:
            for t1 in self.territories:

                if t0.id == t1.id: continue

                for rule in neighborRules:

                    for key, value in rule["t0"].items():
                        if (t0.details[key] != value):
                            continue

                    for key, value in rule["t1"].items():
                        if (t1.details[key] != value):
                            continue

                    pointDist = (((t0.pos[0] - t1.pos[0])**2) + ((t0.pos[1] - t1.pos[1])**2))**0.5
                    if (pointDist <= rule["maxDist"]):
                        t0.edges[t1.id] = pointDist
                        t1.edges[t0.id] = pointDist

                    continue

    def toImage(self, mapScale = None, colorRules = None, filename = None):
        """
        Creates an image representing the map as a graph, with territories as vertices and edges as edges.

        Parameters:
            colorRules(dict): Dictionary where the keys are territories and values are the color they should be on the image, represented as an rgb tuple.
        """
        
        #Represents the extra space between min/max X/Y and the borders of the image.
        coordOffset = (75, 75)
        mapScale = mapScale or (1, 1)
        terrSize = (32, 32)

        #Represents the max render length of an edge.
        #If an edge is more than edgeDrawLimits[1], then shrink the map so it draws it as long as edgeDrawLimits[1] would before.
        #If an edge is less than edgeDrawLimits[0], then inflate the map so it draws it as long as edgeDrawLimits[0] would before.
        edgeDrawLimits = (1, 2)

        courierFont = ImageFont.truetype(f"{fontsDir}/courier.ttf", 24)

        #Initialize min and max X and Y values to the X and Y coords of the first territory in the dict of territories
        firstT = next(iter(self.territories))
        minX, maxX, minY, maxY = firstT.pos[0], firstT.pos[0], firstT.pos[1], firstT.pos[1]
        minEdge = float('inf')
        maxEdge = -1
        
        for t in self.territories:
            minX = min(minX, t.pos[0])
            maxX = max(maxX, t.pos[0])
            minY = min(minY, t.pos[1])
            maxY = max(maxY, t.pos[1])
            if t.edges:
                minEdge = min(minEdge, min(t.edges.values()))
                maxEdge = max(maxEdge, max(t.edges.values()))

        if maxEdge == -1: maxEdge = 1

        mapScale = (
            int(mapScale[0] * min(1, edgeDrawLimits[1] / max(1, maxEdge))),
            int(mapScale[1] * min(1, edgeDrawLimits[1] / max(1, maxEdge)))
        )

        dim = (maxX-minX, maxY-minY)
        #Where the territories are placed on the map relative to 0 is measured by coordinates minus offset
        terrOffset = (0 - minX + coordOffset[0], 0 - minY + coordOffset[0])

        out_img = Image.new("RGB", (
            int((dim[0] * mapScale[0]) + (coordOffset[0]*2)), 
            int((dim[1] * mapScale[1]) + (coordOffset[1]*2))
            ),
            (200, 200, 200)
        )
        imgDraw = ImageDraw.Draw(out_img)

        #Draw territories on the map
        for terr in self.territories:

            #Draw territory edges on the map
            for neighborID in terr.edges.keys():

                neighbor = self.territories[int(neighborID)]

                if neighbor.id > terr.id:

                    imgDraw.line(
                        [
                            ((terr.pos[0] * mapScale[0]) + terrOffset[0],
                            (terr.pos[1] * mapScale[1]) + terrOffset[1]),
                            ((neighbor.pos[0] * mapScale[0]) + terrOffset[0],
                            (neighbor.pos[1] * mapScale[1]) + terrOffset[1])
                        ],
                        fill = "black"
                    )

            #Check for custom color; if none, use default
            terrColor = (255,255,255)

            if colorRules:
                if terr.name in colorRules.keys():
                    terrColor = colorRules[terr.name]

            #Now draw the territory as a circle
            imgDraw.ellipse(
                (
                    (terr.pos[0] * mapScale[0]) + terrOffset[0] - (terrSize[0]/2),
                    (terr.pos[1] * mapScale[1]) + terrOffset[1] - (terrSize[0]/2),
                    (terr.pos[0] * mapScale[0]) + terrOffset[0] + (terrSize[0]/2),
                    (terr.pos[1] * mapScale[1]) + terrOffset[1] + (terrSize[0]/2)
                ), 
            fill = terrColor,
            outline = (0,0,0))

            #Draw the territory's ID number nearby
            imgDraw.text(
                (
                    (terr.pos[0] * mapScale[0]) + (terrSize[0]/2) + terrOffset[0],
                    (terr.pos[1] * mapScale[1]) - terrSize[1] + terrOffset[1]
                ),
                str(terr.id), font=courierFont, fill="black")

        if not (filename): filename = f"{worldsDir}/{self.name}.jpg"
        if not (filename.endswith(".jpg")): filename += ".jpg"
        out_img.save(filename)

        logInfo(f"Successfully saved world {self.name}!")

        return filename

    def __getitem__(self, items):
        """
        Called by: self[items]
        """

        if (type(items) == int):

            if ((items >= len(self.territories)) or (items < 0)): return False

            return self.territories[items]

        if (type(items) == str):

            if items.isdigit(): return self[int(items)]

            #Get the territory from self.territories which has a name equal to items
            return next(iter(terr for terr in self.territories if terr.name == items), False)

        return False