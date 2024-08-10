import json
from functools import lru_cache

from logger import *

from database import *
from common import *
from GameUtils import filehandling, schema
from Schemas.schema_world import schema_world
from Schemas.schema_gamerule import schema_gamerule

from ConcertOfNationsEngine.gameobjects import *
from ConcertOfNationsEngine.concertofnations_exceptions import *

# Deal with worlds

def save_world(world):
    with open(f"{worldsDir}/{world.name}.json", 'w') as f:
        json.dump(filehandling.saveObject(world), f, indent = 4)

    logInfo(f"Successfully saved world {world.name}")

@lru_cache(maxsize=16)
def load_world(world_name):
    """
    Load a world from a .json file representing a map without nations, buildings etc; only terrain, resources etc.
    """
    world = filehandling.easyLoad(world_name, worldsDir)
    logInfo(f"World {world.name} successfully loaded")
    return world

def dbget_world_byName(world_name):
    """
    Get the row in the database table Worlds with this name
    """

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = "SELECT * FROM Worlds WHERE name=%s LIMIT 1;"
    params = [world_name]
    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result): return False
    logInfo(f"Retrieved world {world_name} from database")
    return result

def dbget_world_bysavegame(server_id):
    """
    Get the row in the database table Worlds associated with this savegame
    """
        
    logInfo(f"Getting world for savegame {server_id} from database")
    db = getdb()
    cursor = db.cursor()

    stmt = "SELECT Worlds.* FROM Savegames JOIN Worlds ON Savegames.world_id = Worlds.id WHERE Savegames.server_id=%s LIMIT 1;"
    params = [server_id]
    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result):
        return False

    logInfo("Got worldfile info")
    return gamehandling.load_world(result["name"])

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
        cursor = db.cursor(buffered=True)

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
    
    if ((savegame.gamestate["mapChanged"] == False) and (dbget_worldMap(world, savegame, savegame.turn, nation))):
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
        cursor = db.cursor(buffered=True)

        if (nation):
            stmt = "INSERT INTO WorldMaps (world_id, savegame_id, turn_no, turn_map_no, role_id, filename, link) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            params = [worldInfo['id'], savegameInfo['id'], savegame.turn, savegame.gamestate["mapNum"], roleInfo['id'], filename, link]

        else:
            stmt = "INSERT INTO WorldMaps (world_id, savegame_id, turn_no, turn_map_no, filename, link) VALUES (%s, %s, %s, %s, %s, %s)"
            params = [worldInfo['id'], savegameInfo['id'], savegame.turn, savegame.gamestate["mapNum"], filename, link]

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
    cursor = db.cursor(buffered=True)

    if (nation):
        stmt = "SELECT WorldMaps.* FROM WorldMaps JOIN Worlds on WorldMaps.world_id = Worlds.id JOIN Savegames on WorldMaps.savegame_id = Savegames.id JOIN Roles on WorldMaps.role_id = Roles.id WHERE Worlds.name=%s AND Savegames.server_id=%s AND WorldMaps.turn_no=%s AND WorldMaps.turn_map_no=%s AND Roles.role_discord_id=%s"
        params = [world.name, savegame.server_id, turn, savegame.gamestate["mapNum"] - int(savegame.gamestate["mapChanged"]), nation.role_id]

    else:
        stmt = "SELECT WorldMaps.* FROM WorldMaps JOIN Worlds on WorldMaps.world_id = Worlds.id JOIN Savegames on WorldMaps.savegame_id = Savegames.id WHERE Worlds.name=%s AND Savegames.server_id=%s AND WorldMaps.turn_no=%s AND WorldMaps.turn_map_no=%s"
        params = [world.name, savegame.server_id, turn, savegame.gamestate["mapNum"] - int(savegame.gamestate["mapChanged"])]

    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result): return False

    logInfo(f"Successfully retrieved world map image!")
    return result


# Deal with savegames

def dbget_saveGame_byServer(server_id):
        """
        Get the row in the database table Savegames pertaining to this server
        """
        logInfo(f"Getting a savegame with the id {server_id} from the database")

        db = getdb()
        cursor = db.cursor(buffered=True)

        stmt = "SELECT * FROM Savegames WHERE server_id=%s LIMIT 1;"
        params = [server_id]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False
        logInfo("Successfully retrieved savegame!")
        return result

def insert_savegame(savegame, worldInfo, gamerule_name):
    """
    Try to put a savegame in the database
    """
    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = "INSERT INTO Savegames (server_id, savefile, world_id, gamerulefile) VALUES (%s, %s, %s, %s)"
    params = [savegame.server_id, savegame.name, worldInfo['id'], gamerule_name]
    cursor.execute(stmt, params)
    db.commit()


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
    try: insert_savegame(savegame, worldInfo, gamerule_name)
    except Exception as e:
        logError(e)
        raise LogicError(f"Savegame could not be inserted!")

    #Generate savefile for the game
    save_saveGame(savegame)

def save_saveGame(savegame):
    """
    Save the savegame to its file based on its id
    """
    filehandling.easySave(savegame, savegame.name, savesDir)
    logInfo(f"Saved {savegame.name} to file: {savesDir}/{savegame.name}.json")

