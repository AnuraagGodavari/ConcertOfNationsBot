import json, datetime, pprint, traceback, re, io

import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

from common import *
from database import *
from logger import *

from GameUtils import operations as ops

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *
from DiscordUtils.flexiblecommands import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
from ConcertOfNationsEngine.buildings import *
import ConcertOfNationsEngine.military as military
import ConcertOfNationsEngine.territories as territories


# Admin Nation Actions

async def give_territory(client, ctx, roleID: str, terrID):
    """
    Give a territory to a nation and take it away from its previous owner, if any. 

    Args:
        roleID: The nation role.
        *terrIDs: A valid territory name or numerical id.
    """
    logInfo(f"giveTerritory({ctx.guild.id}, {roleID}, {terrID})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    nation = get_NationFromRole(ctx, roleID, savegame)

    transferred_terr =  savegame.transfer_territory(terrID, nation)
    if not transferred_terr:
        raise InputError(f"Territory {terrID} transfer to {nation.name} did not work")

    save_saveGame(savegame)

    return f"Successfully transferred territory {terrID} to <@&{roleid}>"

async def remove_territory(client, ctx, roleid: str, terrID):
    """
    Remove a territory from a nation.

    Args:
        roleid: The nation role.
        *terrid: A valid territory name or numerical id.
    """

    logInfo(f"giveTerritory({ctx.guild.id}, {roleid}, {terrID})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    
    world = savegame.getWorld()
    if not (world):
        raise InputError("Savegame's world could not be retrieved")

    nation = get_NationFromRole(ctx, roleid, savegame)

    #Check that the territory is valid before removing

    world_terr = world[terrID]

    if not world_terr:
        raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

    territoryName = world_terr.name

    if not(nation.get_territory(terrID)):
        raise InputError(f"Territory {terrID} does not belong to {nation.name}")
    
    #Actually remove the territory

    terrID = world_terr.id

    removed_terr = savegame.remove_territory(terrID, nation)

    removed_terr_json = filehandling.saveObject(removed_terr)

    removed_terr_file = io.StringIO(json.dumps(removed_terr_json, indent = 2))

    save_saveGame(savegame)
    
    return {
        "content": f"Successfully removed the territories: {terrID} from <@&{roleid}>. Attached removed territory information.", 
        "file": discord.File(
            fp = removed_terr_file, 
            filename = f"Territory_{terrID}.json"
            )
        }

async def give_resources(client, ctx, roleid, resource, amount):
    """
    Give a specified amount of any resources to a specified nation.

    Args:
        roleid: The nation role.
        *args (tuple): A list of resources and numbers. Example:
        ("Iron", "2", "Money", "3")
    """

    logInfo(f"giveResources({ctx.guild.id}, {roleid}, {resource}, {amount})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    nation = get_NationFromRole(ctx, roleid, savegame)
        
    if not(resource in savegame.getGamerule()["Resources"] + ["Money"]):
        raise InputError(f"\"{resource}\" is not a resource")

    resources_toadd = {resource: amount}

    logInfo(f"Adding resources to {nation.name}", details = resources_toadd)

    nation.resources = ops.combineDicts(nation.resources, resources_toadd)

    logInfo(f"Successfully added resources", details = nation.resources)

    save_saveGame(savegame)

    return f"Successfully added resources, type \"_n.nationinfo <@&{roleid}>_\" to view changes"

async def change_capacity(client, ctx, roleid, category, amount):
    """ 
    Change the bureaucratic capacity for any category of a specific nation's bureaucracy

    Args:
        roleid: The nation role.
        category: The bureaucratic category.
        amount: A non-negative integer value for the new bureaucratic capacity.
    """

    logInfo(f"change_capacity({ctx.guild.id}, {roleid}, {category}, {amount})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    nation = get_NationFromRole(ctx, roleid, savegame)
    

    if not(category in nation.bureaucracy.keys()):
        raise InputError(f"No such bureaucratic category \"{category}\"")

    if (amount <= 0):
        raise InputError(f"{category} capacity cannot have value \"{amount}\", must be a non-negative integer")

    logInfo(f"Changing bureaucratic capacity for {nation.name} for category {category} from {nation.bureaucracy[category]} to {amount}")

    nation.bureaucracy[category] = (nation.bureaucracy[category][0], int(amount))

    save_saveGame(savegame)

    logInfo(f"Successfully changed national bureaucracy", details = nation.bureaucracy)
    
    return f"Successfully changed bureaucratic capacity for {category} category to {amount}, type \"_n.nationinfo <@&{roleid}>_\" to view changes"

async def change_tax(client, ctx, roleid, amount):
    """ 
    Change a nation's national tax modifier

    Args:
        roleid: The nation role.
        amount: A decimal value representing the new tax rate.
    """

    logInfo(f"change_capacity({ctx.guild.id}, {roleid}, {amount})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    nation = get_NationFromRole(ctx, roleid, savegame)

    logInfo(f"Changing tax modifier for {nation.name} from {nation.modifiers['Tax']} to {amount}")

    nation.modifiers['Tax'] = amount

    save_saveGame(savegame)

    logInfo(f"Successfully changed national tax modifier to {nation.modifiers['Tax']}")
    
    return f"Successfully changed national tax modifier to {nation.modifiers['Tax']}, type \"_n.nationinfo <@&{roleid}>_\" to view changes"
