import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

from common import *
from database import *
from logger import *
from constants import *

from GameUtils import operations as ops
import GameUtils.playerutils as playerutils

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *
from DiscordUtils.flexiblecommands import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
import ConcertOfNationsEngine.buildings
import ConcertOfNationsEngine.territories as territories

from Actions import buildingactions

#The cog itself
class BuildingCommands(commands.Cog):
    """ Commands for players to manage buildings they own """
    
    def __init__(self, client):
        self.client = client

    # Building Actions

    @app_commands.command()
    async def buy_building(self, interaction, terrid: str, buildingname: str):
        """ As a nation, this is an order to expend resources to purchase a building.
        
        Args:
            terrid: The name or numeric ID of the territory
            buildingname: The name of the building you wish to build
        """
        await handle_interaction(interaction.client, interaction, buildingactions.buyBuilding, terrid, buildingname)

    @app_commands.command()
    async def toggle_building(self, interaction, terrid: str, buildingname: str, buildingindex: int):
        """Switch a building's status between Active and Inactive

        Args:
            terrID: The name or numeric ID of the territory
            buildingName: The name of the building you wish to toggle
            buildingIndex: Which building you want to access, starting with 0
        """
        await handle_interaction(interaction.client, interaction, buildingactions.toggleBuilding, terrid, buildingname, buildingindex)

    @app_commands.command()
    async def destroy_building(self, interaction, terrid: str, buildingname: str, buildingindex: int):
        """ Remove a building from a territory owned by the user

        Args:
            terrID: The name or numeric ID of the territory
            buildingName: The name of the building you wish to remove
            buildingIndex: Which building you want to access, starting with 0
        """
        await handle_interaction(interaction.client, interaction, buildingactions.destroyBuilding, terrid, buildingname, buildingindex)


    # Building Information

    @app_commands.command()
    async def buildings(self, interaction):
        """ Show all of the available buildings in the given server's game."""

        await handle_interaction(interaction.client, interaction, buildingactions.buildings)



async def setup(client):
    await client.add_cog(BuildingCommands(client))