import json, pprint, random
from PIL import Image, ImageDraw, ImageFont
from math import *
import operator

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
        
        if (edges):
            self.edges = {int(k): v for k, v in edges.items()}
        else: self.edges = dict()

        self.details = details or dict()
        self.resources = resources or dict()

    def dist(t0, t1):
        return (((t0.pos[0] - t1.pos[0])**2) + ((t0.pos[1] - t1.pos[1])**2))**0.5


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

                    pointDist = t0.dist(t1)
                    if (pointDist <= rule["maxDist"]):
                        t0.edges[t1.id] = round(pointDist, 2)
                        t1.edges[t0.id] = round(pointDist, 2)

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
        background_color = (200, 200, 200)

        #Represents the max render length of an edge.
        #If an edge is more than edgeDrawLimits[1], then shrink the map so it draws it as long as edgeDrawLimits[1] would before.
        #If an edge is less than edgeDrawLimits[0], then inflate the map so it draws it as long as edgeDrawLimits[0] would before.
        edgeDrawLimits = (1, 2)

        fontsize = 24
        courierFont = ImageFont.truetype(f"{fontsDir}/courier.ttf", fontsize)

        edge_fontsize = 18
        edge_courierFont = ImageFont.truetype(f"{fontsDir}/courier.ttf", edge_fontsize)

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
            background_color
        )
        imgDraw = ImageDraw.Draw(out_img)

        #Draw territories on the map
        for terr in self.territories:

            #Draw territory edges and distances on the map
            for neighborID in terr.edges.keys():

                neighbor = self.territories[int(neighborID)]

                if neighbor.id > terr.id:

                    edge_coords = ( 
                            ( 
                                (terr.pos[0] * mapScale[0]) + terrOffset[0],
                                (terr.pos[1] * mapScale[1]) + terrOffset[1]
                            ),
                            (
                                (neighbor.pos[0] * mapScale[0]) + terrOffset[0],
                                (neighbor.pos[1] * mapScale[1]) + terrOffset[1]
                            )
                        )

                    imgDraw.line(
                        [
                            (edge_coords[0][0], edge_coords[0][1]),
                            (edge_coords[1][0], edge_coords[1][1])
                        ],
                        fill = (50, 50, 50)
                    )

                    midpoint = (
                        min(edge_coords[0][0], edge_coords[1][0]) + (abs(edge_coords[0][0] - edge_coords[1][0])/2),
                        min(edge_coords[0][1], edge_coords[1][1]) + (abs(edge_coords[0][1] - edge_coords[1][1])/2)
                    )

                    gapsize = (
                        edge_fontsize*len(str(terr.edges[neighborID])),
                        edge_fontsize
                    )

                    #Display the edge length
                    imgDraw.rectangle(
                        (
                            midpoint[0] - gapsize[0]/2,
                            midpoint[1] - gapsize[1]/2,
                            midpoint[0] + gapsize[0]/2,
                            midpoint[1] + gapsize[1]/2
                        ), 
                        fill = background_color,
                        outline = (50, 50, 50)
                        )

                    imgDraw.text(
                        (
                            midpoint[0] - (gapsize[0]/2) + (edge_fontsize/1.25),
                            midpoint[1] - (gapsize[1]/2)
                        ),
                        str(terr.edges[neighborID]), font=edge_courierFont, fill=(50, 50, 50))

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

    def constructPath(self, prevTerrs, current, min_dist = float('inf')):
        
        if (current in prevTerrs.keys()):

            curr_effective_distance = self[current].edges[prevTerrs[current]]
            curr_distance = min(curr_effective_distance, min_dist)

            prev_path = self.constructPath(prevTerrs, prevTerrs[current])
            
            if not(prev_path):
                prev_distance = 0
            else:
                prev_distance = prev_path[-1]["This Distance"]
                prev_path[-1]["Next Distance"] += curr_distance

            return prev_path + [{
                "ID": current, 
                "Name": self[current].name, 
                "Distance": curr_effective_distance, 
                "This Distance": prev_distance + curr_distance, 
                "Next Distance": prev_distance + curr_distance
                }]

        return []

    def path_to(self, start, target, min_dist = float('inf')):
        """ Use the A* Algorithm to find the shortest path between two territories """

        logInfo(f"Creating a path between territories {start} and {target}")

        start = self[start].id
        target = self[target].id
        
        openTerrs = dict()
        prevTerrs = dict()

        #pathCosts[t] = cost to get to t
        pathCosts = { terr.id: float("inf") for terr in self.territories}
        pathCosts[start] = 0

        #fScore[t] = estimated cost (raw distance) to get to target from t
        fScore = { terr.id: float("inf") for terr in self.territories }
        fScore[start] = self[start].dist(self[target])
        openTerrs[start] = fScore[start]

        while (openTerrs):

            #Node with lowest fScore
            current = min(openTerrs.items(), key = operator.itemgetter(1))[0]

            if (current == target):
                path = self.constructPath(prevTerrs, current, min_dist)
                logInfo(f"Created path from {start} to {target}")
                return path
                
            openTerrs.pop(current)

            for neighbor, edge in self[current].edges.items():
                
                predicted_cost = pathCosts[current] + edge

                #If predicted cost is less than current minimum known cost
                if (predicted_cost < pathCosts[neighbor]):
                    
                    prevTerrs[neighbor] = current
                    pathCosts[neighbor] = predicted_cost
                    fScore[neighbor] = predicted_cost + self[neighbor].dist(self[target])

                    if neighbor not in openTerrs:
                        openTerrs[neighbor] = fScore[neighbor]

        logInfo("Path could not be created")
        return False


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