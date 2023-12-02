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
class DeveloperCommands(commands.Cog):
    """ Commands used to manage menus """
    
    def __init__(self, client):
        self.client = client
    
    @commands.command()
    async def worldmaps(self, ctx):
        """ 
        Get a menu of all the available worldmap json files
        """
        logInfo(f"worldmaps({ctx.guild.id})")

        #Get every worldmap file
    
        worldmaps = [worldmap.split('.json')[0] for worldmap in os.listdir(worldsDir) if worldmap.endswith('.json')]

        menu = MenuEmbed(
            f"World Maps", 
            "_Use the command get_worldmap to examine a worldmap file!_", 
            ctx.author.id,
            fields = [
                (
                    worldmap, ''
                ) 
                for worldmap in worldmaps
            ],
            pagesize = 9,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created worldmaps menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def gamerules(self, ctx):
        """ 
        Get a menu of all the available gamerule json files
        """
        logInfo(f"gamerules({ctx.guild.id})")

        #Get every worldmap file
    
        gamerules = [gamerule.split('.json')[0] for gamerule in os.listdir(gameruleDir) if gamerule.endswith('.json')]

        menu = MenuEmbed(
            f"Gamerules", 
            "_Use the command get_gamerule to examine a gamerule file!_", 
            ctx.author.id,
            fields = [
                (
                    gamerule, ''
                ) 
                for gamerule in gamerules
            ],
            pagesize = 9,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created gamerules menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command(aliases = ["getworldmap", "get-worldmap", "getWorldmap"])
    async def get_worldmap(self, ctx, worldmap_name):
        """ 
        Retrieve a worldmap json file 
        Args:
            worldmap_name: The name of the worldmap
        """
        logInfo(f"get_worldmap({ctx.guild.id}, {worldmap_name})")

        filepath = worldsDir + "/" + worldmap_name + ".json"

        if not(os.path.isfile(filepath)):
            raise InputError(f"\"{worldmap_name}\" is not a valid worldmap")
        
        await ctx.send(f"Attaching file {worldmap_name}.json", file=discord.File(filepath))

        logInfo(f"Successfully sent the file {worldmap_name}.json")

    @commands.command(aliases = ["getgamerule", "get-gamerule", "getGamerule"])
    async def get_gamerule(self, ctx, gamerule_name):
        """ 
        Retrieve a gamerule json file 
        Args:
            gamerule_name: The name of the gamerule (without the .json file extension)
        """
        logInfo(f"get_gamerule({ctx.guild.id}, {gamerule_name})")

        filepath = gameruleDir + "/" + gamerule_name + ".json"

        if not(os.path.isfile(filepath)):
            raise InputError(f"\"{gamerule_name}\" is not a valid gamerule")
        
        await ctx.send(f"Attaching file {gamerule_name}.json", file=discord.File(filepath))

        logInfo(f"Successfully sent the file {gamerule_name}.json")

async def setup(client):
    await client.add_cog(DeveloperCommands(client))