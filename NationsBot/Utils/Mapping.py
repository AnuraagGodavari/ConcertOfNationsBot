import json, pprint, random
from PIL import Image, ImageDraw, ImageFont
from ConcertOfNations import Util, GameObjects, FileHandling, Mapping

#A point on a map.
class Vertex:
    def __init__(self, name, coords, edges, details):
        self.name = name
        self.coords = coords
        self.edges = edges
        self.details = details
        if "Coastal" not in self.details.keys():
            self.details["Coastal"] = False
        
    def distanceTo(self, target):
        return (self.coords[1] - target.coords[1]) ** 2 + (self.coords[0] - target.coords[0]) ** 2
    
    def __getitem__(self, index):
        return self.edges[index]
        
    def __setitem__(self, key, value):
        self.edges[key] = value
        
    def __delitem__(self, key):
        del self.edges[key]

#Holds many vertices, connects them all and conducts pathfinding.
class Map:
    def __init__(self, vertices = {}):
        self.vertices = vertices
    
    def traverse (self, origin, destination, *territoryTypes, availableVertices = None):
        
        if ((origin not in self.vertices.keys()) or (destination not in self.vertices.keys())): 
            return None
        
        if (territoryTypes):
            if (self[destination].details["type"] not in territoryTypes): return None
        
        #If the destination borders the origin, return a path with just these two.
        if (destination in self[origin].edges.keys()):
            path = Util.LinkedList(origin)
            path.add(destination)
            return path
        
        origin, destination = self[origin], self[destination]
        currentNode = origin #A Vertex object representing where we are in the graph
        
        openNodes = [origin] #Adds the starting node to an otherwise empty list of open nodes
        closedNodes = [] #Closed nodes, meaning nodes that will not be revisited
        
        gScores = {origin.name: 0} #gScore[n] = cost of the cheapest path from start to node n
        fScores = {origin.name: origin.distanceTo(destination)} #fScore[n] = gScore[n] plus heuristic (coordinate distance from n to destination) for node n
        cameFrom = {}
        
        while openNodes: #While openNodes is not empty
            
            #set currentNode to the node in openNodes with the lowest fScore
            lowestfScore = openNodes[0]
            for node in openNodes:
                if (fScores[node.name] < fScores[lowestfScore.name]): lowestfScore = node
                
            currentNode = lowestfScore
            
            #We reached the destination! Reconstruct the path.
            if currentNode.name == destination.name:
                
                currentNode = currentNode.name
                path = Util.LinkedList(currentNode)
                
                while currentNode in cameFrom.keys():
                    currentNode = cameFrom[currentNode]
                    path.add(currentNode)
                
                return path
            
            #Clears the current node from the open nodes list; closes it.
            openNodes.remove(currentNode)
            
            #Checks each neighbor of current, adds to open nodes if we've found
            for neighborName in currentNode.edges.keys():
                
                #If specific types of territories are required for the traversal, check if this neighbor is of one of those types
                if (territoryTypes):
                    if (self[neighborName].details["type"] not in territoryTypes): continue
                    
                if (availableVertices):
                    if (neighborName not in availableVertices): continue
                
                tempgScore = gScores[currentNode.name] + currentNode.edges[neighborName]
                if (neighborName not in gScores.keys()): gScores[neighborName] = tempgScore + 1
                
                if (tempgScore < gScores[neighborName]):
                    cameFrom[neighborName] = currentNode.name #The neighbor was preceded by current on the shortest known path.
                    gScores[neighborName] = tempgScore #Reset shortest known distance from start to g
                    fScores[neighborName] = tempgScore + self[neighborName].distanceTo(destination) #set fScore to gScore plus heuristic
                
                    if self[neighborName] not in openNodes: openNodes.append(self[neighborName])
        
        return None #failed

            
        ''' FROM WIKIPEDIA THE FREE ENCYCLOPEDIA
        // This operation can occur in O(1) time if openSet is a min-heap or a priority queue
            current := the node in openSet having the lowest fScore[] value
            if current = goal
                return reconstruct_path(cameFrom, current)

            openSet.Remove(current)
            for each neighbor of current
                // d(current,neighbor) is the weight of the edge from current to neighbor
                // tentative_gScore is the distance from start to the neighbor through current
                tentative_gScore := gScore[current] + d(current, neighbor)
                if tentative_gScore < gScore[neighbor]
                    // This path to neighbor is better than any previous one. Record it!
                    cameFrom[neighbor] := current
                    gScore[neighbor] := tentative_gScore
                    fScore[neighbor] := gScore[neighbor] + h(neighbor)
                    if neighbor not in openSet
                        openSet.add(neighbor)

        // Open set is empty but goal was never reached
        return failure
        '''
                
    def calculateEdges(self, regularThreshold, seaThreshold, terrainDict): #Automatically connects the vertices in the map
    
        for greaterVertex in self.vertices.keys(): #Greater key cycles through the dict
            for lesserVertex in self.vertices.keys(): #Lesser key is used to analyze each vertex in the dict to see if they can connect to the greater key
                
                #If the vertices are not the same and are not already connected
                if not(greaterVertex == lesserVertex) and not (greaterVertex in self[lesserVertex].edges.keys()) and not (lesserVertex in self[greaterVertex].edges.keys()):
                    
                    dist = self[greaterVertex].distanceTo(self[lesserVertex]) #Calculates distance
                    
                    threshold = regularThreshold #Initializes threshold, which is compared to the distance
                    
                    if "SeaTerritory" in (self[greaterVertex].details["type"], self[lesserVertex].details["type"]):
                        threshold = seaThreshold #Threshold changes if at least one of the vertices are maritime
                        
                        for vert in (greaterVertex, lesserVertex):
                            if self[vert].details["type"] != "SeaTerritory":
                                self[vert].details["Coastal"] = True
                    
                    if dist <= threshold: #If distance is <= the threshold, then the two points can connect
                        
                        terrainModifier = max(terrainDict[self[greaterVertex].details["terrain"]], terrainDict[self[lesserVertex].details["terrain"]]) #Multiplier for terrain difficulty
                        
                        self[greaterVertex][lesserVertex] = (dist**0.5)*terrainModifier #Edge size = Effective movement cost
                        self[lesserVertex][greaterVertex] = (dist**0.5)*terrainModifier
    
    def toImage(self, filename = None, colorData = None, visibleVertices = None):
    
        xMin = xMax = yMin = yMax = 0
        
        maxNameLen = 0
        fontSize = 32
        
        closestVertDistX = False
        
        #Get min and max x and y coordinates of all the vertices
        #Get the longest name and use that to calculate the map size multiplier as well
        for vertex in self.vertices.values():
            
            if vertex.coords[0] < xMin: xMin = vertex.coords[0]
            elif vertex.coords[0] > xMax: xMax = vertex.coords[0]
            
            if vertex.coords[1] < yMin: yMin = vertex.coords[1]
            elif vertex.coords[1] > yMax: yMax = vertex.coords[1]
            
            if (len(vertex.name) > maxNameLen): maxNameLen = len(vertex.name)
        
        xSize = (xMax - xMin) * 12
        ySize = (yMax- yMin) * 12
        
        map = Image.new("RGBA", (xSize, ySize), (210, 210, 210))
        mapDraw = ImageDraw.Draw(map)
        scale = min(xMax - xMin, yMax - yMin)
        
        #Draw lines for all the edges in the map
        for vertex in self.vertices.values():
        
            for edgeName in vertex.edges.keys():
            
                if (visibleVertices):
                    if not((edgeName in visibleVertices) and (vertex.name in visibleVertices)): 
                        continue
            
                edge = self[edgeName]
                mapDraw.line(
                    [((xMin + vertex.coords[0])*12, #x0
                    (yMin + vertex.coords[1])*12), #y0
                    ((xMin + edge.coords[0])*12,  #x1
                    (yMin + edge.coords[1])*12)], #y1
                    fill = "grey", width = int(scale/100)
                )
        
        radius = int(scale/15)
        
        #Draw the territories and their labels on top
        for vertex in self.vertices.values():
            
            if (visibleVertices):
                if (vertex.name not in visibleVertices): 
                    continue
            
            xCoord = (xMin + vertex.coords[0])*12
            yCoord = (yMin + vertex.coords[1])*12
            
            color = None
            
            #If there is a dictionary of nation territories
            if(colorData):
                for nation in colorData.values():
                    if (vertex.name in nation["Territories"]):
                        color = tuple(nation["Color"])
            
            #if unowned
            if not(color): color = "white"
            
            if (vertex.details["type"] == "LandTerritory"): outlineColor = "black"
            elif (vertex.details["type"] == "SeaTerritory"): outlineColor = "blue"
            
            mapDraw.ellipse((xCoord - radius, yCoord - radius, xCoord + radius, yCoord + radius), fill = color, outline = outlineColor)
            
            courierNew = ImageFont.truetype("Resources/courier.ttf", min(int(scale/10), fontSize))
            mapDraw.text((xCoord, yCoord-(radius*1.5)), vertex.name, fill='black', font=courierNew)
            
        #mapDraw.ellipse((0, 0, 100, 100), outline = "black")
        
        width, height = map.size
        minSize = 2000
        
        if ((width < minSize) and (height < minSize)):
            smaller = min(map.size)
            factor = minSize/smaller
            
            map = map.resize((int(width*factor), int(height*factor)))
        
        elif (width < minSize):
            factor = minSize/width
            
            map = map.resize((int(width*factor), int(height*factor)))
        
        elif (height < minSize):
            factor = minSize/map.height
            
            map = map.resize((int(width*factor), int(height*factor)))
        
        if not(filename): return map
        
        map.save(f"Maps/{filename}.png")
    
    def traversalToImage(self, origin, destination, *territoryTypes, knownTerrs = None):
        xMin = xMax = yMin = yMax = 0

        for vertex in self.vertices.values():
            
            if vertex.coords[0] < xMin: xMin = vertex.coords[0]
            elif vertex.coords[0] > xMax: xMax = vertex.coords[0]
            
            if vertex.coords[1] < yMin: yMin = vertex.coords[1]
            elif vertex.coords[1] > yMax: yMax = vertex.coords[1]

        map = Image.new("RGBA", ((xMax - xMin)*12, (yMax- yMin)*12), (210, 210, 210))
        mapDraw = ImageDraw.Draw(map)
        scale = min(xMax - xMin, yMax - yMin)
        
        #XXX
        path = self.traverse(origin, destination, *territoryTypes)
        if (path == None): return
        
        currentLink = path.start
        
        while (currentLink != None):
            vertex = self[currentLink.value]
            if currentLink.next != None:
                edge = self[currentLink.next.value]
                mapDraw.line([((xMin + vertex.coords[0])*12, (yMin + vertex.coords[1])*12), ((xMin + edge.coords[0])*12, (yMin + edge.coords[1])*12)], fill = "green", width = int(scale/100))
                
                radius = int(scale/15)
                xCoord = (xMin + vertex.coords[0])*12
                yCoord = (yMin + vertex.coords[1])*12
                mapDraw.ellipse((xCoord - radius, yCoord - radius, xCoord + radius, yCoord + radius), fill = "green")
                
                xCoord = (xMin + edge.coords[0])*12
                yCoord = (yMin + edge.coords[1])*12
                mapDraw.ellipse((xCoord - radius, yCoord - radius, xCoord + radius, yCoord + radius), fill = "green")
            currentLink = currentLink.next

        map.save(f"Maps/{origin} to {destination} Traversal.png")
            
    def __getitem__ (self, index):
        return self.vertices[index]
        
    def __setitem__ (self, key, value):
        self.vertices[key] = value

