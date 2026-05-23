import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

from common import *
from database import *
from logger import *
from constants import *

from GameUtils import operations as ops
import GameUtils.playerutils as playerutils

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *
from DiscordUtils.flexiblecommands import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
import ConcertOfNationsEngine.buildings as building_utils
import ConcertOfNationsEngine.territories as territories

from Actions import mapactions

    
# Util functions
def buildingsMenu(client, ctx):
    """
    Return a menu showing all buildings in the context's savegame, either with or without 'buy' buttons
    """
    
    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    all_buildings = building_utils.get_allbuildings(savegame)

    menu = MenuEmbed(
        f"Buildings", 
        f"_Information about all of the buildings in this game's ruleset._\n_Valid status regular expressions: {building_utils.valid_statuspatterns}_", 
        ctx.author.id,
        fields = [
            (buildingName, buildingInfo)
            for buildingName, buildingInfo in all_buildings.items()
        ],
        pagesize = 3,
        sortable = True,
        isPaged = True
        )

    territorySelected = playerutils.getKeyValue(ctx.guild.id, ctx.author.id, MapCacheEnums.TERRITORY_SELECTED)

    if (territorySelected):
        menu.buttons = [
            CommandButton(ctx, client, buildingName, 1, buyBuilding, [territorySelected, buildingName])
            for buildingName in all_buildings.keys()
        ]

    elif (get_player_byGame(savegame, ctx.author.id)):
        menu.buttons = [
            CommandButton(ctx, 
                client, 
                f"Build {buildingName}", 
                2, 
                mapactions.selectTerritory,
                preClick = putBuildingInCart,
                preClickArgs = [ctx, buildingName]
                )
            for buildingName in all_buildings.keys()
        ]

    return menu

def putBuildingInCart(ctx, buildingName):
    playerutils.addKeyValue(ctx.guild.id, ctx.author.id, BuildingCacheEnums.BUILDING_IN_CART, buildingName)


# Building Actions

async def buyBuilding(client, ctx, terrID, buildingName):
    """ 
    As a nation, this is an order to expend resources to purchase a building.
    
    Args:
        terrID: The name or numeric ID of the territory
        buildingName: The name of the building you wish to build
    """
    logInfo(f"buyBuilding(({ctx.guild.id}, {terrID}, {buildingName})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    world = savegame.getWorld()
    if not (world):
        raise InputError("Savegame's world could not be retrieved")


    #Territory info from the map
    world_terrInfo = world[terrID]

    if not world_terrInfo:
        raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
    
    territoryName = world_terrInfo.name
    terrID = world_terrInfo.id

    #Validate that the player owns this territory
    playerinfo = get_player_byGame(savegame, ctx.author.id)

    if not (playerinfo):
        raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

    roleid = playerinfo['role_discord_id']

    nation = get_NationFromRole(ctx, roleid, savegame)

    if not (nation.get_territory(terrID)):
        raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the territory {territoryName}")
    

    #Validate that building can be bought

    if not (nation.canBuyBuilding(savegame, buildingName, building_utils.get_blueprint(buildingName, savegame), terrID)):
        raise InputError(f"Could not buy {buildingName}")

    nation.addBuilding(buildingName, terrID, savegame)

    save_saveGame(savegame)

    return f"Successfully bought {buildingName} in {territoryName}!"
    
async def toggleBuilding(client, ctx, terrID, buildingName, buildingIndex):
    """ 
    Switch a building's status between Active and Inactive

    Args:
        terrID: The name or numeric ID of the territory
        buildingName: The name of the building you wish to toggle
        buildingIndex: Which building you want to access, starting with 0
        """
    logInfo(f"toggleBuilding({ctx.guild.id}, {terrID}, {buildingName}, {buildingIndex})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    world = savegame.getWorld()
    if not (world):
        raise InputError("Savegame's world could not be retrieved")


    #Territory info from the map
    world_terrInfo = world[terrID]

    if not world_terrInfo:
        raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
    
    territoryName = world_terrInfo.name
    terrID = world_terrInfo.id

    playerinfo = get_player_byGame(savegame, ctx.author.id)

    if not (playerinfo):
        raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

    roleid = playerinfo['role_discord_id']

    nation = get_NationFromRole(ctx, roleid, savegame)
    
    if not(nation.get_territory(terrID)):
        raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the territory {territoryName}")

    newstatus = territories.togglebuilding(nation, terrID, buildingName, buildingIndex, savegame)

    if not (newstatus):
        raise InputError(f"Could not toggle building {buildingName} {buildingIndex} in territory {terrID}.")

    save_saveGame(savegame)

    return f"New building status: {newstatus}"

async def destroyBuilding(client, ctx, terrID, buildingName, buildingIndex):
    """ 
    Remove a building from a territory owned by the user

    Args:
        terrID: The name or numeric ID of the territory
        buildingName: The name of the building you wish to remove
        buildingIndex: Which building you want to access, starting with 0
    """
    
    logInfo(f"destroyBuilding({ctx.guild.id}, {terrID}, {buildingName}, {buildingIndex})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    world = savegame.getWorld()
    if not (world):
        raise InputError("Savegame's world could not be retrieved")


    #Territory info from the map
    world_terrInfo = world[terrID]

    if not world_terrInfo:
        raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
    
    territoryName = world_terrInfo.name
    terrID = world_terrInfo.id

    #Nation info
    playerinfo = get_player_byGame(savegame, ctx.author.id)

    if not (playerinfo):
        raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

    roleid = playerinfo['role_discord_id']

    nation = get_NationFromRole(ctx, roleid, savegame)
    
    #Can we do the operation on this territory

    if not(nation.get_territory(terrID)):
        raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the territory {territoryName}")

    if (not territories.hasbuilding(nation, terrID, buildingName)):
        raise InputError(f"Territory {territoryName} does not have building {buildingName}")

    blueprint = building_utils.get_blueprint(buildingName, savegame)

    territories.destroybuilding(nation, terrID, buildingName, buildingIndex, blueprint)

    await ctx.send(f"Building {buildingName} has successfully been deleted from territory {territoryName}")

    save_saveGame(savegame)


# Building Information

async def getBuildings(client, ctx):
    """ 
    Show all of the available buildings in the given server's game. 
    """
    
    logInfo(f"getBuildings({ctx.guild.id})")

    menu = buildingsMenu(client, ctx)

    assignMenu(ctx.author.id, menu)

    logInfo(f"Created buildings menu and assigned it to player {ctx.author.id}")

    return menu

