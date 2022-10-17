import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from ConcertOfNationsEngine.GameHandling import *


def get_NationFromRole(ctx, roleid, savegame):
    """Get nation info"""

    roleObj = ctx.guild.get_role(int(roleid[3:-1]))
    if not(roleObj):
        logInfo(f"Unknown role {roleid}")
        raise Exception(f"Unknown role {roleid}")
        return False

    role = get_Role(roleObj.id)
    
    if not(role):
        logInfo(f"Could not load information for the role {roleid}")
        raise Exception(f"Could not load information for the role {roleid}")
        return False

    if not(role['name'] in savegame.nations.keys()):
        logInfo(f"Nation {role['name']} does not exist in this game")
        return False

    nation = savegame.nations[role['name']]

    if not(role['discord_id'] == nation.role_id):
        logInfo(f"Role error: The role for {role['name']} does not match with an existing nation {nation.name}")
        return False

    return nation

def get_SavegameFromCtx(ctx):
    """Get savegame info from database"""

    try:
        savegame = FileHandling.loadObject(load_saveGame(dbget_saveGame_byServer(ctx.guild.id)["savefile"]))
    except Exception as e:
        logInfo("Could not load a game for this server.")
        logError(e)
        raise Exception("Could not load a game for this server.")
        return False
    
    return savegame