# A type of map that represents a galaxy, including systems and rogue and extra-systemic celestial objects.
class Galaxy(Map):
    def __init__(self, vertices = {}):
        Map.__init__(self, vertices)
        
    def calculateEdges(self, regularThreshold, seaThreshold, terrainDict):
        Map.calculateEdges(self, regularThreshold, seaThreshold, terrainDict) #Parent object's calculateEdges
        
        for vertex in self.vertices.keys():
            system = self[vertex].details["System"] #The star system of the vertex
            edgesToDel = []
            
            for edge in self[vertex].edges.keys(): #Checks all of this vertex's edges
                if self[edge].details["System"] != system and system != None and not(self[vertex].details["terrain"] == self[edge].details["terrain"] == "Star"): #If the two are part of different systems and are not both stars
                    edgesToDel.append(edge)
            
            for edge in edgesToDel:
                del self[vertex][edge] #Delete their mutual edges
                del self[edge][vertex]

#A type of map that represents a spherical planet
class Planet(Map):
    pass

#Testing functions

def makeMap(path, testMap, seaThreshold, regularThreshold, terrainDict): #Test path: "Open Skies Milky Way Map.json"
    with open(f"Maps/{path}") as f:
        regionMap = json.load(f)["Territories"]

    for region in regionMap.keys(): #Gathers all nodes into map
        for territory in regionMap[region].keys():
            testMap.vertices[territory] = (Vertex(territory, regionMap[region][territory].pop("Coordinates"), dict(), regionMap[region][territory]))
            
    testMap.calculateEdges(seaThreshold, regularThreshold, terrainDict)
    return testMap
    
