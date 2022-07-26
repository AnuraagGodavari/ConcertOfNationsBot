import json, os, inspect, pprint, copy

#General methods

def newGame(gameName, serverID, startMonth, startYear, map, gameDict): #Creates a new saveFile
    
    if (map in os.listdir("Maps")) and (gameDict in os.listdir("Dictionaries")): #If the map and gameDict file names lead to existing files
        
        saveGame = GameObjects.SaveGame(gameName, serverID, GameObjects.Date(startMonth, startYear), map, gameDict) #Creates a SaveGame object
        
        with open(f"Savegames/{gameName} - {serverID}.json", 'w') as f: #Saves the SaveGame to a new file
            json.dump(saveObject(saveGame), f, indent = 4)
            
        return saveGame

# getNation(608117738183065641, None, 608113391747465227)
def getNation(nationID, gamePassword, serverID = None):
    if serverID != None:
        saveGame = getSaveGame(serverID)
    else:
        saveGame = getSaveGame(gamePassword)
    nation = loadObject(saveGame["Nations"][str(nationID)])
    return nation

def getSaveGame(ID):
    ID = str(ID)
    for file in os.listdir("Savegames"):
        if (file[:-5].split(" - ")[-1] == ID): #if ID in file:
            with open(f"Savegames/{file}") as f:
                saveGame = json.load(f)
                return saveGame

#d = saveObject(getNation(608117738183065641, None, 608113391747465227))
def saveObject(originalThing): #recursively turns a custom object, with object parameters and subparameters, into a dictionary

    thing = copy.deepcopy(originalThing)
    
	#Define the dictionary we should return
    rtnDict = {}
	
	#If thing is a custom class, this should work
    try: rtnDict = toDict(thing)
		
    except:
		
        if isinstance(thing, dict):
            rtnDict = thing
			
        elif isinstance(thing, list):
            rtnList = []
            for item in thing:
                rtnList.append(saveObject[item])
            return rtnList
		
        else: #Primitive data type
            return thing
            
	#Save each value in the rtnDict recursively
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

#creates an object from a json or python dict
def loadObject(thing):
    
    if isinstance(thing, dict):
        for key in thing.keys():
            thing[key] = loadObject(thing[key])
        return toObject(thing)
    
    elif isinstance(thing, list):
        return list(map(lambda index: loadObject(index), thing))
        
    return thing

def toObject(thing): #Turns dict from json into object

    if (isinstance(thing, dict)):
        if ("__class__" in thing.keys()): #If dictionary and can be converted to non-dict object:
            
            class_name = thing.pop("__class__")
            module_name = thing.pop("__module__")
            
            #For importing modules from packages. Not a perfect way of doing this, but it's the best way I can think of doing it for now.
            if ('.' in module_name):
                module_name_list = module_name.split('.')
                module = __import__(module_name_list.pop(0))
                
                #Loop to go through the sub modules and keep importing.
                for subModule in module_name_list:
                    module = getattr(module, subModule)
                
            else:
                pprint.pprint(thing)
                module = __import__(module_name)
                 
            class_ = getattr(module,class_name)
            
            obj = class_(**thing) #generate object
            
            #if (("Territory" not in class_name) and (class_name != "Vertex")): 
                #print(class_name)
                #print(obj)
            
            return obj
        else:
            obj = thing
            return obj
        
    else: #if not a dictionary or is a dictionary but not convertable to non-dict object:
        obj = thing
        return obj

