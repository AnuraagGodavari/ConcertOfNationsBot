import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *
from constants import *

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
import ConcertOfNationsEngine.buildings

from GameUtils.filehandling import *
import GameUtils.playerutils as playerutils

#The cog itself
class MapCommands(commands.Cog):
    """ Commands for seeing maps of the world and interacting with territories"""
    
    def __init__(self, client):
        self.client = client
        

    # Util Functions

    def territoriesMenu(self, ctx, roleid, shop = False):
        """
        Create a menu for territories by nation
        Args:
            roleid (Optional): The nation role. By default it's the nation belonging to the user.
            shop: Is a territory being selected for shopping? By default, False.
        """

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        if (not roleid):

            playerinfo = get_player_byGame(savegame, ctx.author.id)

            if not (playerinfo):
                raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

            roleid = playerinfo['role_discord_id']
            logInfo(f"Got default role id {roleid} for this player")

        nation = get_NationFromRole(ctx, roleid, savegame)
        

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        #Handles getting the world map if one exists that represents the current gamestate, or creating a new one otherwise.
        savegame.world_toImage(mapScale = (100, 100))
        worldMapInfo = dbget_gameWorldMap(world, savegame, savegame.turn)

        logInfo("Got a matching world map for this game.", details = {k: v for k, v in worldMapInfo.items() if k != 'created'})

        menu_territories = nation.territories.keys()

        menu = MenuEmbed(
            f"{nation.name} Territories", 
            "_Territories are displayed by their IDs. Use the command \"territory <id or name>\" to see more information about a territory!_", 
            ctx.author.id,
            imgurl = worldMapInfo['link'],
            fields = [
                (f"Territory {world[terrID].id}", {
                    "Name": world[terrID].name, 
                    "Coordinates": {'x': world[terrID].pos[0], 'y': world[terrID].pos[1]},
                    "Natural Resources": world[terrID].resources,
                    "Buildings": len([
                        buildingsList 
                        for buildingsList in nation.territories[terrID]["Buildings"].values()
                    ]),
                    "Sub-Territories": [world[subterr_id].name for subterr_id in world[terrID].subterritories],
                    **({ "Parent Territory": world[world[terrID].parent].name} if world[terrID].parent else {}) # Don't show null
                    }
                ) 
                for terrID in menu_territories
            ],
            pagesize = 3,
            sortable = True,
            isPaged = True
            )

        buildingInCart = playerutils.getKeyValue(ctx.guild.id, ctx.author.id, BuildingCacheEnums.BUILDING_IN_CART)

        if (shop and buildingInCart):
            menu.buttons = [
                CommandButton(ctx, self.client, f"{world[terr].name}", 1, "buy_building", [world[terr].id, buildingInCart])
                for terr in menu_territories
            ]

        else:
            menu.buttons = [
                CommandButton(ctx, self.client, f"{world[terr].name}", 1, "territory", [world[terr].id])
                for terr in menu_territories
            ]

        return menu
        
    def selectTerritory(self, ctx, terrID):
        playerutils.addKeyValue(ctx.guild.id, ctx.author.id, MapCacheEnums.TERRITORY_SELECTED, terrID)


    @commands.command()
    async def worldmap(self, ctx):
        """
        Look at the world map from the perspective of the player country
        """
        logInfo(f"worldmap({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            raise NonFatalError("No savegame attached to this server")

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        #Handles getting the world map if one exists that represents the current gamestate, or creating a new one otherwise.
        savegame.world_toImage(mapScale = (100, 100))
        worldMapInfo = dbget_gameWorldMap(world, savegame, savegame.turn)

        logInfo("Got a matching world map for this game.", details = {k: v for k, v in worldMapInfo.items() if k != 'created'})
        
        #Make a menu for the world map display

        menu = MenuEmbed(
            f"{savegame.name} World Map", 
            "_Territories are displayed by their IDs. Use the command \"terr\_lookup <id>\" to see more information about a territory!_", 
            ctx.author.id,
            imgurl = worldMapInfo['link'],
            fields = [
                (f"Territory {i}", {
                    "Name": terr.name, 
                    "Coordinates": {'x': terr.pos[0], 'y': terr.pos[1]},
                    "Resources": terr.resources,
                    "Base Nodes": terr.nodes
                    }
                ) 
                for i, terr in enumerate(world.territories)
                if not(terr.parent)
            ],
            pagesize = 3,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created worldmap_full menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

        save_saveGame(savegame)
        
    @commands.command()
    @commands.has_permissions(administrator = True)
    async def worldmap_full(self, ctx, roleid = None):
        """
        Look at the full world map associated with this game, without any fog of war unless admin specifies a country.
        Args:
            roleid: The nation role. If not specified, the worldmap will show all territories.
        """
        logInfo(f"worldmap_full({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            raise NonFatalError("No savegame attached to this server")

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        #Handles getting the world map if one exists that represents the current gamestate, or creating a new one otherwise.
        savegame.world_toImage(mapScale = (100, 100))
        worldMapInfo = dbget_gameWorldMap(world, savegame, savegame.turn)

        logInfo("Got a matching world map for this game.", details = {k: v for k, v in worldMapInfo.items() if k != 'created'})
        
        #Make a menu for the world map display

        menu = MenuEmbed(
            f"{savegame.name} World Map", 
            "_Territories are displayed by their IDs. Use the command \"terr\_lookup <id>\" to see more information about a territory!_", 
            ctx.author.id,
            imgurl = worldMapInfo['link'],
            fields = [
                (f"Territory {i}", {
                    "Name": terr.name, 
                    "Coordinates": {'x': terr.pos[0], 'y': terr.pos[1]},
                    "Resources": terr.resources,
                    "Base Nodes": terr.nodes
                    }
                ) 
                for i, terr in enumerate(world.territories)
                if not(terr.parent)
            ],
            pagesize = 3,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created worldmap_full menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

        save_saveGame(savegame)


    #Territories

    @commands.command()
    async def territories(self, ctx, roleid = None):
        """ 
        Show all of the territories owned by a nation, either that of the author or one that is specified.
        Args:
            roleid (Optional): The nation role. By default it's the nation belonging to the user.
        """
        logInfo(f"territories({ctx.guild.id}, {roleid})")

        menu = self.territoriesMenu(ctx, roleid)
        
        assignMenu(ctx.author.id, menu)

        logInfo(f"Created territories menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command(aliases=['selectterritory', 'select-territory'])
    async def select_territory(self, ctx, roleid = None): 
        """ 
        Select one of the territories owned by a nation, either that of the author or one that is specified.
        Args:
            roleid (Optional): The nation role. By default it's the nation belonging to the user.
        """
        logInfo(f"territories({ctx.guild.id}, {roleid})")

        menu = self.territoriesMenu(ctx, roleid, shop = True)

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created territories menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def territory(self, ctx, terrID):
        """
        Look at the details of a territory.

        Example: To look at territory 0, type:
        > n.territory 0
        
        Args:
            terrID: The name or numeric ID of the territory.
        """
        logInfo(f"territory({ctx.guild.id, terrID})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")


        #Territory info from the map
        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        fields = [
            ("Mineable Resources", world_terrInfo.resources)
        ]
        if (world_terrInfo.subterritories):
            fields += [
                ("Sub-Territories", [world[subterr_id].name for subterr_id in world_terrInfo.subterritories])
            ]

        buttons = [
            CommandButton(ctx, self.client, "Buildings", 1, "territory-buildings", [terrID]),
            CommandButton(ctx, self.client, "Population", 1, "population", [terrID])
        ] + [
            CommandButton(ctx, self.client, f"{world[subterr_id].name}", 3, "territory", [subterr_id])
            for subterr_id in world_terrInfo.subterritories
        ]

        #Territory info from the game
        terr_owner = savegame.find_terrOwner(world_terrInfo.id)

        if terr_owner:

            nation_terrInfo = savegame.nations[terr_owner].getTerritoryInfo(world_terrInfo.id, savegame)
            
            fields += [
                ("Owner", terr_owner),
                ("Buildings", len([
                    buildingStatus 
                    for buildingsList in nation_terrInfo["Savegame"]["Buildings"].values()
                    for buildingStatus in buildingsList
                    ])),
                ("Revenue", territories.newturnresources(nation_terrInfo, savegame) or None),
                ("Population", territories.get_totalpopulation(savegame.nations[terr_owner], world_terrInfo.id)),
                ("Manpower", nation_terrInfo["Savegame"]["Manpower"]),
                ("Nodes", {resource: f"{val[0]}/{val[1]}" for resource, val in nation_terrInfo["Savegame"]["Nodes"].items()})
            ]

            playerinfo = get_player_byGame(savegame, ctx.author.id)

            if (playerinfo):

                if (savegame.nations[terr_owner].role_id == playerinfo["role_discord_id"]):

                    buttons += [
                        CommandButton(
                            ctx, 
                            self.client, 
                            "Buy a building", 
                            2, 
                            "buildings_shop",
                            preClick = self.selectTerritory,
                            preClickArgs = [ctx, terrID]
                        )
                    ]

        else:

            fields += [
                ("Nodes", {resource: str(val) for resource, val in world_terrInfo.nodes.items()})
            ]

        
        menu = MenuEmbed(
            f"[{world_terrInfo.id}] {world_terrInfo.name}", 
            "_For building information, use the command n.territory-buildings <territory name or id>_", 
            ctx.author.id,
            fields = fields,
            buttons = buttons,
            format_text = True
        )


        assignMenu(ctx.author.id, menu)

        logInfo(f"Created territory {world_terrInfo.id} menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command(aliases=['territorybuildings', 'territory-buildings'])
    async def territory_buildings(self, ctx, terrID):
        """ 
        Show all of the available buildings in a given territory. 

        Example: To look at he buildings in territory 0, type:
        > n.territory_buildings 0
        
        Args:
            terrID: The name or numeric ID of the territory
        """
        logInfo(f"territory_buildings({ctx.guild.id}, {terrID})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")


        #Territory info from the map
        world_terr = world[terrID]

        if not world_terr:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")

        #Territory info from the game
        terr_owner = savegame.find_terrOwner(world_terr.id)
        if not terr_owner:
            raise InputError(f"Territory \"{terrID}\" is unowned and has no buildings")

        nation_terrInfo = savegame.nations[terr_owner].getTerritoryInfo(world_terr.id, savegame)

        menu = MenuEmbed(
            f"Buildings in {world_terr.name}", 
            "_Information about all of the buildings in this territory, including all statuses and the blueprint for one of each building._", 
            ctx.author.id,
            fields = [
                (buildingName, 
                ops.combineDicts({"Number": len(buildingsList), "All Statuses": buildingsList}, buildings.get_blueprint(buildingName, savegame))
                )
                for buildingName, buildingsList in nation_terrInfo["Savegame"]["Buildings"].items()
            ],
            pagesize = 3,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created buildings menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

async def setup(client):
    await client.add_cog(MapCommands(client))