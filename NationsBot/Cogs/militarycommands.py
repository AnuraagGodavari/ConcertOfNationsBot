import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *

from GameUtils.filehandling import *
import GameUtils.operations as ops

#The cog itself
class MilitaryCommands(commands.Cog):
    """ A cog for player commands related to the military """

    #Manpower

    @commands.command(aliases=['raiseManpower', 'raise-manpower', 'raisemanpower'])
    async def raise_manpower(self, ctx, terrID, amount):
        """ Raise manpower in a given territory. """
        logInfo(f"raise_manpower({ctx.guild.id}, {terrID}, {amount})")

        if not (ops.isPositiveInt(amount)):
            raise InputError(f"Invalid amount {amount}, must be positive integer")

        amount = int(amount)

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terr = world[terrID]

        if not world_terr:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

        territoryName = world_terr.name

        #Validate that the player owns this territory
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (territoryName in nation.territories.keys()):
            raise InputError(f"<@{playerinfo['role_discord_id']}> does not own the territory {territoryName}")

        total_pop = territories.get_totalpopulation(nation, territoryName)

        if (total_pop <= 0):
            raise InputError("Manpower cannot be raised from this territory because it has no population")

        if (territories.get_manpower(nation, territoryName) + amount > total_pop):
            raise InputError(f"Cannot raise {amount} manpower because it exceeds total ummobilized population of {total_pop}")

        territories.recruit_manpower(nation, territoryName, amount)

        logInfo(f"Successfully raised {amount} manpower in territory {territoryName}")
        await ctx.send(f"Successfully raised {amount} manpower in territory {territoryName}")

        save_saveGame(savegame)

    @commands.command(aliases=['disbandManpower', 'disband-manpower', 'disbandmanpower'])
    async def disband_manpower(self, ctx, terrID, amount):
        """ Disband manpower in a given territory. """
        logInfo(f"disband_manpower({ctx.guild.id}, {terrID}, {amount})")

        if not (ops.isPositiveInt(amount)):
            raise InputError(f"Invalid amount {amount}, must be positive integer")

        amount = int(amount)

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terr = world[terrID]

        if not world_terr:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

        territoryName = world_terr.name

        #Validate that the player owns this territory
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (territoryName in nation.territories.keys()):
            raise InputError(f"<@{playerinfo['role_discord_id']}> does not own the territory {territoryName}")

        total_pop = territories.get_totalpopulation(nation, territoryName)

        if (total_pop <= 0):
            raise InputError("Manpower cannot be disbanded from this territory because it has no population")

        manpower = territories.get_manpower(nation, territoryName)

        if (manpower < amount):
            raise InputError(f"Cannot disband {amount} manpower because it exceeds total manpower {manpower}")

        territories.disband_manpower(nation, territoryName, amount)

        logInfo(f"Successfully disbanded {amount} manpower in territory {territoryName}")
        await ctx.send(f"Successfully disbanded {amount} manpower in territory {territoryName}")

        save_saveGame(savegame)


async def setup(client):
    await client.add_cog(MilitaryCommands(client))