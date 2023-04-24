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
class MenuCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
    
    @commands.command()
    async def sort(self, ctx, *sortargs):
        """ Retrieve the previous menu and create an embed where its contents are sorted with sort args. """
        logInfo(f"sort({ctx.author.id}, {sortargs})")
        
        playerID = ctx.author.id
        menu = getMenu(playerID)

        menu.sortContent(*sortargs)

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def reverse(self, ctx):
        """ Display the fields in the previous menu in reverse order """
        logInfo(f"reverse({ctx.author.id})")
        
        playerID = ctx.author.id
        menu = getMenu(playerID)

        menu.fields.reverse()

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def pagesize(self, ctx, pagesize):
        """ Change the page size of the current command, then re-display it """
        logInfo(f"pagesize({ctx.author.id}, {pagesize})")
        
        playerID = ctx.author.id
        menu = getMenu(playerID)

        if not (menu):
            raise InputError(f"Player <@{ctx.author.id}> does not have a menu assigned")

        if not(menu.isPaged):
            raise InputError(f"{menu.title} Menu does not have pages")

        if not(ops.isInt(pagesize)):
            raise InputError("Page size must be a whole number")

        pagesize = int(pagesize)

        if ((pagesize > 25) or (pagesize < 1)):
            raise InputError("Page size must be between 1 and 25")

        menu.pagesize = pagesize

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

async def setup(client):
    await client.add_cog(MenuCommands(client))