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
class MappingCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def nationmap(self, ctx):
        pass

    @commands.command()
    async def territory(self, ctx, terrID):
        """
        Look at the full world map associated with this game, without any fog of war unless admin specifies a country.
        """
        logInfo(f"territory({ctx.guild.id, terrID})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        terrEmbed = discord.Embed(
            title = world_terrInfo.name,
            description = ""
        )
        terrEmbed.add_field(name = "Territory ID", value = terrID, inline = False)

        await ctx.send(embed = terrEmbed)

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
            raise NonFatalError("No savegame attached to this server")

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        #Handles getting the world map if one exists that represents the current gamestate, or creating a new one otherwise.
        savegame.world_toImage(mapScale = (100, 100))
        worldMapInfo = dbget_worldMap(world, savegame, savegame.turn)

        logInfo("Got a matching world map for this game.", details = {k: v for k, v in worldMapInfo.items() if k != 'created'})
        
        #Make a menu for the world map display

        menu = MenuEmbed(
            f"{savegame.name} World Map", 
            "_Territories are displayed by their IDs. Use the command \"terr\_lookup <id>\" to see more information about a territory!_", 
            imgurl = worldMapInfo['link'],
            fields = [(f"Territory {i}", saveObject(terr)) for i, terr in enumerate(world.territories)],
            pagesize = 9
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created worldmap_full menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())
        

async def setup(client):
    await client.add_cog(MappingCommands(client))