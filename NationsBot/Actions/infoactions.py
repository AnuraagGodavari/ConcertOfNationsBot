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

from Actions import mapactions

# General Information

async def gamestate(client, ctx):
    """
    Provide info about the current game as it is right now.
    """
    logInfo(f"giveTerritory({ctx.guild.id})")

    savegame = get_SavegameFromCtx(ctx)

    menu = MenuEmbed(
        f"{savegame.name} Game State", 
        None, 
        None,
        fields = [
            ("Turn", savegame.turn),
            ("Date", f"Month {savegame.date['m']}, Year {savegame.date['y']}")
        ],
        format_text = False
        )

    logInfo(f"Created Game State display")

    await ctx.send(embed = menu.toEmbed())

async def nationinfo(client, ctx, roleID: str = None):
        """
        Display basic info about the author's nation or, if another role is specified, that role's nation. 

        Parameters
        -----------
            roleID: discord.Role
                The nation role.
        """

        logInfo(f"nationinfo({ctx.guild.id}, {roleID})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        gamerule = savegame.getGamerule()

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if (not roleID):

            if not (playerinfo):
                raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

            roleID = playerinfo["role_discord_id"]
            logInfo(f"Got default role id {roleID} for this player")

        nation = get_NationFromRole(ctx, roleID, savegame)
        
        menu = MenuEmbed(
            f"{nation.name} Information", 
            None, 
            None,
            fields = [
                ("Resources", nation.resources),
                ("Revenue", ops.combineDicts(nation.get_TurnRevenue(savegame, onlyestimate = True), {"Money": nation.get_taxincome(gamerule)})),
                ("Bureaucracy", {f"{category}": f"{cap[0]}/{cap[1]}" for category, cap in nation.bureaucracy.items()}),
                ("Modifiers", nation.modifiers)
            ],
            buttons = [
                CommandButton(ctx, client, "Territories", 1, mapactions.territories, [nation.role_id]),
                #CommandButton(ctx, client, "Trade", 1, "trade", [nation.role_id]),
                #CommandButton(ctx, client, "Forces", 1, "forces", [nation.role_id]),
                #CommandButton(ctx, client, "Population", 1, "population", [nation.role_id])
            ]
            )

        if (playerinfo):

            if (get_RoleID(roleID) == playerinfo["role_discord_id"]): menu.buttons += [
                #CommandButton(ctx, client, "Info Commands", 2, "help", ["InfoCommands"]),
                #CommandButton(ctx, client, "Map Commands", 2, "help", ["MapCommands"]),
                #CommandButton(ctx, client, "Military Commands", 2, "help", ["MilitaryCommands"]),
                #CommandButton(ctx, client, "Building Commands", 2, "help", ["BuildingCommands"]),
                #CommandButton(ctx, client, "Trade Commands", 2, "help", ["TradeCommands"]),
                #CommandButton(ctx, client, "Buildings Shop", 3, "buildings_shop")
            ]

        logInfo(f"Created Nation info display")

        return menu

async def nations(client, ctx):
        """ 
        Display basic info about all nations in the game.
        """
        logInfo(f"nationinfo({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        gamerule = savegame.getGamerule()

        nations = get_PlayerGames(savegame.server_id)

        if not(nations):
            await ctx.send("No nations in this game yet! An admin can use the command add_nation.")
            return
        
        menu = MenuEmbed(
            f"All Nations", 
            None, 
            None,
            fields = [
                (f"{nation['name']}", f"<@{nation['player_discord_id']}>")
                for nation in nations
            ],
            buttons = [
                CommandButton(ctx, client, f"{nation['name']}", 1, nationinfo, [nation['role_discord_id']])
                for nation in nations
            ],
            format_text = False
            )

        logInfo(f"Created Nation info display")

        return menu


# Military Information

async def forces(client, ctx, roleID: str = None):
    """ 
    Show all of the forces controlled by a nation, either that of the author or one that is specified. 
    
    Parameters
    -----------
        roleID: str
            The nation role.
    """
    
    logInfo(f"forces({ctx.guild.id}, {roleID})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    if (not roleID):

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleID = playerinfo['role_discord_id']
        logInfo(f"Got default role id {roleID} for this player")

    nation = get_NationFromRole(ctx, roleID, savegame)

    menu = MenuEmbed(
        f"{nation.name} Military Forces", 
        "_Use the command \"force <id or name>\" to see more information about a force!_", 
        ctx.author.id,
        fields = [
            (forcename, {
                "Status": force["Status"] if "Moving" not in force["Status"] else f"{force['Status']} to {force['Path'][-1]['Name']} [ID: {force['Path'][-1]['ID']}] ",
                "Location": force["Location"],
                "Units": len(force["Units"]),
                "Size": sum(unit.size for unit in force["Units"].values())
                }
            ) 
            for forcename, force in nation.military.items()
        ],
        buttons = [
            CommandButton(ctx, client, forcename, 1, "force", [forcename])
            for forcename in nation.military.keys()
        ],
        pagesize = 9,
        sortable = True,
        isPaged = True
        )

    assignMenu(ctx.author.id, menu)

    logInfo(f"Created forces menu and assigned it to player {ctx.author.id}")

    return menu

async def force(client, ctx, forcename: str = None):
    """ 
    Show a specific force controlled by any nation in the game. 

    Parameters
    -----------
        forcename: str
            A specific force's name belonging to any nation
    """

    logInfo(f"force({ctx.guild.id}, {forcename})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled
        
    nationname = savegame.find_forceOwner(forcename)        
    if (not nationname):
        raise InputError(f"Force {forcename} does not exist in this game! If the name has spaces, encase it in quotes like this: \"name\"")
    nation = savegame.nations[nationname]

    force = nation.military[forcename]

    menu = MenuEmbed(
        f"{forcename} Units", 
        f"Owner: {nation.name}\nStatus: {force['Status']}\nLocation: {force['Location']}", 
        ctx.author.id,
        fields = [
            (unit.name, unit.get_fields())
            for unit in force["Units"].values()
        ],
        pagesize = 9,
        sortable = True,
        isPaged = True
        )

    if ("Moving" in force["Status"]):
        menu.description += f"\n Path: {' >> '.join([territory['Name'] + ' [' + str(territory['ID']) + '] Distance: ' + str(territory['Distance']) for territory in force['Path']])}"

    elif ("Battling" in force["Status"]):
        menu.description += f"\nIn battle with {force['Battle']['Nation']} force: {force['Battle']['Force']}"

    assignMenu(ctx.author.id, menu)

    logInfo(f"Created force menu and assigned it to player {ctx.author.id}")

    return menu

async def units(client, ctx):
    """ 
    Show all of the available units in the given server's game. 
    """

    logInfo(f"units({ctx.guild.id})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    gamerule = savegame.getGamerule()
    if not (gamerule):
        raise InputError("Savegame's gamerule could not be retrieved")

    menu = MenuEmbed(
        f"Units", 
        f"_Information about all of the units in this game's ruleset._\n_Valid status regular expressions: {military.valid_statuspatterns}_", 
        ctx.author.id,
        fields = [
            (unitName, unitInfo)
            for unitName, unitInfo in military.get_allunits(gamerule).items()
        ],
        pagesize = 6,
        sortable = True,
        isPaged = True
        )

    assignMenu(ctx.author.id, menu)

    logInfo(f"Created units menu and assigned it to player {ctx.author.id}")

    return menu


# Population Utils

def nation_population(ctx, nation):

    menu = MenuEmbed(
        f"Populations", 
        "_List of each individual population in this nation by territory, occupation and other identifiers_", 
        ctx.author.id,
        fields = [
            (str(territoryName) + ' ' + ' '.join(list(pop.identifiers.values())) + ' ' + pop.occupation, 
            {
                "Population": pop.size,
                "Growth": pop.growthrate,
                "Mobilization": pop.manpower / pop.size
            }
            )
            for territoryName, popslist in nation.all_populations().items() for pop in popslist
        ],
        pagesize = 20,
        sortable = True,
        isPaged = True
        )

    return menu

def territory_population(ctx, terrID, savegame):

    world = savegame.getWorld()
    if not (world):
        raise InputError("Savegame's world could not be retrieved")


    #Territory info from the map
    world_terrInfo = world[terrID]

    if not world_terrInfo:
        raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

    pops = []

    #Territory info from the game
    terr_owner = savegame.find_terrOwner(world_terrInfo.name)
    if terr_owner:

        nation_terrInfo = savegame.nations[terr_owner].get_territory(world_terrInfo.name)
        
        pops = [
            (' '.join(list(pop.identifiers.values())) + ' ' + pop.occupation, 
            {
                "Population": pop.size,
                "Growth Rate": pop.growthrate,
                "Manpower": pop.manpower,
                "Percent Raised as Manpower": pop.manpower / pop.size
            }
            )
            for pop in nation_terrInfo["Population"]
        ]

    menu = MenuEmbed(
        f"{world_terrInfo.name} Populations", 
        "_List of each individual population in this nation by territory, occupation and other identifiers_", 
        ctx.author.id,
        fields = pops,
        pagesize = 20,
        sortable = True,
        isPaged = True
        )

    return menu


# Population Information

async def population(client, ctx, roleID, terrID):
    """ 
    Show all of the populations in a nation or a territory

    Parameters
    -----------
        roleID (optional): str
            The nation role.

        territory (optional): str
            The territory name or ID.
    """
    logInfo(f"population({ctx.guild.id}, {roleID})")

    savegame = get_SavegameFromCtx(ctx)
    if not (savegame): 
        return #Error will already have been handled

    if (not(roleID) and terrID):
        menu = territory_population(ctx, terrID, savegame)

    else:
        if (not (roleID)):

            playerinfo = get_player_byGame(savegame, ctx.author.id)

            if not (playerinfo):
                raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

            roleID = playerinfo['role_discord_id']
            logInfo(f"Got default role id {roleID} for this player")

        nation = get_NationFromRole(ctx, roleID, savegame, isOptionalArg=True)
        
        menu = nation_population(ctx, nation)

    assignMenu(ctx.author.id, menu)

    logInfo(f"Created populations menu and assigned it to player {ctx.author.id}")

    return menu

async def population_info(client, ctx):
        logInfo(f"population_info({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        gamerule = savegame.getGamerule()
        if not (gamerule):
            raise InputError("Savegame's gamerule could not be retrieved")

        menu = MenuEmbed(
            f"Population Info", 
            f"_Information about the possible occupations and identifiers for populations in this game.", 
            ctx.author.id,
            fields = [
                (field[0], '\n'.join(field[1]))
                for field in
                list(gamerule["Population Identifiers"].items()) + [("Occupations", gamerule["Occupations"])]
            ],
            pagesize = 20,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created population info menu and assigned it to player {ctx.author.id}")

        return menu


