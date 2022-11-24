import json
from functools import lru_cache

from logger import *

from database import *
from common import *
from Utils import FileHandling

from ConcertOfNationsEngine.GameObjects import *
from ConcertOfNationsEngine.CustomExceptions import *

#Deal with worlds

def save_world(world):
    with open(f"{worldsDir}/Test World.json", 'w') as f:
        json.dump(FileHandling.saveObject(world), f, indent = 4)

    logInfo(f"Successfully saved world {world.name}")

@lru_cache(maxsize=16)
def load_world(world_name):
    """
    Load a world from a .json file representing a map without nations, buildings etc; only terrain, resources etc.
    """
    world = FileHandling.easyLoad(world_name, worldsDir)
    logInfo(f"World {world.name} successfully loaded")
    return world

def dbget_world_byName(world_name):
        """
        Get the row in the database table Worlds with this name
        """

        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT * FROM Worlds WHERE name=%s LIMIT 1;"
        params = [world_name]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False
        logInfo(f"Retrieved world {world_name} from database")
        return result

def setupNew_world(world):
    """
    Given a new world object, create a file for it and save it to the database.
    """
    logInfo("Setting up a new world in worldfiles and database")
    
    if (dbget_world_byName(world.name)):
        raise InputError(f"World with name {world.name} already exists")

    #Update database
    try:
        db = getdb()
        cursor = db.cursor()

        stmt = "INSERT INTO Worlds (name) VALUES (%s)"
        params = [world.name]
        cursor.execute(stmt, params)
        db.commit()
    except Exception as e:
        logError(e)
        raise LogicError(f"World could not be inserted!")

    logInfo("Successfully inserted world into database")

    #Generate world file
    save_world(world)


def insert_worldMap(world, savegame, filename, link, nation = None):
    """
    Inserting a worldImage into the database based on savegame, nation, turn number, etc. and containing a filename and imgur link
    """
    logInfo("Saving information for a world image")
    
    if (dbget_worldMap(world, savegame, savegame.turn, nation)):
        logInfo(f"World Map already exists for world {world.name}, savegame {savegame.name} turn {savegame.turn} and nation {nation or 'n/a'}")
        return

    savegameInfo = dbget_saveGame_byServer(savegame.server_id)
    if not (savegameInfo):
        raise InputError(f"Savegame {savegame.name} does not exist in the database")

    worldInfo = dbget_world_byName(world.name)
    if not (worldInfo):
        raise InputError(f"World {world.name} does not exist in the database")

    if (nation):
        roleInfo = get_Role(nation.role_id)
        if not (roleInfo):
            raise InputError(f"Nation {nation.name} does not exist in the database as a role")

     #Update database
    try:
        db = getdb()
        cursor = db.cursor()

        if (nation):
            stmt = "INSERT INTO WorldMaps (world_id, savegame_id, turn_no, role_id, filename, link) VALUES (%s, %s, %s, %s, %s, %s)"
            params = [worldInfo['id'], savegameInfo['id'], savegame.turn, roleInfo['id'], filename, link]

        else:
            stmt = "INSERT INTO WorldMaps (world_id, savegame_id, turn_no, filename, link) VALUES (%s, %s, %s, %s, %s)"
            params = [worldInfo['id'], savegameInfo['id'], savegame.turn, filename, link]

        cursor.execute(stmt, params)
        db.commit()
    except Exception as e:
        logError(e)
        raise LogicError(f"World could not be inserted!")

def dbget_worldMap(world, savegame, turn, nation = None):
    """
    Get the row in the database table WorldMaps pertaining to the information provided
    """
    logInfo(f"Retrieving a world map with the world {world.name} and the game {savegame.name} from the database")

    db = getdb()
    cursor = db.cursor()

    if (nation):
        stmt = "SELECT WorldMaps.* FROM WorldMaps JOIN Worlds on WorldMaps.world_id = Worlds.id JOIN Savegames on WorldMaps.savegame_id = Savegames.id JOIN Roles on WorldMaps.role_id = Roles.id WHERE Worlds.name=%s AND Savegames.server_id=%s AND WorldMaps.turn_no=%s AND Roles.discord_id=%s"
        params = [world.name, savegame.server_id, turn, nation.role_id]

    else:
        stmt = "SELECT WorldMaps.* FROM WorldMaps JOIN Worlds on WorldMaps.world_id = Worlds.id JOIN Savegames on WorldMaps.savegame_id = Savegames.id WHERE Worlds.name=%s AND Savegames.server_id=%s AND WorldMaps.turn_no=%s"
        params = [world.name, savegame.server_id, turn]

    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result): return False
    logInfo(f"Successfully retrieved world map image!")
    return result


#Deal with savegames

def dbget_saveGame_byServer(server_id):
        """
        Get the row in the database table Savegames pertaining to this server
        """
        logInfo(f"Getting a savegame with the id {server_id} from the database")

        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT * FROM Savegames WHERE server_id=%s LIMIT 1;"
        params = [server_id]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False
        logInfo("Successfully retrieved savegame!")
        return result

def setupNew_saveGame(savegame, world_name, gamerule_name):
    """
    Given a new savegame object, create a savefile for it and save it to the database.
    """
    logInfo("Setting up a new savegame in the savefiles and database")

    server_id = savegame.server_id
    
    if (dbget_saveGame_byServer(server_id)):
        raise InputError(f"Savegame already exists for the server {server_id}")

    #World must already exist in the database
    worldInfo = dbget_world_byName(world_name)
    
    if not (worldInfo):
        raise InputError(f"World {world_name} does not exist in the database")

    #Update database
    try:
        db = getdb()
        cursor = db.cursor()

        stmt = "INSERT INTO Savegames (server_id, savefile, world_id, gamerulefile) VALUES (%s, %s, %s, %s)"
        params = [server_id, savegame.name, worldInfo['id'], gamerule_name]
        cursor.execute(stmt, params)
        db.commit()
    except Exception as e:
        logError(e)
        raise GameException(f"Savegame could not be inserted!")

    #Generate savefile for the game
    save_saveGame(savegame)

