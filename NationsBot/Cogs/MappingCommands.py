import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from DiscordUtils.GetGameInfo import *

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.CustomExceptions import *

#The cog itself
class MappingCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def nationmap(self, ctx):
        pass

    @commands.command()
    async def worldmap(self, ctx, roleid = None):
        logInfo("Not accounting for 'known world'")
        """
        logInfo(f"worldmap({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        nation = None

        if (roleid):
            nation = get_NationFromRole(ctx, roleid, savegame)
            if not (nation): 
                raise InputError(f"Could not get nation with role {roleid}")
        """
        
    @commands.command()
    @commands.has_permissions(administrator = True)
    async def worldmap_full(self, ctx):
        """
        Look at the full world map associated with this game, without any fog of war unless admin specifies a country.
        """
        logInfo(f"worldmap_full({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        worldMapInfo = dbget_worldMap(world, savegame, savegame.turn)

        logInfo(worldMapInfo)
        await ctx.send(worldMapInfo['link'])
        

        
def setup(client):
    client.add_cog(MappingCommands(client))