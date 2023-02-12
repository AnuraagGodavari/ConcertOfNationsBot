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

from GameUtils.FileHandling import *

#The cog itself
class MenuCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
    
    @commands.command()
    async def sort(self, ctx, *sortargs):
        """ Retrieve the previous menu and create an embed where its contents are sorted with sort args. """
        logInfo(f"sort({sortargs})")
        
        playerID = ctx.author.id
        menu = getMenu(playerID)

        menu.sortContent(*sortargs)

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def reverse(self, ctx):
        """ Display the fields in the previous menu in reverse order """
        pass

async def setup(client):
    await client.add_cog(MenuCommands(client))