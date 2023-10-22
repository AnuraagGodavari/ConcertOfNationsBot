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
    """ Commands for players to manage their military forces """

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

    @commands.command(aliases=['splitunit', 'split-unit', 'splitUnit'])
    async def split_unit(self, ctx, base_forcename, base_unitname, *new_unitsizes):
        """ Split a unit of a given nation into multiple new ones. """
        logInfo(f"split_unit({ctx.guild.id}, {base_forcename}, {base_unitname}, {new_unitsizes})")

        if (len(new_unitsizes) < 1):
            raise InputError(f"Must have at least one new unit size")

        for unitsize in new_unitsizes:
            if not (ops.isPositiveInt(unitsize)):
                raise InputError(f"Invalid unit size {unitsize}, must be positive integer")

        new_unitsizes = [int(unitsize) for unitsize in new_unitsizes]

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

        baseForce = nation.military[base_forcename]

        if not (base_unitname in baseForce["Units"].keys()):
            raise InputError(f"Unit: {base_unitname} does not exist in Force: {base_forcename}")

        unit = baseForce["Units"][base_unitname]

        if not(military.unit_splittable(unit, *new_unitsizes)):
            raise InputError("Could not split unit")

        military.split_unit_inForce(nation, baseForce, unit, *new_unitsizes)

        await ctx.send(f"Force \"{base_forcename}\" has split unit {base_unitname} into new units with sizes: {new_unitsizes}. Use n.force \"{base_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['splitforce', 'split-force', 'splitForce'])
    async def split_force(self, ctx, base_forcename, *units_toSplit):
        """ Split a force belonging to a nation, transferring several units to the new force """
        logInfo(f"split_force({ctx.guild.id}, {base_forcename}, {units_toSplit})")

        if (len(units_toSplit) < 1):
            raise InputError(f"Must have at least one unit to transfer")

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

        baseForce = nation.military[base_forcename]

        if not(military.force_splittable(baseForce, *units_toSplit)):
            raise InputError("Could not split force")

        new_forcename = military.split_force(nation, baseForce, *units_toSplit)

        await ctx.send(f"Force \"{base_forcename}\" has been split into new force {new_forcename} and transferred the units: {units_toSplit}. Use n.force \"{new_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['disbandunits', 'disband-units', 'disbandUnits'])
    async def disband_units(self, ctx, base_forcename, *units_toDisband):
        """ Disband units in a given force, returning their manpower to their home provinces. """
        logInfo(f"disband_units({ctx.guild.id}, {base_forcename}, {units_toDisband})")

        if (len(units_toDisband) < 1):
            raise InputError(f"Must have at least one unit to disband")

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

        baseForce = nation.military[base_forcename]

        if [unitname for unitname in units_toDisband if unitname not in baseForce["Units"]]:
            raise InputError(f"Units do not all exist in force {base_forcename}")

        military.disband_units_inForce(nation, baseForce, units_toDisband)
        
        if not(baseForce["Units"]):
            nation.military.pop(base_forcename)

        await ctx.send(f"Disbanded units: {units_toDisband}. Use n.force \"{base_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['disbandforce', 'disband-force', 'disbandForce'])
    async def disband_force(self, ctx, base_forcename):
        """ Disband a given force, returning its units' manpowers to their home provinces. """
        logInfo(f"disband_units({ctx.guild.id}, {base_forcename})")

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

        military.disband_force(nation, base_forcename)

        await ctx.send(f"Disbanded force: {base_forcename}. Use n.force \"{base_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['moveforce', 'move-force', 'moveForce'])
    async def move_force(self, ctx, base_forcename, *terrIDs):
        """ Order a given force to start moving to a series of territories """
        logInfo(f"move_force({ctx.guild.id}, {base_forcename}, {terrIDs})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        gamerule = savegame.getGamerule()

        if not (gamerule):
            raise InputError("Savegame's gamerule could not be retrieved")

        territories = list()

        for terrID in terrIDs:

            if terrID.isdigit(): terrID = int(terrID)

            #Territory info from the map
            world_terr = world[terrID]

            if not world_terr:
                raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

            territories.append(world_terr.name)

        #Validate that the player owns these forces
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        path = military.setmovement_force(nation, base_forcename, world, gamerule, savegame, *territories)

        if (path):
            await ctx.send(f"Force {base_forcename} has begun moving. Path: {[territory['Name'] for territory in path]}")

        else:
            await ctx.send(f"Could not move {base_forcename}")

        save_saveGame(savegame)



async def setup(client):
    await client.add_cog(MilitaryCommands(client))