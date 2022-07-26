#Useful Classes

class Link:
    def __init__(self, value, next = None):
        self.value = value
        self.next = next
        
    def search(self, linkValue):
        if (next == None): return None
        elif (next.value == linkValue): return next
        else: return next.search(linkValue)
    
    def __str__(self):
        rtnString = str(self.value)
        if (self.next): rtnString += ">>" + str(self.next)
        return rtnString
    
    def passDown(self, newValue):
        if self.next == None: self.next = Link(newValue)
        else:self.next.passDown(newValue)

class LinkedList:
    def __init__(self, start = None):
        if start.__class__.__name__ != "Link":
            self.start = Link(start)
        else: self.start = start
        
    def add(self, newValue, previousValue = None):
        if previousValue == None: self.start = Link(newValue, self.start)
        
        elif (start.search(previousValue)): 
            pos = start.search(previousValue)
            pos.next = Link(newValue, pos.next)
            
    def append(self, newValue):
        self.start.passDown(newValue)
            
    def __str__(self):
        return str(self.start)

class StackPlate:
    def __init__(self, value, below = None):
        self.value = value
        self.below = below
        
class Stack:
    def __init__(self, top = None):
        if ((top.__class__ == StackPlate) or (top == None)):
            self.top = top
        else: self.top = StackPlate(top)
        
    def push(self, newPlate):
        if (newPlate.__class__ != StackPlate):
            newPlate = StackPlate(newPlate)
        newPlate.below = self.top
        self.top = newPlate
        
    def pop(self):
        popped = self.top.value
        self.top = self.top.below
        return popped

class TwoWayDict:
    def __init__(self, colA, colB):
        if len(colA) == len(colB):
            self.colA = colA
            self.colB = colB
    
    def __len__(self):
        return len(self.colA)
    
    def __getitem__(self, key):
        for index in range(len(self)):
            if self.colA[index] == key:
                return self.colB[index]
            elif self.colB[index] == key:
                return self.colA[index]
                
    def __str__ (self):
        rtn = ""
        for index in range(len(self)):
            rtn += str(self.colA[index])
            rtn += " : "
            rtn += str(self.colA[index])
            rtn += ", "
        return rtn

#A set of relations between an object that shares this name and other objects. Think of it as a vertex with edges.
class RelationSet:
    def __init__(self, name, relations = None):
        self.name = name
        self.relations = relations or {}
    
    #Set the entire set of relations between self and the target
    def relate(self, target, relation = None):
        if (relation): self[target] = [relation] 
        else: self[target] = []
    
    #Add a new relation to the list of relations between self and the target
    def addRelation(self, target, relation):
        if (target not in self.relations.keys()): self[target] = [relation]
        
        else: self[target].append(relation)
    
    #Get self's relation to the key
    def __getitem__(self, key):
        return self.relations[key]
    
    #Set self's relation to the key
    def __setitem__(self, key, value):
        self.relations[key] = value

#A set of relations between objects. Think of it as a map with vertices.
class RelationalMatrix:
    def __init__ (self, relations = None, keys = None):
        self.relations = relations or {}
        
        if (keys and not self.relations): self.relations = {key: RelationSet(key) for key in keys}
    
    #Add a relation to the relationSet objects for all of the listed keys.
    def relate(self, relation, *keys):
        for highKey in keys:
            #If this key does not already exist in self.relations, add it here
            if (highKey not in self.relations): self.addRelation(highKey)
            
            for lowKey in keys:
                if (highKey != lowKey): self.relations[highKey].addRelation(lowKey, relation)
    
    #Makes an empty RelationSet for a new index (e.g. if newIndex is 'A', add 'A' to self.relations with a value of an empty RelationSet)
    def addRelation(self, newIndex):
        self.relations[newIndex] = RelationSet(newIndex)
    
    #Remove a specific relation from each of the keys to each other
    def removeRelation(self, relation, *keys):
        for highKey in keys:
            for lowKey in keys:
                if (highKey != lowKey): 
                    self.relations[highKey][lowKey] = relation
   
    #Removes all relations between all the keys
    def clearRelations(self, *keys):
        for highKey in keys:
            for lowKey in keys:
                if (highKey != lowKey): 
                    #Pops only the lowKey key in the highKey relationSet
                    self.relations[highKey].relations.remove(lowKey)
    
    def __getitem__(self, key):
        return self.relations[key]