@lru_cache(maxsize=16)
def load_saveGame(savegame_name):
    """
    Load a savegame object from its savefile
    """
    savegame = filehandling.easyLoad(savegame_name, savesDir)
    logInfo(f"Savegame {savegame.name} successfully loaded and added to cache")
    return savegame

def load_saveGame_from_server(server_id):
    """
    Load a savegame object from its savefile by server id
    """
    
    savegameInfo = dbget_saveGame_byServer(server_id)

    savegame = load_saveGame(savegameInfo["savefile"])

    logInfo(f"Savegame {savegame.name} successfully loaded and added to cache")
    return savegame

def get_player_byGame(savegame, player_id):

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = """
    SELECT *, Players.player_discord_id, Roles.role_discord_id FROM 
        PlayerGames 
            INNER JOIN Players ON PlayerGames.player_id=Players.id
            INNER JOIN Savegames ON PlayerGames.game_id=Savegames.id
            INNER JOIN Roles ON PlayerGames.role_id=Roles.id
    WHERE Savegames.server_id=%s AND Players.player_discord_id=%s LIMIT 1;
    """

    params = [savegame.server_id, player_id]
    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result): return False
    logInfo(f"Player {player_id} info for game {savegame.server_id} retrieved")
    return result

def remove_player_fromGame(savegame, player_id):

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = """
    DELETE PlayerGames.* FROM PlayerGames
        INNER JOIN Players ON PlayerGames.player_id=Players.id
        INNER JOIN Savegames ON PlayerGames.game_id=Savegames.id
    WHERE Savegames.server_id=%s AND Players.player_discord_id=%s;
    """

    params = [savegame.server_id, player_id]
    cursor.execute(stmt, params)
    db.commit()


# Deal with gamerules

def save_gamerule(gamerule_name, gamerule):
    with open(f"{gameruleDir}/{gamerule_name}.json", 'w') as f:
        json.dump(filehandling.saveObject(gamerule), f, indent = 4)

    logInfo(f"Successfully saved gamerule {gamerule_name}")

def load_gamerule(gamerule_name):
    """
    Load a dictionary from a .json file representing a game's ruleset
    """
    gamerule = filehandling.easyLoad(gamerule_name, gameruleDir)
    logInfo("Gamerule successfully loaded")
    return gamerule

def dbget_gamerule(server_id):
    """
    Get the name of the gamerule associated with this savegame
    """
        
    logInfo(f"Getting gamerule for savegame {server_id} from database")
    db = getdb()
    cursor = db.cursor()

    stmt = "SELECT gamerulefile FROM Savegames WHERE server_id=%s LIMIT 1;"
    params = [server_id]
    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result):
        return False

    logInfo("Got gamerule info")
    return gamehandling.load_gamerule(result["gamerulefile"])


# Get connected files

def gamerule_connected_files(gamerule_name):
    """
    Get all savegames and worlds that use this gamerule
    """

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = "SELECT Savegames.savefile, Worlds.name as world_name FROM Savegames JOIN Worlds ON Savegames.world_id = Worlds.id WHERE gamerulefile=%s"
    params = [gamerule_name]
    cursor.execute(stmt, params)
    result = cursor.fetchall()

    if not (result): return False

    result = [dict(zip(("savefile", "worldfile"), item)) for item in result]

    logInfo(f"Retrieved savegames and worlds from database which use gamerule {gamerule_name}")
    return result

def world_connected_files(world_name):
    """
    Get all savegames and gamerules that use this world
    """

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = "SELECT Savegames.savefile, Savegames.gamerulefile FROM Savegames JOIN Worlds ON Savegames.world_id = Worlds.id WHERE Worlds.name=%s"
    params = [world_name]
    cursor.execute(stmt, params)
    result = cursor.fetchall()

    if not (result): return False

    result = [dict(zip(("savefile", "gamerulefile"), item)) for item in result]

    logInfo(f"Retrieved savegames and worlds from database which use gamerule {world_name}")
    return result


# Validate files

def validate_modified_gamerule(gamerule_name, gamerule_contents):
    """
    Validate a gamerule against its schema
    """
    
    schema.schema_validate(schema_gamerule, gamerule_contents, gamerule = gamerule_contents)

    connected_files = gamerule_connected_files(gamerule_name)

    for world_name in [files["worldfile"] for files in connected_files]:
        
        with open (worldsDir + f"/{world_name}.json", 'r') as f:
            world = json.load(f)

        try:
            schema.schema_validate(schema_world, world, gamerule = gamerule_contents, world = world)
        except Exception as e:
            logError(e)
            raise InputError(f"Worldmap {world_name} is now invalid with the gamerule change.")
    
    logInfo(f"Successfully validated modified gamerule {gamerule_name}.")

    save_gamerule(gamerule_name, gamerule_contents)

