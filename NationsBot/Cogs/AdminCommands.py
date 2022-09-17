import json, datetime, pprint, traceback

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from ConcertOfNationsEngine.GameHandling import *

#The cog itself
class AdminCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        

    @commands.command()
    async def test_admincommands(self, ctx, roleid, player, **args):
        await ctx.send("Test!")

    @commands.command()
    async def addNation(self, ctx, roleid, playerid, **args):
        """
        Add a nation (by role) and player to a savegame.
        """

        try:
            savegame = FileHandling.loadObject(load_saveGame(dbget_saveGame_byServer(ctx.guild.id)["savefile"]))
        except Exception as e:
            logInfo("Could not load a game for this server.")
            logError(e)
            await ctx.send("Could not load a game for this server.")
            return

        role = ctx.guild.get_role(int(roleid[3:-1]))
        player = ctx.guild.get_member(int(playerid[2:-1]))

        logInfo(f"Adding nation {role.name} to saveGame")

        try:
            savegame.add_Nation(Nation(role.name, role.id, (role.color.r, role.color.g, role.color.b)))
        except Exception as e:
            logError(e, {"Message": "Could not add nation to savegame"})
            await ctx.send(f"Could not add {roleid}: {str(e)}")
            return

        try:
            add_Nation(
                savegame, 
                savegame.nations[role.name], 
                player.id
                )
        except Exception as e:
            logError(e, {"Message": f"Could not add nation to database"})
            await ctx.send(f"Could not add {roleid}: {str(e)}")
            return

        logInfo(f"Successfully added nation:", FileHandling.saveObject(savegame))

        save_saveGame(savegame)

        await ctx.send(f"Added {roleid} to this game!")

        
def setup(client):
    client.add_cog(AdminCommands(client))