def save_saveGame(savegame):
    """
    Save the savegame to its file based on its id
    """
    FileHandling.easySave(savegame, savegame.name, savesDir)
    logInfo(f"Saved {savegame.name} to file: {savesDir}/{savegame.name}.json")

@lru_cache(maxsize=16)
def load_saveGame(savegame_name):
    """
    Load a savegame object from its savefile
    """
    savegame = FileHandling.easyLoad(savegame_name, savesDir)
    logInfo(f"Savegame {savegame.name} successfully loaded and added to cache")
    return savegame

def get_player_byGame(savegame, player_id):

    db = getdb()
    cursor = db.cursor()

    stmt = """
    SELECT * FROM 
        PlayerGames 
            INNER JOIN Players ON PlayerGames.player_id=Players.id
            INNER JOIN Savegames ON PlayerGames.game_id=Savegames.id
    WHERE Savegames.server_id=%s AND Players.discord_id=%s LIMIT 1;
    """

    params = [savegame.server_id, player_id]
    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result): return False
    logInfo(f"Player {player_id} info for game {savegame.server_id} retrieved")
    return result


#Deal with other files
def load_gamerule(gamerule_name):
    """
    Load a dictionary from a .json file representing a game's ruleset
    """
    gamerule = FileHandling.easyLoad(gamerule_name, gameruleDir)
    logInfo("Gamerule successfully loaded")
    return gamerule


#Player
def add_Player(playerID):
    """
    Add a player by discord ID to the database
    """
    db = getdb()
    cursor = db.cursor()

    try:
        stmt = "INSERT INTO Players (discord_id) VALUES (%s)"
        params = [playerID]
        cursor.execute(stmt, params)
        db.commit()
    except Exception as e:
        raise Exception(f"Could not insert player into database: <{e}>")

    logInfo(f"Added player <{playerID}> to the database")

def get_Player(playerID):
        """
        Get the row in the database table Players pertaining to this player
        """

        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT * FROM Players WHERE discord_id=%s LIMIT 1;"
        params = [playerID]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False

        logInfo(f"Retrieved player from database with id {result['id']}")
        return result


#Role
def add_Role(roleID, roleName):
    """
    Add a role by discord ID to the database
    """
    db = getdb()
    cursor = db.cursor()

    try:
        stmt = "INSERT INTO Roles (discord_id, name) VALUES (%s, %s)"
        params = [roleID, roleName]
        cursor.execute(stmt, params)
        db.commit()
    except Exception as e:
        raise Exception(f"Could not insert role into database: <{e}>")

    logInfo(f"Added role <{roleID}> to the database")

def get_Role(roleID):
        """
        Get the row in the database table Roles pertaining to this role
        """

        db = getdb()
        cursor = db.cursor()

        stmt = "SELECT * FROM Roles WHERE discord_id=%s LIMIT 1;"
        params = [roleID]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False

        logInfo(f"Retrieved role from database with id {result['id']}")
        return result


#Nation
def add_Nation(savegame, nation, playerID):
    """
    Add a nation as a role to the database
    """

    logInfo(f"Adding nation {nation.name} to savegame {savegame.name} with player {playerID}")

    nation_name = nation.name
    roleID = nation.role_id

    db = getdb()
    cursor = db.cursor()

    #Fail if player is already tracked to a nation
    playerExists = get_player_byGame(savegame, playerID)
    if (playerExists):
        logInfo(f"Player {playerID} exists in game {savegame.name} already")
        return False
    
    logInfo("Player is not already tracked to a nation")

    #Insert player if need be
    playerInfo = get_Player(playerID)

    if not (playerInfo):
        add_Player(playerID)
        playerInfo = get_Player(playerID)

    logInfo("Got player")

    #Insert role if need be
    roleInfo = get_Role(roleID)

    if not (get_Role(roleID)):
        add_Role(roleID, nation_name)
        roleInfo = get_Role(roleID)
        logInfo(f"Created new role for \"{nation_name}\"")

    else: 
        logInfo(f"Role <{roleID}> for \"{nation_name}\" already exists in the database")

    savegameInfo = savegame.getRow()

    if not(savegameInfo and playerInfo and roleInfo):
        logInfo(
            f"Something went wrong when adding nation {nation.name}", 
            {
                "savegameInfo": bool(savegameInfo) * "Exists", 
                "playerInfo": bool(playerInfo) * "Exists", 
                "roleInfo": bool(roleInfo) * "Exists"
            }
            )
        raise Exception(f"Something went wrong when adding nation {nation.name}")

    try:
        stmt = "INSERT INTO PlayerGames (player_id, game_id, role_id) VALUES (%s, %s, %s)"
        params = [playerInfo["id"], savegameInfo["id"], roleInfo["id"]]
        cursor.execute(stmt, params)
        db.commit()
    except Exception as e:
        raise Exception(f"Could not insert nation into database: <{e}>")

    result = get_player_byGame(savegame, playerID)

    if not (result): 
        logInfo(f"Adding nation \"{nation_name}\" to database failed")
        return False

    logInfo(f"Added nation \"{nation_name}\" to database")
    return result
    