#Test: 
def testOpenSkies(): 
    terrainDict = {"Star": 1, "Venusian": 1, "Tropical": 1, "Cold": 1, "Martian": 1, "Gaseous": 1, "Grassland": 1, "Temperate": 1, "Alpine": 1, "Hilly": 1, "Uralic": 1}
    testMap = makeMap("Open Skies Milky Way Points.json", Galaxy(), -1, 100000, terrainDict)
    
    with open("Maps/Open Skies Milky Way Map.json", 'w') as f: #Saves the SaveGame to a new file
        json.dump(FileHandling.saveObject(testMap), f, indent = 4)
        
def testTestGamex10():

    testMap = Map()
    
    for i in range(100):
        testMap.vertices[f"Test {i+1}"] = Vertex(f"Test {i+1}", [random.randint(1, 1000), random.randint(1, 1000)], dict(), {"type": "LandTerritory", "terrain": "Flat", "resources": {"Iron": random.randint(1,4)}, "Coastal": False})
        
    terrainDict = {"Flat": 1}
    testMap.calculateEdges(20000, 12500, terrainDict)
    
    testMap.toImage("Test")
    
    testMap.traversalToImage("Test 1", "Test 9")
    #print(testMap.traverse("Test 1", "Test 9"))
    
    with open("Maps/Test Map.json", 'w') as f: #Saves the SaveGame to a new file
        json.dump(FileHandling.saveObject(testMap), f, indent = 4)
        