def validate_modified_world(world_name, world_contents):
    """
    Validate a world against its schema
    """
    
    schema.schema_validate(schema_world, world_contents, world = world_contents)

    connected_files = world_connected_files(world_name)

    for gamerule_name in [files["gamerulefile"] for files in connected_files]:
        
        with open (gameruleDir + f"/{gamerule_name}.json", 'r') as f:
            gamerule = json.load(f)

        try:
            schema.schema_validate(schema_world, world_contents, gamerule = gamerule, world = world_contents)
        except Exception as e:
            logError(e)
            raise InputError(f"Modified world {world_name} is now incompatible with the gamerule {gamerule_name}.")

    try:
        world = filehandling.loadObject(world_contents)
    except Exception as e:
        logError(e)
        raise InputError(f"World could not be converted to the World class.")
    
    logInfo(f"Successfully validated modified world {world.name}.")

    save_world(world)


# Edit game files

def validate_gamerule_edit_permissions(player_id, gamerule_name):
    """
    Validate that a player is able to edit a gamerule file
    """

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = "SELECT player_id, game_id FROM GameruleEditPermissions AS Perms JOIN Players ON Perms.player_id = Players.id JOIN Savegames ON Perms.game_id = Savegames.id WHERE Players.player_discord_id = %s AND Savegames.gamerulefile=%s LIMIT 1"
    params = [player_id, gamerule_name]
    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result): return False

    logInfo(f"Retrieved gamerule {gamerule_name} edit permissions for player {player_id}")
    return result

def validate_world_edit_permissions(player_id, world_name):
    """
    Validate that a player is able to edit a gamerule file
    """

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = "SELECT player_id, world_id FROM WorldEditPermissions AS Perms JOIN Players ON Perms.player_id = Players.id JOIN Worlds ON Perms.world_id = Worlds.id WHERE Players.player_discord_id = %s AND Worlds.name=%s LIMIT 1"
    params = [player_id, world_name]
    cursor.execute(stmt, params)
    result = fetch_assoc(cursor)

    if not (result): return False

    logInfo(f"Retrieved world {world_name} edit permissions for player {player_id}")
    return result


# Player
def add_Player(playerID):
    """
    Add a player by discord ID to the database
    """
    db = getdb()
    cursor = db.cursor(buffered=True)

    try:
        stmt = "INSERT INTO Players (player_discord_id) VALUES (%s)"
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
        cursor = db.cursor(buffered=True)

        stmt = "SELECT * FROM Players WHERE player_discord_id=%s LIMIT 1;"
        params = [playerID]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False

        logInfo(f"Retrieved player from database with id {result['id']}")
        return result


# Role
def add_Role(roleID, roleName):
    """
    Add a role by discord ID to the database
    """
    db = getdb()
    cursor = db.cursor(buffered=True)

    try:
        stmt = "INSERT INTO Roles (role_discord_id, name) VALUES (%s, %s)"
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
        cursor = db.cursor(buffered=True)

        stmt = "SELECT * FROM Roles WHERE role_discord_id=%s LIMIT 1;"
        params = [roleID]
        cursor.execute(stmt, params)
        result = fetch_assoc(cursor)

        if not (result): return False

        logInfo(f"Retrieved role from database with id {result['id']}")
        return result


# Players and associated roles
def get_PlayerGames(server_id):
    """
    Get the row in the database table Roles pertaining to this role
    """

    db = getdb()
    cursor = db.cursor(buffered=True)

    stmt = "SELECT Savegames.*, Players.*, Roles.* FROM Savegames \
        JOIN PlayerGames ON Savegames.id = PlayerGames.game_id \
        JOIN Players ON PlayerGames.player_id = Players.id \
        JOIN Roles ON PlayerGames.role_id = Roles.id \
        WHERE Savegames.server_id=%s"
    
    params = [server_id]
    cursor.execute(stmt, params)
    result = fetch_assoc_all(cursor)

    if not (result): return False

    logInfo(f"Retrieved player game from database from server {server_id}")
    return result

# Nation
def add_Nation(savegame, nation, playerID):
    """
    Add a nation as a role to the database
    """

    logInfo(f"Adding nation {nation.name} to savegame {savegame.name} with player {playerID}")

    nation_name = nation.name
    roleID = nation.role_id

    db = getdb()
    cursor = db.cursor(buffered=True)

    #Fail if player is already tracked to a nation
    playerExists = get_player_byGame(savegame, playerID)
    if (playerExists):
        logInfo(f"Player {playerID} exists in game {savegame.name} already, removing player")
        remove_player_fromGame(savegame, playerID)
        logInfo(f"Removed player {playerID} from previous role in game {savegame.name}")
    
    else: logInfo("Player is not already tracked to a nation")

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
        return False

    try:
        stmt = "INSERT INTO PlayerGames (player_id, game_id, role_id) VALUES (%s, %s, %s)"
        params = [playerInfo["id"], savegameInfo["id"], roleInfo["id"]]
        cursor.execute(stmt, params)
        db.commit()
    except Exception as e:
        logError(e, errorInfo = {"Message": "Could not insert nation into database"})
        return False

    result = get_player_byGame(savegame, playerID)

    if not (result): 
        logInfo(f"Adding nation \"{nation_name}\" to database failed")
        return False

    logInfo(f"Added nation \"{nation_name}\" to database")
    return result
    