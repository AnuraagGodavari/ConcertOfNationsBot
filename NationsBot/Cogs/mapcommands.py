import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

from common import *
from database import *
from logger import *
from constants import *

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *
from DiscordUtils.flexiblecommands import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
import ConcertOfNationsEngine.buildings

from GameUtils.filehandling import *
import GameUtils.playerutils as playerutils

from Actions import mapactions

#The cog itself
class MapCommands(commands.Cog):
    """ Commands for seeing maps of the world and interacting with territories"""
    
    def __init__(self, client):
        self.client = client
        

    @app_commands.command()
    async def worldmap(self, interaction):
        """Look at the world map from the perspective of the player country"""
        
        await handle_interaction(interaction.client, interaction, mapactions.worldmap)
        
    @app_commands.command()
    @commands.has_permissions(administrator = True)
    async def worldmap_full(self, interaction, role: discord.Role = None):
        """ Look at the full world map associated with this game, without any fog of war unless admin specifies a country.

        Args:
            role: The nation role. If not specified, the worldmap will show all territories.
        """
        
        await handle_interaction(interaction.client, interaction, mapactions.worldmapFull, role.id if role else None)


    #Territories

    @app_commands.command()
    async def territories(self, interaction, role: discord.Role = None):
        """ Show all of the territories owned by a nation, either that of the author or one that is specified.

        Args:
            role: The nation role. By default it's the nation belonging to the user.
        """
        
        await handle_interaction(interaction.client, interaction, mapactions.getTerritories, role.id if role else None)

    @app_commands.command()
    async def territory(self, interaction, territory: str):
        """ Look at the details of a territory.
        
        Args:
            territory: The name or numeric ID of the territory.
        """
        
        await handle_interaction(interaction.client, interaction, mapactions.territory, territory)

    @app_commands.command()
    async def territory_buildings(self, interaction, territory: str):
        """ Show all of the available buildings in a given territory. 
        
        Args:
            territory: The name or numeric ID of the territory.
        """
        
        await handle_interaction(interaction.client, interaction, mapactions.territoryBuildings, territory)

async def setup(client):
    await client.add_cog(MapCommands(client))