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
    async def worlds(self, ctx):
        """ 
        Get a menu of all the available world json files
        """
        logInfo(f"worlds({ctx.guild.id})")

        #Get every world file
    
        worlds = [world.split('.json')[0] for world in os.listdir(worldsDir) if world.endswith('.json')]

        menu = MenuEmbed(
            f"World Maps", 
            "_Use the command get_world to examine a world file!_", 
            ctx.author.id,
            fields = [
                (
                    world, ''
                ) 
                for world in worlds
            ],
            pagesize = 9,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created worlds menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def gamerules(self, ctx):
        """ 
        Get a menu of all the available gamerule json files
        """
        logInfo(f"gamerules({ctx.guild.id})")

        #Get every world file
    
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

    @commands.command(aliases = ["getworld", "get-world", "getWorldmap"])
    async def get_world(self, ctx, world_name):
        """ 
        Retrieve a world json file 
        Args:
            world_name: The name of the world
        """
        logInfo(f"get_world({ctx.guild.id}, {world_name})")

        filepath = worldsDir + "/" + world_name + ".json"

        if not(os.path.isfile(filepath)):
            raise InputError(f"\"{world_name}\" is not a valid world")
        
        await ctx.send(f"Attaching file {world_name}.json", file=discord.File(filepath))

        logInfo(f"Successfully sent the file {world_name}.json")

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

    @commands.command(aliases = ["modifyworld", "modify-world", "modifyWorld"])
    async def modify_world(self, ctx, world_name): 
        """
        Upload a modified world json file to change the file being used by the bot
        Args:
            world_name: The name of the world (without the .json file extension)
        """
        logInfo(f"modify_world({ctx.guild.id}, {world_name})")

        filepath = worldsDir + "/" + world_name + ".json"

        if not(os.path.isfile(filepath)):
            raise InputError(f"\"{world_name}\" is not a valid world")

        if (len(ctx.message.attachments) != 1):
            raise InputError("Can only attach exactly one json file when invoking this command")

        new_world_json = None

        if not(validate_world_edit_permissions(get_PlayerID(ctx.author.id), world_name)):
            raise InputError(f"User <@{ctx.author.id}> does not have permission to edit this world file.")

        try:
            new_world_file = await ctx.message.attachments[0].to_file()
            new_world_json = json.load(new_world_file.fp)
        except Exception as e:
            logError(e)
            raise InputError("Input file is not valid JSON.")

        validate_modified_world(world_name, new_world_json)

        logInfo(f"Validated and saved world {world_name}!")
        await ctx.send(f"Validated and saved world {world_name}!")
        
    @commands.command(aliases = ["modifygamerule", "modify-gamerule", "modifyGamerule"])
    async def modify_gamerule(self, ctx, gamerule_name): 
        """
        Upload a modified gamerule json file to change the file being used by the bot
        Args:
            gamerule_name: The name of the gamerule (without the .json file extension)
        """
        logInfo(f"modify_gamerule({ctx.guild.id}, {gamerule_name})")

        filepath = gameruleDir + "/" + gamerule_name + ".json"

        if not(os.path.isfile(filepath)):
            raise InputError(f"\"{gamerule_name}\" is not a valid gamerule")

        if (len(ctx.message.attachments) != 1):
            raise InputError("Can only attach exactly one json file when invoking this command")

        new_gamerule_json = None

        if not(validate_gamerule_edit_permissions(get_PlayerID(ctx.author.id), gamerule_name)):
            raise InputError(f"User <@{ctx.author.id}> does not have permission to edit this gamerule file.")

        try:
            new_gamerule_file = await ctx.message.attachments[0].to_file()
            new_gamerule_json = json.load(new_gamerule_file.fp)
        except Exception as e:
            logError(e)
            raise InputError("Input file is not valid JSON.")

        validate_modified_gamerule(gamerule_name, new_gamerule_json)

        logInfo(f"Validated and saved gamerule {gamerule_name}!")
        await ctx.send(f"Validated and saved gamerule {gamerule_name}!")
        

async def setup(client):
    await client.add_cog(DeveloperCommands(client))