def testTestGame():

    testMap = Map()
    
    for i in range(10):
        testMap.vertices[f"Test {i+1}"] = Vertex(f"Test {i+1}", [random.randint(1, 100), random.randint(1, 100)], dict(), {"type": "LandTerritory", "terrain": "Flat", "resources": {"Iron": random.randint(1,4)}, "Coastal": True})
        
    terrainDict = {"Flat": 1}
    testMap.calculateEdges(2000, 1250, terrainDict)
    
    testMap.toImage("Test")
    
    testMap.traversalToImage("Test 1", "Test 9")
    #print(testMap.traverse("Test 1", "Test 9"))
    
    with open("Maps/Test Map.json", 'w') as f: #Saves the SaveGame to a new file
        json.dump(FileHandling.saveObject(testMap), f, indent = 4)

def testTestGame_Sea():

    testMap = Map()
    
    for i in range(50):
        testMap.vertices[f"Test {i+1}"] = Vertex(f"Test {i+1}", [random.randint(1, 1000), random.randint(1, 1000)], dict(), {"type": "LandTerritory", "terrain": "Flat", "resources": {"Iron": random.randint(1,4)}, "Coastal": True})
        
    for i in range(50):
        testMap.vertices[f"Test Sea {i+1}"] = Vertex(f"Test Sea {i+1}", [random.randint(1, 1000), random.randint(1, 1000)], dict(), {"type": "SeaTerritory", "terrain": "Temperate Ocean", "resources": {}, "Coastal": True})
        
    terrainDict = {"Flat": 1, "Temperate Ocean": 1}
    testMap.calculateEdges(20000, 12500, terrainDict)
    
    testMap.toImage("Test")
    
    testMap.traversalToImage("Test 1", "Test 9")
    #print(testMap.traverse("Test 1", "Test 9"))
    
    with open("Maps/Test Map.json", 'w') as f: #Saves the SaveGame to a new file
        json.dump(FileHandling.saveObject(testMap), f, indent = 4)

