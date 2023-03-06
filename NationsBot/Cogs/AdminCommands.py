import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

import GameUtils.Operations as ops
from DiscordUtils.GetGameInfo import *

from ConcertOfNationsEngine.GameHandling import *
from ConcertOfNationsEngine.CustomExceptions import *

#The cog itself
class AdminCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client

    # Manage nations

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def giveTerritory(self, ctx, roleid, territoryName, **args):
        """
        Give a territory to a nation and take it away from its previous owner, if any.
        """
        logInfo(f"giveTerritory({ctx.guild.id}, {roleid}, {territoryName}, {args})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        nation = get_NationFromRole(ctx, roleid, savegame)
        if not (nation): 
            return #Error will already have been handled

        try: savegame.transfer_territory(territoryName, nation)
        except Exception as e: raise e

        logInfo(f"Successfully transferred the territory {territoryName} to {nation.name}")
        await ctx.send(f"Successfully transferred the territory {territoryName} to {nation.name}")

        save_saveGame(savegame)

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def giveResources(self, ctx, roleid, *args):
        """
        Give a specified amount of any resources to a specified nation.
        
        Args:
            *args (tuple): A list of resources and numbers. Example:
            ("Iron", "2", "Money", "3")
        """

        logInfo(f"giveResources({ctx.guild.id}, {roleid}, {args})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        nation = get_NationFromRole(ctx, roleid, savegame)
        if not (nation): 
            return #Error will already have been handled

        if len(args) < 1:
            raise InputError("Not enough args!")

        elif (len(args) % 2 != 0):
            raise InputError("Odd number of args")

        #Get and validate resources
        resources_toadd = {args[n*2]: args[(n*2)+1] for n in range(int(len(args)/2))}

        for k, v in resources_toadd.items():
            
            if not(k in savegame.getGamerule()["Resources"] + ["Money"]):
                raise InputError(f"\"{k}\" is not a resource")

            if not (ops.isInt(v)):
                raise InputError(f"\"{v}\" is not a valid amount of resources")

            else:
                resources_toadd[k] = int(v)

        logInfo(f"Adding resources to {nation.name}", details = resources_toadd)

        nation.resources = ops.combineDicts(nation.resources, resources_toadd)

        logInfo(f"Successfully added resources", details = nation.resources)
        await ctx.send(f"Successfully added resources, type \"_n.nationinfo {roleid}_\" to view changes")

        save_saveGame(savegame)


    # Manage the savegame

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def advanceTurn(self, ctx, numMonths = None):
        """Advance the turn for the current server's savegame, optionally by a number of months"""
        
        if not numMonths: numMonths = 1

        logInfo(f"advanceTurn({ctx.guild.id}, {numMonths})")
        
        if (type(numMonths) == str):
            if not(numMonths.isdigit()):
                raise InputError(f"Invalid number of months \'{numMonths}\'")

        numMonths = int(numMonths)

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        savegame.advanceTurn(numMonths)

        await ctx.send(f"Advanced turn to turn {savegame.turn}, new date is {savegame.date['m']}/{savegame.date['y']}!")

        save_saveGame(savegame)

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def addNation(self, ctx, roleid, playerid):
        """
        Add a nation (by role) and player to a savegame.

        Args:
            roleid(str): 
        """

        logInfo(f"addNation({ctx.guild.id}, {roleid}, {playerid})")

        #Get savegame info from database
        try:
            savegame = FileHandling.loadObject(load_saveGame(dbget_saveGame_byServer(ctx.guild.id)["savefile"]))
        except Exception as e:
            raise InputError("Could not load a game for this server.")
            return

        role = ctx.guild.get_role(get_RoleID(roleid))
        player = ctx.guild.get_member(get_PlayerID(playerid))

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
    @commands.has_permissions(administrator = True)
    async def initGame(self, ctx, name, date):
        """
        Called in a server without an attached game to initialize a game
        """

        logInfo(f"initGame({ctx.guild.id}, {name}, {date})")

        try: month, year = (int(x) for x in re.split(r'[,/\\]', date))
        except:
            raise InputError("Could not parse the date. Please write in one of the following formats without spaces: \n> monthnumber,yearnumber\n> monthnumber/yearnumber")
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
        except CustomException as e:
            raise e
            return
        except Exception as e:
            raise NonFatalError("Something went wrong when initializing the savegame.")
            return

        logInfo(f"Successfully created savegame {savegame.name} for server {ctx.guild.id}")
        await ctx.send(f"Successfully initialized game \"{savegame.name}\" at date {savegame.date} and turn {savegame.turn} for this server!")

        save_saveGame(savegame)

        
async def setup(client):
    await client.add_cog(AdminCommands(client))