#A list of lists that are centered around an axis that is the middle of all the lists. This is CenteredTierList[0].
class CenteredTierList:
    def __init__(self, maxWidth = 0):
        self.maxWidth = maxWidth
        self.tiers = []
        self.depth = 0
    
    #Adds a new tier to the tier list, after splitting it up into smaller lists if necessary.
    def addTier(self, newTier, index = "null", offset = 0):
        
        #if newTier is an empty list
        if not(newTier): return 0
        
        if (index == "null"):
            index = self.depth
        
        #left is a list of all objects from the left of the list, removed to make it small enough to fit in this tier list
        left = []
        #right is a list of all objects from the right of the list, removed to make it small enough to fit in this tier list
        right = []
        #startAgain = True means add to left, if = False it means add to right.
        startAgain = True
        
        threshold = self.maxWidth or len(newTier)+1
        
        #While the newTier is still too big for the list
        while(len(newTier) > threshold):
            if (startAgain):
                left.append(newTier[0 + offset])
                startAgain = False
                newTier = newTier[1:]
                
            else:
                right.append(newTier[-1 - offset])
                startAgain = True
                newTier = newTier[0:-1 - offset]
            
            if (len(left) + len(right) >= threshold):
                right.reverse()
                self.insertTier(left + right, index)
                left = []
                right = []
        
        if(bool(left) or bool(right)):
            right.reverse()
            self.insertTier(left + right, index)
                
        self.insertTier(newTier, index)
    
    #Puts a new tier in the specified position.
    def insertTier(self, newTier, index):
        base = self.tiers[0:index]
        shifted = self.tiers[index:]
        self.tiers = base + [newTier] + shifted

        self.depth += 1
    
    #Removes the tier at the given index
    def remove(self, index):
        if (index == len(self.tiers - 1)):
            self.tiers = self.tiers[:-1]
        else:
            self.tiers = self.tiers[:index] + self.tiers[index+1:]
        self.depth -= 1
    
    #Removes None from the ends of each tier
    def trim(self):
        for tierNum in range(len(self.tiers)):
            #Removes Nones
            self.tiers[tierNum] = list(filter(None, self.tiers[tierNum]))
        #Removes tiers filled with None from entire list
        self.tiers = list(filter(None, self.tiers))
    
    #Get a sightline. This means a list of each object at [key] position relative to the center.
    def __getitem__ (self, key):
        line = []
        
        for tier in self.tiers:
            #int(len(tier)/2) is the center
            newKey = int(len(tier)/2) + key
            if ((newKey >= len(tier)) or (newKey < 0)):
                line.append(None)
            else:
                line.append(tier[newKey])
        return line
    
    def __str__(self):
        rtn = ""
        for tier in self.tiers:
            for thing in tier:
                rtn += str(thing) + ", "
            rtn += '\n'
        return rtn

#A binary tree where each node has a description. 
class BinDescTree:
    def __init__(self, val = None, description = None, left = None, right = None):
        self.val = val
        self.description = description
        self.left = left
        self.right = right
    
    #Put in a new node.
    def insert(self, v, desc):
        
        #If this tree is empty, add the new node info to this node.
        if not(self.val):
            self.v = v
            self.description = desc
        
        #If the v is lesser than this node's val, move it to the left
        elif (v < self.val):
            if (self.left == None):
                self.left = BinDescTree(v, desc)
                
            else:
                self.left.insert(v, desc)
                
        #If the v is greater than this node's val, move it to the right
        elif(v > self.val):
            if (self.right == None):
                self.right = BinDescTree(v, desc)
                
            else:
                self.right.insert(v, desc)   
        
        #If the v is equal to this node's val, make it this node's left. Make the former left the new node's left.
        else:
            self.left = BinDescTree(v, desc, self.left)
            
    def inorder(self):
        rtn = []
        
        if (self.left): rtn += self.left.inorder()
        
        rtn.append(self.description)
        
        if (self.right): rtn += self.right.inorder()
        
        return list(filter(None, rtn)) 

#Useful Methods

def bound(lowerBound, val, upperBound):
    return max(lowerBound, min(upperBound, val))

def sortForwards(list):
	for i in range(len(list)):
		minimum = i
		
		for j in range(i + 1, len(list)):
			if list[j] < list[minimum]:
				minimum = j
				
		list[minimum], list[i] = list[i], list[minimum]
	
	return list
    
def sortBackwards(list):
    list = sortForwards(list)
    newList = []
    
    for i in range(len(list)):
        newList.append(list[(i + 1)*-1])
        
    return newList
    
