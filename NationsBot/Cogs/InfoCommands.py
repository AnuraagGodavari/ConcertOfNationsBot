import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from DiscordUtils.menuembed import *
from DiscordUtils.GetGameInfo import *

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.CustomExceptions import *

#The cog itself
class InfoCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def gamestate(self, ctx):
        """
        Provide info about the current game as it is right now
        """
        logInfo(f"giveTerritory({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)

        menu = MenuEmbed(
            f"{savegame.name} Game State", 
            None, 
            None,
            fields = [
                ("Turn", savegame.turn),
                ("Date", f"Month {savegame.date['m']}, Year {savegame.date['y']}")
            ]
            )

        logInfo(f"Created Game State display")

        await ctx.send(embed = menu.toEmbed())

    @commands.command()
    async def nationinfo(self, ctx, roleid = None):
        """ Display basic info about the author's nation or, if another role is specified, the same info about that role's nation. """
        logInfo(f"nationinfo({ctx.guild.id}, {roleid})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        if (not roleid):

            playerinfo = get_player_byGame(savegame, ctx.author.id)

            if not (playerinfo):
                raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

            roleid = playerinfo['role_discord_id']
            logInfo(f"Got default role id {roleid} for this player")

        nation = get_NationFromRole(ctx, roleid, savegame)
        if not (nation): 
            return #Error will already have been handled

        menu = MenuEmbed(
            f"{nation.name} Information", 
            None, 
            None,
            fields = [
                ("Resources", nation.resources),
            ]
            )

        logInfo(f"Created Nation info display")

        await ctx.send(embed = menu.toEmbed())

        
async def setup(client):
    await client.add_cog(InfoCommands(client))