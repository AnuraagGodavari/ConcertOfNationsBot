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
import ConcertOfNationsEngine.diplomacy as diplomacy

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
            pop = territories.add_population(nation, territoryName, populations.Population(size, 0, occupation, identifiers))

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

    @commands.command(aliases = ["changePopulationGrowth", "changePopulationgrowth","changepopulationGrowth", "changepopulationgrowth", "changepopulation_growth", "change_populationgrowth", "populationgrowth", "populationGrowth", "population-growth"])
    @commands.has_permissions(administrator = True)
    async def change_population_growth(self, ctx, terrID, growthrate: int | float, occupation, *identifiers):
        """ Change the growth rate modifier of an existing population """
        logInfo(f"change_population_growth({ctx.guild.id}, {terrID}, {growthrate}, {occupation}, {identifiers})")

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

        await ctx.send(f"Population {' '.join(list(pop.identifiers.values())) + ' ' + pop.occupation} in {territoryName} now has growth rate modifier {growthrate}")

        save_saveGame(savegame)

    @commands.command(aliases = ["changeManpower", "change-manpower", "changemanpower"])
    @commands.has_permissions(administrator = True)
    async def change_manpower(self, ctx, terrID, amount):
        """ Manually raise manpower in a given territory. """
        logInfo(f"change_manpower({ctx.guild.id}, {terrID}, {amount})")

        if not (ops.isInt(amount)):
            raise InputError(f"Invalid amount {amount}, must be integer")

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

        nationName = savegame.find_terrOwner(territoryName)
        if not (nationName): 
            raise InputError("Territory is unowned and cannot have manpower changed for it.")
        nation = savegame.nations[nationName]

        total_pop = territories.get_totalpopulation(nation, territoryName)

        #If change amount is positive, raise manpower

        if (amount > 0):

            if (total_pop <= 0):
                raise InputError("Manpower cannot be raised from this territory because it has no population")

            if (territories.get_manpower(nation, territoryName) + amount > total_pop):
                raise InputError(f"Cannot raise {amount} manpower because it exceeds total ummobilized population of {total_pop}")

            territories.recruit_manpower(nation, territoryName, amount)

        #If change amount is negative, disband manpower

        elif (amount < 0):

            amount = abs(amount)

            if (total_pop <= 0):
                raise InputError("Manpower cannot be disbanded from this territory because it has no population")

            manpower = territories.get_manpower(nation, territoryName)

            if (manpower < amount):
                raise InputError(f"Cannot disband {amount} manpower because it exceeds total manpower {manpower}")

            territories.disband_manpower(nation, territoryName, amount)

        logInfo(f"Successfully changed manpower in territory {territoryName} to {territories.get_manpower(nation, territoryName)}")
        await ctx.send(f"Successfully changed manpower in territory {territoryName} to {territories.get_manpower(nation, territoryName)}")

        save_saveGame(savegame)
    
    @commands.command(aliases = ["editManpower", "edit-manpower", "editmanpower"])
    @commands.has_permissions(administrator = True)
    async def edit_manpower(self, ctx, terrID, amount):
        """ Edit the raw manpower number in any given territory. """
        logInfo(f"change_manpower({ctx.guild.id}, {terrID}, {amount})")

        if not (ops.isInt(amount)):
            raise InputError(f"Invalid amount {amount}, must be integer")

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

        nationName = savegame.find_terrOwner(territoryName)
        if not (nationName): 
            raise InputError("Territory is unowned and cannot have manpower changed for it.")
        nation = savegame.nations[nationName]

        total_pop = territories.get_totalpopulation(nation, territoryName)

        #If change amount is positive, raise manpower

        if (amount > 0):

            if (total_pop <= 0):
                raise InputError("Manpower cannot be raised from this territory because it has no population")

            if (territories.get_manpower(nation, territoryName) + amount > total_pop):
                raise InputError(f"Cannot raise {amount} manpower because it exceeds total ummobilized population of {total_pop}")

            nation.get_territory(territoryName)["Manpower"] += amount

        #If change amount is negative, disband manpower

        elif (amount < 0):

            amount = abs(amount)

            if (total_pop <= 0):
                raise InputError("Manpower cannot be disbanded from this territory because it has no population")

            manpower = territories.get_manpower(nation, territoryName)

            if (manpower < amount):
                raise InputError(f"Cannot disband {amount} manpower because it exceeds total manpower {manpower}")

            nation.get_territory(territoryName)["Manpower"] -= amount

        logInfo(f"Successfully changed manpower in territory {territoryName} to {territories.get_manpower(nation, territoryName)}")
        await ctx.send(f"Successfully changed manpower in territory {territoryName} to {territories.get_manpower(nation, territoryName)}")

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

    @commands.command(aliases = ["changeTax", "change-tax", "changetax"])
    @commands.has_permissions(administrator = True)
    async def change_tax(self, ctx, roleid, amount):
        """ Change a nation's national tax modifier """

        logInfo(f"change_capacity({ctx.guild.id}, {roleid}, {amount})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (ops.isFloat(amount)):
            raise InputError(f"Tax modifier cannot have value \"{amount}\"")

        logInfo(f"Changing tax modifier for {nation.name} from {nation.modifiers['Tax']} to {amount}")

        nation.modifiers['Tax'] = float(amount)

        logInfo(f"Successfully changed national tax modifier to {nation.modifiers['Tax']}")
        await ctx.send(f"Successfully changed national tax modifier to {nation.modifiers['Tax']}, type \"_n.nationinfo {roleid}_\" to view changes")


    # Manage military

    @commands.command(aliases=['admincreateforce', 'admin-create-force', 'adminCreateForce'])
    @commands.has_permissions(administrator = True)
    async def admin_give_unit(self, ctx, roleid, terrID, unitType, amount):
        """ Manually give a unit to a given nation with no cost. """
        logInfo(f"admin_give_unit({ctx.guild.id}, {roleid}, {terrID}, {unitType}, {amount})")

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

        nation = get_NationFromRole(ctx, roleid, savegame)

        gamerule = savegame.getGamerule()

        blueprint = military.get_blueprint(unitType, gamerule)

        #Manually create and place the unit
        unitName = military.new_unitName(nation.military, name_template = f"{nation.name} {territoryName} {unitType}")
        newunit = military.Unit(unitName, f"Active", unitType, amount, territoryName)

        newforcename = military.new_forceName([name for nation in savegame.nations.values() for name in nation.military.keys()], name_template = f"{nation.name} Force")
        nation.military[newforcename] = {
            "Status": "Active",
            "Location": territoryName,
            "Units": {unitName: newunit}
        }
        newforce = nation.military[newforcename]

        await ctx.send(f"New force \"{newforcename}\" created in territory {territoryName} with status of {newforce['Status']}")

        save_saveGame(savegame)

    @commands.command(aliases = ["changeforcestatus", "change-forcestatus"])
    @commands.has_permissions(administrator = True)
    async def change_forcestatus(self, ctx, roleid, forceName, newstatus):
        """ Change the status of any force and all units within it"""
        logInfo(f"change_forcestatus({ctx.guild.id}, {roleid}, {forceName}, {newstatus})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled
            
        gamerule = savegame.getGamerule()

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not(forceName in nation.military.keys()):
            raise InputError(f"{nation.name} does not own force \"{forceName}\"")

        if not(military.validate_status(newstatus)):
            raise InputError(f"Invalid status for force \"{newstatus}\"")

        newstatus = military.newforcestatus(nation, forceName, newstatus, savegame, gamerule)

        await ctx.send(f"New force status: {newstatus}")

        save_saveGame(savegame)
      
    @commands.command(aliases=['admincombineforces', 'admin-combine-forces', 'AdminCombineForces'])
    @commands.has_permissions(administrator = True)
    async def admin_combine_forces(self, ctx, roleid, base_forcename, *additional_forcenames):
        """ Combine multiple forces of a given nation. """
        logInfo(f"combine_forces({ctx.guild.id}, {base_forcename}, {additional_forcenames})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        #Validate that the player owns these forces

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"{roleid} does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        for forcename in additional_forcenames:
            if not (forcename in nation.military.keys()):
                raise InputError(f"{roleid} does not own the force {forcename}.  If a name has spaces, use quotation marks like this: \"name of force\"")

        base_force = nation.military[base_forcename]
        additional_forces = [nation.military[forcename] for forcename in additional_forcenames]

        if not(military.forces_addable(base_force, *additional_forces)):
            raise InputError("Could not combine these forces. Check if they have the same statuses, locations and types.")

        additional_forces = [nation.pop_force(forcename) for forcename in additional_forcenames]

        combined_force = military.combine_forces(base_force, *additional_forces)

        await ctx.send(f"Force \"{base_forcename}\" has merged with the following forces: {additional_forcenames}")

        save_saveGame(savegame)

    @commands.command(aliases=['admincombineunits', 'admin-combine-units', 'adminCombineUnits'])
    @commands.has_permissions(administrator = True)
    async def admin_combine_units(self, ctx, roleid, base_forcename, base_unitname, *additional_unitnames):
        """ Combine multiple units of a given nation. """
        logInfo(f"combine_units({ctx.guild.id}, {roleid}, {base_forcename}, {base_unitname}, {additional_unitnames})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        #Validate that the player owns these forces

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"{roleid} does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        base_force = nation.military[base_forcename]

        if not (base_unitname in base_force["Units"].keys()):
            raise InputError(f"{roleid} force {base_forcename} does not contain a unit named {base_unitname}.")

        for unitname in additional_unitnames:
            if not (unitname in base_force["Units"].keys()):
                raise InputError(f"{roleid} force {base_forcename} does not contain a unit named {unitname}.")

        base_unit = base_force["Units"][base_unitname]
        additional_units = [base_force["Units"][unitname] for unitname in additional_unitnames]

        if not(military.units_addable(base_unit, *additional_units)):
            raise InputError("Could not combine units")
        
        military.combine_units_inForce(base_force, base_unit, *additional_units)

        await ctx.send(f"Force \"{base_forcename}\" has merged unit {base_unitname} with the following units: {additional_unitnames}")

        save_saveGame(savegame)

    @commands.command(aliases=['adminsplitunit', 'admin-split-unit', 'adminSplitUnit'])
    @commands.has_permissions(administrator = True)
    async def admin_split_unit(self, ctx, roleid, base_forcename, base_unitname, *new_unitsizes):
        """ Split a unit of a given nation into multiple new ones. """
        logInfo(f"admin_split_unit({ctx.guild.id}, {base_forcename}, {base_unitname}, {new_unitsizes})")

        if (len(new_unitsizes) < 1):
            raise InputError(f"Must have at least one new unit size")

        for unitsize in new_unitsizes:
            if not (ops.isPositiveInt(unitsize)):
                raise InputError(f"Invalid unit size {unitsize}, must be positive integer")

        new_unitsizes = [int(unitsize) for unitsize in new_unitsizes]

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{roleid}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        baseForce = nation.military[base_forcename]

        if not (base_unitname in baseForce["Units"].keys()):
            raise InputError(f"Unit: {base_unitname} does not exist in Force: {base_forcename}")

        unit = baseForce["Units"][base_unitname]

        if not(military.unit_splittable(unit, *new_unitsizes)):
            raise InputError("Could not split unit")

        military.split_unit_inForce(nation, baseForce, unit, *new_unitsizes)

        await ctx.send(f"Force \"{base_forcename}\" has split unit {base_unitname} into new units with sizes: {new_unitsizes}. Use n.force \"{base_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['adminsplitforce', 'admin-split-force', 'adminSplitForce'])
    @commands.has_permissions(administrator = True)
    async def admin_split_force(self, ctx, roleid, base_forcename, *units_toSplit):
        """ Split a force belonging to any given nation, transferring several units to the new force """
        logInfo(f"split_force({ctx.guild.id}, {base_forcename}, {units_toSplit})")

        if (len(units_toSplit) < 1):
            raise InputError(f"Must have at least one unit to transfer")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{roleid}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        baseForce = nation.military[base_forcename]

        if not(military.force_splittable(baseForce, *units_toSplit)):
            raise InputError("Could not split force")

        new_forcename = military.split_force(nation, baseForce, *units_toSplit)

        await ctx.send(f"Force \"{base_forcename}\" has been split into new force {new_forcename} and transferred the units: {units_toSplit}. Use n.force \"{new_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['admindisbandunits', 'admin-disband-units', 'adminDisbandUnits'])
    @commands.has_permissions(administrator = True)
    async def admin_disband_units(self, ctx, roleid, base_forcename, *units_toDisband):
        """ Disband units in a given force belonging to a specific nation, returning their manpower to their home provinces. """
        logInfo(f"admin_disband_units({ctx.guild.id}, {roleid}, {base_forcename}, {units_toDisband})")

        if (len(units_toDisband) < 1):
            raise InputError(f"Must have at least one unit to disband")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        #Validate that the player owns these forces
        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"{roleid} does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        baseForce = nation.military[base_forcename]

        if [unitname for unitname in units_toDisband if unitname not in baseForce["Units"]]:
            raise InputError(f"Units do not all exist in force {base_forcename}")

        military.disband_units_inForce(nation, baseForce, units_toDisband)
        
        if not(baseForce["Units"]):
            nation.military.pop(base_forcename)

        await ctx.send(f"Disbanded units: {units_toDisband}. Use n.force \"{base_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['admindisbandforce', 'admin-disband-force', 'adminDisbandForce'])
    @commands.has_permissions(administrator = True)
    async def admin_disband_force(self, ctx, roleid, base_forcename):
        """ Disband a given force, returning its units' manpowers to their home provinces. """
        logInfo(f"disband_units({ctx.guild.id}, {roleid}, {base_forcename})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        #Validate that the player owns these forces
        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        military.disband_force(nation, base_forcename)

        await ctx.send(f"Disbanded force: {base_forcename}. Use n.force \"{base_forcename}\" to see more.")

        save_saveGame(savegame)

    @commands.command(aliases=['adminmoveforce', 'admin-move-force', 'adminMoveForce'])
    @commands.has_permissions(administrator = True)
    async def admin_move_force(self, ctx, roleid, base_forcename, *terrIDs):
        """ As an admin, order a given force to start moving to a series of territories """
        logInfo(f"admin_move_force({ctx.guild.id}, {roleid}, {base_forcename}, {terrIDs})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        territories = list()

        for terrID in terrIDs:

            if terrID.isdigit(): terrID = int(terrID)

            #Territory info from the map
            world_terr = world[terrID]

            if not world_terr:
                raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

            territories.append(world_terr.name)

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        path = military.setmovement_force(nation, base_forcename, world, *territories)

        if (path):
            await ctx.send(f"Force {base_forcename} has begun moving. Path: {[territory['Name'] for territory in path]}")

        else:
            await ctx.send(f"Could not move {base_forcename}")

        save_saveGame(savegame)

    @commands.command(aliases=['adminchangeforcelocation', 'admin-change-force-location', 'adminMoveForceLocation'])
    @commands.has_permissions(administrator = True)
    async def admin_change_force_location(self, ctx, roleid, base_forcename, terrID):
        """ As an admin, order a given force to start moving to a series of territories """
        logInfo(f"admin_change_force_location({ctx.guild.id}, {roleid}, {base_forcename}, {terrID})")

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

        nation = get_NationFromRole(ctx, roleid, savegame)

        if not (base_forcename in nation.military.keys()):
            raise InputError(f"<@&{playerinfo['role_discord_id']}> does not own the force {base_forcename}. If the name has spaces, use quotation marks like this: \"name of force\"")

        base_force = nation.military[base_forcename]

        base_force["Location"] = territoryName

        await ctx.send(f"Force {base_forcename} new location: {base_force['Location']}")

        save_saveGame(savegame)


    # Manage diplomacy

    @commands.command(aliases=["adminsetrelationship", "admin-set-relationship", "adminSetRelationship"])
    @commands.has_permissions(administrator = True)
    async def admin_set_relationship(self, ctx, relation, *roleids):
        """Declare the relations of several nations with each other"""

        logInfo(f"set_relationship({ctx.guild.id}, {relation}, {roleids})")

        if (len(set(roleids)) <= 1):
            raise InputError("Must have multiple unique nations to set relation for")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled
        
        nations = [get_NationFromRole(ctx, roleid, savegame) for roleid in roleids]

        if not(diplomacy.validate_relation(relation)):
            raise InputError(f"Invalid diplomatic relation {relation}. Valid relations: {', '.join(statuspattern[:-1] for statuspattern in diplomacy.valid_statuspatterns)}")

        diplomacy.set_relation(relation, *nations)

        await ctx.send(f"Made the following nations have the relationship {relation} with each other: {', '.join([nation.name for nation in nations])}")

        save_saveGame(savegame)


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