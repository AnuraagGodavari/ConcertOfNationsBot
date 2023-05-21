import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

import GameUtils.operations as ops
from DiscordUtils.getgameinfo import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *

from ConcertOfNationsEngine.dateoperations import *

from ConcertOfNationsEngine.buildings import *
import ConcertOfNationsEngine.territories as territories
import ConcertOfNationsEngine.populations as populations

#The cog itself
class AdminCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client


    # Manage buildings

    @commands.command(aliases = ["giveBuilding", "give-buildng", "givebuilding"])
    @commands.has_permissions(administrator = True)
    async def give_building(self, ctx, terrID, buildingName, **args):
        """ """
        logInfo(f"n.givebuilding({ctx.guild.id}, {terrID}, {buildingName})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        territoryName = world_terrInfo.name
        
        #Get nation info
        nationName = savegame.find_terrOwner(territoryName)
        if not (nationName): 
            raise InputError("Territory is unowned and cannot have a building placed in it.")
        nation = savegame.nations[nationName]

        #Put building in territory
        if (buildingName in nation.territories[territoryName]["Buildings"]):
            raise InputError(f"{buildingName} already exists in {territoryName}")

        if not (buildingName in get_allbuildings(savegame)):
            raise InputError(f"Building {buildingName} does not exist")

        nation.territories[territoryName]["Buildings"][buildingName] = "Active"

        nation.add_buildingeffects(buildings.get_alleffects(buildingName, savegame))

        await ctx.send(f"Successfully added {buildingName} to {territoryName}!")

        save_saveGame(savegame)
    
    @commands.command(aliases = ["changebuildingstatus", "change-buildingstatus"])
    @commands.has_permissions(administrator = True)
    async def change_buildingstatus(self, ctx, terrID, buildingName, newstatus):
        """ Change the status of any building """
        logInfo(f"change_buildingstatus({ctx.guild.id}, {terrID}, {buildingName}, {newstatus})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        territoryName = world_terrInfo.name

        #Get nation info
        nationName = savegame.find_terrOwner(territoryName)
        if not (nationName): 
            raise InputError("Territory is unowned and does not have this building")
        nation = savegame.nations[nationName]

        if (territoryName not in nation.territories.keys()):
            raise InputError(f"Nation {nation.name} does not own territory \"{territoryName}\"")

        newstatus = territories.newbuildingstatus(nation, territoryName, buildingName, newstatus, savegame)

        await ctx.send(f"New building status: {newstatus}")

        save_saveGame(savegame)
        
    @commands.command(aliases = ["takebuilding", "take-building", "removebuilding", "remove_building", "remove-building"])
    @commands.has_permissions(administrator = True)
    async def take_building(self, ctx, terrID, buildingName):
        """ Remove a building from any territory """
        logInfo(f"take_building({ctx.guild.id}, {terrID}, {buildingName})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        territoryName = world_terrInfo.name

        #Get nation info
        nationName = savegame.find_terrOwner(territoryName)
        if not (nationName): 
            raise InputError("Territory is unowned and does not have this building")
        nation = savegame.nations[nationName]

        #Can we do the operation on this territory

        if (not territories.hasbuilding(nation, territoryName, buildingName)):
            raise InputError(f"Territory {territoryName} does not have building {buildingName}")

        newstatus = territories.destroybuilding(nation, territoryName, buildingName)

        nation.remove_buildingeffects(buildings.get_alleffects(buildingName, savegame))

        await ctx.send(f"Building {buildingName} has successfully been deleted from territory {territoryName}")

        save_saveGame(savegame)


    # Manage population

    @commands.command(aliases = ["changePopulation", "changepopulation", "add_population", "addPopulation", "addpopulation"])
    @commands.has_permissions(administrator = True)
    async def change_population(self, ctx, terrID, size: int, occupation, *identifiers):
        """ Change the size of an existing population or add a new one """
        logInfo(f"change_population({ctx.guild.id}, {terrID}, {size}, {occupation}, {identifiers})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        gamerule = savegame.getGamerule()
        if not (gamerule):
            raise InputError("Savegame's gamerule could not be retrieved")

        identifiers = populations.identifiers_list_toDict(gamerule, *identifiers)

        #If no error thrown, then we can continue
        populations.validate_population(gamerule, size, occupation, identifiers)

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        territoryName = world_terrInfo.name

        #Get nation info
        nationName = savegame.find_terrOwner(territoryName)
        if not (nationName): 
            raise InputError("Territory is unowned and does not have this building")
        nation = savegame.nations[nationName]

        #Add population if doesn't exist
        if not (territories.get_population(nation, territoryName, occupation, identifiers)):
            if size == 0:
                raise InputError("Cannot delete a population that does not already exist")
            logInfo("Specified population does not exist, adding new population")
            pop = territories.add_population(nation, territoryName, populations.Population(size, gamerule["Base Population Growth"], occupation, identifiers))

        #Delete the population if size is 0
        elif size == 0:
            logInfo("Specified population exists and will be deleted")
            pop = territories.remove_population(nation, territoryName, occupation, identifiers)
            
        #Else, change the population size
        else:
            pop = territories.change_population(nation, territoryName, size, occupation, identifiers)

        if not (pop):
            raise InputError(f"Changing population failed")

        await ctx.send(f"Population {' '.join(list(pop.identifiers.values())) + ' ' + pop.occupation} in {territoryName} now has size {size}")

        save_saveGame(savegame)

    @commands.command(aliases = ["changePopulationGrowth", "changePopulationgrowth","changepopulationGrowth", "changepopulationgrowth", "changepopulation_growth", "change_populationgrowth"])
    @commands.has_permissions(administrator = True)
    async def change_population_growth(self, ctx, terrID, growthrate: int | float, occupation, *identifiers):
        """ Change the size of an existing population or add a new one """
        logInfo(f"change_population({ctx.guild.id}, {terrID}, {growthrate}, {occupation}, {identifiers})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        gamerule = savegame.getGamerule()
        if not (gamerule):
            raise InputError("Savegame's gamerule could not be retrieved")

        identifiers = populations.identifiers_list_toDict(gamerule, *identifiers)

        #If no error thrown, then we can continue
        populations.validate_population(gamerule, 1, occupation, identifiers, growth = growthrate)

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        territoryName = world_terrInfo.name

        #Get nation info
        nationName = savegame.find_terrOwner(territoryName)
        if not (nationName): 
            raise InputError("Territory is unowned and does not have this building")
        nation = savegame.nations[nationName]

        #Add population if doesn't exist
        if not (territories.get_population(nation, territoryName, occupation, identifiers)):
            raise InputError("Cannot change growth rate for a population that does not already exist")

        pop = territories.change_populationgrowth(nation, territoryName, growthrate, occupation, identifiers)

        if not (pop):
            raise InputError(f"Changing population growth rate failed")

        await ctx.send(f"Population {' '.join(list(pop.identifiers.values())) + ' ' + pop.occupation} in {territoryName} now has growth rate {growthrate}")

        save_saveGame(savegame)


    # Manage nations

    @commands.command(aliases = ["giveTerritory", "give-territory", "giveterritory"])
    @commands.has_permissions(administrator = True)
    async def give_territory(self, ctx, roleid, terrID, **args):
        """
        Give a territory to a nation and take it away from its previous owner, if any.
        """
        logInfo(f"giveTerritory({ctx.guild.id}, {roleid}, {terrID}, {args})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        nation = get_NationFromRole(ctx, roleid, savegame)
        

        transferred_terr =  savegame.transfer_territory(terrID, nation)
        if not transferred_terr:
            raise InputError(f"Territory {terrID} transfer to {nation.name} did not work")

        logInfo(f"Successfully transferred the territory {terrID} to {nation.name}")
        await ctx.send(f"Successfully transferred the territory {terrID} to {nation.name}")

        save_saveGame(savegame)

    @commands.command(aliases = ["giveResources", "give-resources", "giveresources"])
    @commands.has_permissions(administrator = True)
    async def give_resources(self, ctx, roleid, *args):
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

    @commands.command(aliases = ["changeCapacity", "change-capacity", "changecapacity", "change_bureaucracy", "changeBureaucracy", "change-bureaucracy", "changebureaucracy"])
    @commands.has_permissions(administrator = True)
    async def change_capacity(self, ctx, roleid, category, amount):
        """ Change the bureaucratic capacity for any category of a specific nation's bureaucracy """

        logInfo(f"change_capacity({ctx.guild.id}, {roleid}, {category}, {amount})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        nation = get_NationFromRole(ctx, roleid, savegame)
        

        if not(category in nation.bureaucracy.keys()):
            raise InputError(f"No such bureaucratic category \"{category}\"")

        if (amount.startswith('-') or not (ops.isInt(amount))):
            raise InputError(f"{category} capacity cannot have value \"{amount}\"")

        logInfo(f"Changing bureaucratic capacity for {nation.name} for category {category} from {nation.bureaucracy[category]} to {amount}")

        nation.bureaucracy[category] = (nation.bureaucracy[category][0], int(amount))

        logInfo(f"Successfully changed national bureaucracy", details = nation.bureaucracy)
        await ctx.send(f"Successfully changed bureaucratic capacity for {category} category to {amount}, type \"_n.nationinfo {roleid}_\" to view changes")


    # Manage the savegame

    @commands.command(aliases = ["advanceTurn", "advanceturn", "advance-turn"])
    @commands.has_permissions(administrator = True)
    async def advance_turn(self, ctx, numMonths = None):
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

    @commands.command(aliases = ["addNation", "add-nation", "addnation"])
    @commands.has_permissions(administrator = True)
    async def add_nation(self, ctx, roleid, playerid):
        """
        Add a nation (by role) and player to a savegame.

        Args:
            roleid(str): 
        """

        logInfo(f"addNation({ctx.guild.id}, {roleid}, {playerid})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        role = ctx.guild.get_role(get_RoleID(roleid))
        player = ctx.guild.get_member(get_PlayerID(playerid))

        logInfo(f"Adding nation {role.name} to savegame")

        #Try adding the nation to the savegame

        nation = Nation(role.name, role.id, (role.color.r, role.color.g, role.color.b))
        nation = savegame.add_Nation(nation)

        if not (nation):
            logInfo(f"Did not add nation {roleid} to savegame file; already exists")

        #Try adding the nation to the database - including player, role, and playergame tables
        db_nation = add_Nation(
                savegame, 
                savegame.nations[role.name], 
                player.id
                )
        
        if not db_nation:
            raise InputError(f"Could not add nation {roleid} with player {playerid} to the database")

        logInfo(f"Successfully added nation:", filehandling.saveObject(savegame))

        save_saveGame(savegame)

        await ctx.send(f"Added {roleid} to this game!")

    @commands.command(aliases = ["initgame", "initGame", "init-game"])
    @commands.has_permissions(administrator = True)
    async def init_game(self, ctx, name, datestr):
        """
        Called in a server without an attached game to initialize a game
        """

        logInfo(f"initGame({ctx.guild.id}, {name}, {datestr})")

        try: month, year = (int(x) for x in re.split(r'[,/\\]', datestr))
        except:
            raise InputError("Could not parse the date. Please write in one of the following formats without spaces: \n> monthnumber,yearnumber\n> monthnumber/yearnumber")

        date = {"m": month, "y": year}

        if not (date_validate(date)):
            raise InputError(f"Invalid date \"{datestr}\"")

        savegame = Savegame(
            name,
            ctx.guild.id,
            date,
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
            raise NonFatalError("Something unexpected went wrong when initializing the savegame.")
            return

        logInfo(f"Successfully created savegame {savegame.name} for server {ctx.guild.id}")
        await ctx.send(f"Successfully initialized game \"{savegame.name}\" at date {savegame.date} and turn {savegame.turn} for this server!")

        save_saveGame(savegame)

        
async def setup(client):
    await client.add_cog(AdminCommands(client))