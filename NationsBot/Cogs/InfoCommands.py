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

        
async def setup(client):
    await client.add_cog(InfoCommands(client))