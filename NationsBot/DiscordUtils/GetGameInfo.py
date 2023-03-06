import re
import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.CustomExceptions import *

def get_PlayerID(playerid):

    playerid = str(playerid)

    if (re.search("^<@[1234567890]*>$", playerid)):
        return int(playerid[2:-1])

    if ops.isInt(playerid):
        return int(playerid)

    raise InputError(f"\"{playerid}\" is not a valid player")

def get_RoleID(roleid):

    roleid = str(roleid)

    if (re.search("^<@&[1234567890]*>$", roleid)):
        return int(roleid[3:-1])

    if ops.isInt(roleid):
        return int(roleid)

    raise InputError(f"\"{roleid}\" is not a valid role")

def get_NationFromRole(ctx, roleid, savegame):
    """Get nation info"""

    roleObj = ctx.guild.get_role(int(get_RoleID(roleid)))
    if not(roleObj):
        raise InputError(f"Unknown role {roleid}")
        return False

    role = get_Role(roleObj.id)
    
    if not(role):
        logInfo(f"Could not load information for the role {roleid}")
        raise InputError(f"Could not load information for the role {roleid}")
        return False

    if not(role['name'] in savegame.nations.keys()):
        raise InputError(f"Nation {role['name']} does not exist in this game")
        return False

    nation = savegame.nations[role['name']]

    if not(role['discord_id'] == nation.role_id):
        raise InputError(f"The role for {role['name']} does not match with an existing nation {nation.name}")
        return False

    logInfo(f"Successfully got nation {nation.name} by role!")

    return nation

def get_SavegameFromCtx(ctx):
    """Get savegame info from database"""

    try:
        savegame = FileHandling.loadObject(load_saveGame(dbget_saveGame_byServer(ctx.guild.id)["savefile"]))
    except Exception as e:
        logInfo("Could not load a game for this server.")
        logError(e)
        raise InputError("Could not load a game for this server.")
        return False

    logInfo(f"Successfully got savegame {savegame.name} from ctx")
    
    return savegame