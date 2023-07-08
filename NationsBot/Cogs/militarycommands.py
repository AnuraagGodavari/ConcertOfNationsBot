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
import ConcertOfNationsEngine.military as military

from GameUtils.filehandling import *
import GameUtils.operations as ops

#The cog itself
class MilitaryCommands(commands.Cog):
    """ A cog for player commands related to the military """

    # Manpower

    @commands.command(aliases=['raiseManpower', 'raise-manpower', 'raisemanpower'])
    async def raise_manpower(self, ctx, terrID, amount):
        """ Raise manpower in a given territory. """
        logInfo(f"raise_manpower({ctx.guild.id}, {terrID}, {amount})")

        if not (ops.isPositiveInt(amount)):
            raise InputError(f"Invalid amount {amount}, must be positive integer")

        amount = int(amount)

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terr = world[terrID]

        if not world_terr:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

        territoryName = world_terr.name

        #Validate that the player owns this territory
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (territoryName in nation.territories.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the territory {territoryName}")

        total_pop = territories.get_totalpopulation(nation, territoryName)

        if (total_pop <= 0):
            raise InputError("Manpower cannot be raised from this territory because it has no population")

        if (territories.get_manpower(nation, territoryName) + amount > total_pop):
            raise InputError(f"Cannot raise {amount} manpower because it exceeds total ummobilized population of {total_pop}")

        territories.recruit_manpower(nation, territoryName, amount)

        logInfo(f"Successfully raised {amount} manpower in territory {territoryName}")
        await ctx.send(f"Successfully raised {amount} manpower in territory {territoryName}")

        save_saveGame(savegame)

    @commands.command(aliases=['disbandManpower', 'disband-manpower', 'disbandmanpower'])
    async def disband_manpower(self, ctx, terrID, amount):
        """ Disband manpower in a given territory. """
        logInfo(f"disband_manpower({ctx.guild.id}, {terrID}, {amount})")

        if not (ops.isPositiveInt(amount)):
            raise InputError(f"Invalid amount {amount}, must be positive integer")

        amount = int(amount)

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terr = world[terrID]

        if not world_terr:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

        territoryName = world_terr.name

        #Validate that the player owns this territory
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (territoryName in nation.territories.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the territory {territoryName}")

        total_pop = territories.get_totalpopulation(nation, territoryName)

        if (total_pop <= 0):
            raise InputError("Manpower cannot be disbanded from this territory because it has no population")

        manpower = territories.get_manpower(nation, territoryName)

        if (manpower < amount):
            raise InputError(f"Cannot disband {amount} manpower because it exceeds total manpower {manpower}")

        territories.disband_manpower(nation, territoryName, amount)

        logInfo(f"Successfully disbanded {amount} manpower in territory {territoryName}")
        await ctx.send(f"Successfully disbanded {amount} manpower in territory {territoryName}")

        save_saveGame(savegame)


    # Force management

    @commands.command(aliases=['buildUnit', 'build-unit', 'buildunit'])
    async def build_unit(self, ctx, terrID, unitType, amount):
        """ Disband manpower in a given territory. """
        logInfo(f"build_unit({ctx.guild.id}, {terrID}, {unitType}, {amount})")

        if not (ops.isPositiveInt(amount)):
            raise InputError(f"Invalid amount {amount}, must be positive integer")

        amount = int(amount)

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terr = world[terrID]

        if not world_terr:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

        territoryName = world_terr.name

        #Validate that the player owns this territory
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (territoryName in nation.territories.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the territory {territoryName}")

        gamerule = savegame.getGamerule()

        blueprint = military.get_blueprint(unitType, gamerule)

        if not (nation.can_build_unit(savegame, territoryName, unitType, blueprint, amount)):
            raise InputError(f"Could not build {unitType} for {nation.name} in {territoryName}")

        newforcename = nation.build_unit(territoryName, unitType, amount, blueprint, savegame)
        newforce = nation.military[newforcename]

        await ctx.send(f"New force \"{newforcename}\" created in territory {territoryName} with status of {newforce['Status']}")

        save_saveGame(savegame)

    @commands.command(aliases=['combineforces', 'combine-forces', 'combineForces'])
    async def combine_forces(self, ctx, base_forcename, *additional_forcenames):
        """ Combine multiple forces of a given nation. """
        logInfo(f"combine_forces({ctx.guild.id}, {base_forcename}, {additional_forcenames})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        #Validate that the player owns these forces
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        for forcename in additional_forcenames:
            if not (forcename in nation.military.keys()):
                raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the force {forcename}.  If a name has spaces, use quotation marks like this: \"name of force\"")

        base_force = nation.military[base_forcename]
        additional_forces = [nation.military[forcename] for forcename in additional_forcenames]

        if not(military.forces_addable(base_force, *additional_forces)):
            raise InputError("Could not combine these forces. Check if they have the same statuses, locations and types.")

        additional_forces = [nation.pop_force(forcename) for forcename in additional_forcenames]

        combined_force = military.combine_forces(base_force, *additional_forces)

        await ctx.send(f"Force \"{base_forcename}\" has merged with the following forces: {additional_forcenames}")

        save_saveGame(savegame)

    @commands.command(aliases=['combineunits', 'combine-units', 'combineUnits'])
    async def combine_units(self, ctx, base_forcename, base_unitname, *additional_unitnames):
        """ Combine multiple units of a given nation. """
        logInfo(f"combine_units({ctx.guild.id}, {base_forcename}, {base_unitname}, {additional_unitnames})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        #Validate that the player owns these forces
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        base_force = nation.military[base_forcename]

        if not (base_unitname in base_force["Units"].keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> force {base_forcename} does not contain a unit named {base_unitname}.")

        for unitname in additional_unitnames:
            if not (unitname in base_force["Units"].keys()):
                raise InputError(f"<@&{playerinfo['role_discord_id']}> force {base_forcename} does not contain a unit named {unitname}.")

        base_unit = base_force["Units"][base_unitname]
        additional_units = [base_force["Units"][unitname] for unitname in additional_unitnames]

        if not(military.units_addable(base_unit, *additional_units)):
            raise InputError("Could not combine units")
        
        military.combine_units_inForce(base_force, base_unit, *additional_units)

        await ctx.send(f"Force \"{base_forcename}\" has merged unit {base_unitname} with the following units: {additional_unitnames}")

        save_saveGame(savegame)


async def setup(client):
    await client.add_cog(MilitaryCommands(client))