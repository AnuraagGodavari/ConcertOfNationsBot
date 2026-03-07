import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

from common import *
from database import *
from logger import *

from GameUtils import operations as ops

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *
from DiscordUtils.flexiblecommands import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
from ConcertOfNationsEngine.buildings import *
import ConcertOfNationsEngine.military as military
import ConcertOfNationsEngine.territories as territories

from Actions import infoactions


#The cog itself
class InfoCommands(commands.Cog):
    """Commands that deliver information to a player about the game they're currently in"""
    
    def __init__(self, client):
        self.client = client
        
    @app_commands.command()
    async def gamestate(self, interaction):
        """ Provide info about the current game as it is right now. """
        await handle_interaction(interaction.client, interaction, infoactions.gamestate)

    @app_commands.command()
    async def nationinfo(self, interaction, role: discord.Role = None):
        """Display basic info about the author's nation or, if another role is specified, that role's nation. 

        Parameters
        -----------
            role (optional): discord.Role
                The nation role.
        """
        
        await handle_interaction(interaction.client, interaction, infoactions.nationinfo, role.id if role else None)


    @app_commands.command()
    async def nations(self, interaction):
        """Display basic info about all nations in the game."""
        
        await handle_interaction(interaction.client, interaction, infoactions.nations)


    # Military Information

    @app_commands.command()
    async def forces(self, interaction, role: discord.Role = None):
        """Show all of the forces controlled by a nation, either that of the author or one that is specified. 
        
        Parameters
        -----------
            role (optional): discord.Role
                The nation role.
        """
        
        await handle_interaction(interaction.client, interaction, infoactions.forces, role.id if role else None)

    @app_commands.command()
    async def force(self, interaction, forcename: str):
        """Show a specific force controlled by any nation in the game. 

        Parameters
        -----------
            forcename: str
                A specific force's name belonging to any nation
        """

        await handle_interaction(interaction.client, interaction, infoactions.force, forcename)

    @app_commands.command()
    async def units(self, interaction):
        """Show all of the available units in the given server's game."""

        await handle_interaction(interaction.client, interaction, infoactions.force)


    # Population Information

    @app_commands.command()
    async def population(self, interaction, role: discord.Role = None, territory: str = None):
        """Show all of the populations in a nation or a territory

        Parameters
        -----------
            role (optional): discord.Role
                The nation role.

            territory (optional): str
                The territory name or ID.
        """

        await handle_interaction(interaction.client, interaction, infoactions.population, role.id if role else None, territory)

    @app_commands.command()
    async def population_info(self, interaction):
        """Show all of the population identifiers in the given server's gamerule."""

        await handle_interaction(interaction.client, interaction, infoactions.population_info)
        

async def setup(client):

    await client.add_cog(InfoCommands(client))