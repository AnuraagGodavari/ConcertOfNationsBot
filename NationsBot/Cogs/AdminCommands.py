import json, datetime, pprint, traceback, re

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
    async def giveTerritory(self, ctx, roleid, territoryName, **args):
        """
        Give a territory to a nation and take it away from its previous owner, if any.
        """
        pass

        #Check if territory name exists

        #Check if territory is owned, remove it

        #Add this territory to the nation

    @commands.command()
    async def addNation(self, ctx, roleid, playerid):
        """
        Add a nation (by role) and player to a savegame.
        """

        logInfo(f"addNation({ctx.guild.id}, {roleid}, {playerid})")

        #Get savegame info from database
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

        #Try adding the nation to the savegame
        try:
            savegame.add_Nation(Nation(role.name, role.id, (role.color.r, role.color.g, role.color.b)))
        except Exception as e:
            logError(e, {"Message": "Could not add nation to savegame"})
            await ctx.send(f"Could not add {roleid}: {str(e)}")
            return

        #Try adding the nation to the database - including player, role, and playergame tables
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

    @commands.command()
    async def initGame(self, ctx, name, date):
        """
        Called in a server without an attached game to initialize a game
        """

        logInfo(f"initGame({ctx.guild.id}, {name}, {date})")

        try: month, year = (int(x) for x in re.split(r'[,/\\]', date))
        except:
            await ctx.send("Could not parse the date. Please write in one of the following formats without spaces: \n> monthnumber,yearnumber\n> monthnumber/yearnumber")
            return

        savegame = Savegame(
            name,
            ctx.guild.id,
            {"m": month, "y": year},
            1
        )
        
        try:
            setupNew_saveGame(
                savegame, 
                "Test World", 
                "Test Gamerule"
                )
        except Exception as e:
            logInfo("Savegame already in database")
            await ctx.send("This server already has a game assigned to it")
            return

        logInfo(f"Successfully created savegame {savegame.name} for server {ctx.guild.id}")
        await ctx.send(f"Successfully initialized game \"{savegame.name}\" at date {savegame.date} and turn {savegame.turn} for this server!")

        
def setup(client):
    client.add_cog(AdminCommands(client))