def compareLists(list1, list2):
    rtnList = []
    if len(list1) >= len(list2):
        rtnList = [list1, list2]
    else:
        rtnList = [list2, list1]
    return rtnList
    
def isSufficient(num1, num2 = 1, threshold = 1):
    if num1 > threshold:
        return num1
    else:
        return num2

#Divides a list into equal sets.
def pageify(set, pageSize):
    multiplier = 1
    pagedSet = []
    setLen = len(set)
    
    while(True):
        
        pagedSet += [set[pageSize * (multiplier - 1) : min(pageSize * multiplier, setLen)]]
        
        if (pageSize * multiplier >= setLen): 
            break
        
        multiplier += 1
    
    return pagedSet

def isWithin(num1, num2 = 1, threshold = 1):
    if num1 < threshold:
        return num1
    else:
        return num2

def combineDicts(*args):
    rtnDict = {}
    for arg in args:
        if arg != None: #For each dictionary in the arguments if it is not equal to None,
            for key in arg.keys():
                if key in rtnDict.keys():
                    if isinstance(rtnDict[key], dict):
                        rtnDict[key] = combineDicts(rtnDict[key], arg[key])
                    else:
                        try: rtnDict[key] += arg[key]
                        except: pass
                else:
                    rtnDict[key] = arg[key]
    return rtnDict

#creates an object from a json or python dict
def loadObject(thing):
    
    if isinstance(thing, dict):
        for key in thing.keys():
            thing[key] = loadObject(thing[key])
        return toObject(thing)
    
    elif isinstance(thing, list):
        return list(map(lambda index: loadObject(index), thing))
        
    return thing

#d = saveObject(getNation(608117738183065641, None, 608113391747465227))
def saveObject(thing): #recursively turns a custom object, with object parameters and subparameters, into a dictionary
#used to be: def saveObject(thing, keys = None): 
    rtnDict = {}
    try:
        rtnDict = toDict(thing)
    except:
        if isinstance(thing, dict):
            rtnDict = thing
        elif isinstance(thing, list):
            rtnList = []
            for item in thing:
                rtnList.append(saveObject[item])
            return rtnList
        else:
            return thing
            
    for param in rtnDict.keys(): #For each thing in this new dictionary:
        if isinstance(rtnDict[param], list): #If thing is a list
            temp, rtnDict[param] = rtnDict[param], [] #Makes the list empty and refills it with built-in data types.
            for item in temp:
                rtnDict[param].append(saveObject(item))
        elif isinstance(rtnDict[param], dict): #If thing is a dict
            rtnDict[param] = saveObject(rtnDict[param])
        else:
            try: rtnDict[param] = saveObject(rtnDict[param]) #Tries to saveObject the thing, assuming it is a custom object
            except: pass
    
    return rtnDict

def toDict(thing): #Turns object into dict for json
  
  rtnDict = { #metadata for the dictionary
    "__class__": thing.__class__.__name__,
   "__module__": thing.__module__
  }
  
  rtnDict.update(thing.__dict__) #converts object parameters to a dict, combines with current dict
  
  return rtnDict

def toObject(thing): #Turns dict from json into object

    if (isinstance(thing, dict)):
        if ("__class__" in thing.keys()): #If dictionary and can be converted to non-dict object:
            class_name = thing.pop("__class__")
            module_name = thing.pop("__module__")
            module = __import__(module_name)
            class_ = getattr(module,class_name)
            
            obj = class_(**thing) #generate object
            return obj
        else:
            obj = thing
            return obj
        
    else: #if not a dictionary or is a dictionary but not convertable to non-dict object:
        obj = thing
        return obj

def getFlanks(inList, *checkFor):
    leftBound = 0
    continueLeft = True
    
    rightBound = 0
    continueRight = True
    
    for i in range(len(inList)):
        leftNum = i
        rightNum = len(inList) - 1 - i
        if (((inList[leftNum] in checkFor) or (inList[leftNum].__class__.__name__ in checkFor))& continueLeft):
            leftBound += 1
            
        else:
            continueLeft = False
            
        if (((inList[rightNum] in checkFor) or (inList[rightNum].__class__.__name__ in checkFor)) & continueRight):
            rightBound += 1
            
        else:
            continueRight = False
        
        #End condition: Once they reach the center or both flanks are bounded fully
        if ((rightNum - leftNum < 2) or not(continueRight or continueLeft)):
            rightBound = len(inList) - rightBound
            if (rightBound == 0): rightBound = len(inList)
            
            return (leftBound, rightBound)


#Bottom



















#Bottom 2 Electric Boogaloo