def mapFromImage(imageName):
    image = Image.open(imageName)
    imgMap = Map()
    
    width, height = image.size
    
    #Go through each pixel in the image
    for x in range(width):
        for y in range(height):
            pixelColor = image.getpixel((x, y))
            
            #colorDict = {"Land": (255, 255, 255), "Sea": (0, 162, 232)}
            #for color in colorDict.keys():
            
            #It's a land territory
            if (pixelColor == (255, 255, 255, 255)):
                imgMap[f"Territory ({x},{y})"] = Vertex(f"Territory ({x},{y})", [x, y], dict(), {"type": "LandTerritory", "terrain": "Flat", "resources": {"Iron": random.randint(1,4)}, "Coastal": False})
               
            #It's a coastal land territory
            elif (pixelColor == (153, 217, 234, 255)):
                imgMap[f"Territory ({x},{y})"] = Vertex(f"Territory ({x},{y})", [x, y], dict(), {"type": "LandTerritory", "terrain": "Flat", "resources": {"Iron": random.randint(1,4)}, "Coastal": False})
                
            elif (pixelColor == (0, 162, 232, 255)):
                imgMap[f"Territory ({x},{y})"] = Vertex(f"Territory ({x},{y})", [x, y], dict(), {"type": "SeaTerritory", "terrain": "Temperate Ocean", "resources": {}, "Coastal": True})
                
            elif (pixelColor == (34, 177, 76, 255)):
                imgMap[f"Colonizable Territory ({x},{y})"] = Vertex(f"Colonizable Territory ({x},{y})", [x, y], dict(), {"type": "LandTerritory", "terrain": "Flat", "resources": {"Iron": random.randint(1,4)}, "Coastal": False})
            
            elif (pixelColor == (237, 28, 36, 255)):
                imgMap[f"TestB Territory ({x},{y})"] = Vertex(f"TestB Territory ({x},{y})", [x, y], dict(), {"type": "LandTerritory", "terrain": "Flat", "resources": {"Iron": random.randint(1,4)}, "Coastal": False})
                
    terrainDict = {"Flat": 1, "Temperate Ocean": 1}
    imgMap.calculateEdges(300, 1000, terrainDict)
    
    #imgMap.toImage("mapFromImage")
    
    #imgMap.traversalToImage("Territory (40,48)", "Territory (39,36)")
    
    with open("Maps/mapFromImage.json", 'w') as f: #Saves the SaveGame to a new file
        mapDict = FileHandling.saveObject(imgMap)
        json.dump(mapDict, f, indent = 4)

'''testMap = Map()

for i in range(10):
    testMap.vertices[f"Test {i}"] = Vertex(f"Test {i}", [random.randint(1,101), random.randint(1,101)], {})
    
testMap.calc(200, 5000, {})

#for vertex in testMap.vertices.keys():
#    pprint.pprint(testMap.vertices[vertex].edges)'''

#Bottom






























#Bottom 2 electric boogaloo