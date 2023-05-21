import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from GameUtils import operations as ops

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
from ConcertOfNationsEngine.buildings import *
import ConcertOfNationsEngine.territories as territories


#The cog itself
class InfoCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def gamestate(self, ctx):
        """
        Provide info about the current game as it is right now
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
            ]
            )

        logInfo(f"Created Game State display")

        await ctx.send(embed = menu.toEmbed())

    @commands.command()
    async def nationinfo(self, ctx, roleid = None):
        """ Display basic info about the author's nation or, if another role is specified, the same info about that role's nation. """
        logInfo(f"nationinfo({ctx.guild.id}, {roleid})")

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
        

        menu = MenuEmbed(
            f"{nation.name} Information", 
            None, 
            None,
            fields = [
                ("Resources", nation.resources),
                ("Bureaucracy", {f"{category}": f"{cap[0]}/{cap[1]}" for category, cap in nation.bureaucracy.items()})
            ]
            )

        logInfo(f"Created Nation info display")

        await ctx.send(embed = menu.toEmbed())


    #Territory Information

    @commands.command()
    async def territories(self, ctx, roleid = None):
        """ Show all of the territories owned by a nation, either that of the author or one that is specified. """
        logInfo(f"territories({ctx.guild.id}, {roleid})")

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
        worldMapInfo = dbget_worldMap(world, savegame, savegame.turn)

        logInfo("Got a matching world map for this game.", details = {k: v for k, v in worldMapInfo.items() if k != 'created'})

        menu = MenuEmbed(
            f"{nation.name} Territories", 
            "_Territories are displayed by their IDs. Use the command \"territory <id or name>\" to see more information about a territory!_", 
            ctx.author.id,
            imgurl = worldMapInfo['link'],
            fields = [
                (f"Territory {world[terr].id}", {
                    "Name": world[terr].name, 
                    "Coordinates": {'x': world[terr].pos[0], 'y': world[terr].pos[1]},
                    "Resources": world[terr].resources
                    }
                ) 
                for terr in nation.territories.keys()
            ],
            pagesize = 9,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created territories menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def territory(self, ctx, terrID):
        """
        Look at the details of a territory
        """
        logInfo(f"territory({ctx.guild.id, terrID})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

        #Territory info from the map
        world_terrInfo = world[terrID]

        if not world_terrInfo:
            raise InputError(f"Invalid Territory Name or ID \"{terrID}\"")
        
        fields = [
            ("Mineable Resources", world_terrInfo.resources)
        ]

        #Territory info from the game
        terr_owner = savegame.find_terrOwner(world_terrInfo.name)
        if terr_owner:

            nation_terrInfo = savegame.nations[terr_owner].getTerritoryInfo(world_terrInfo.name, savegame)
            
            fields += [
                ("Owner", terr_owner),
                ("Number of buildings", len(nation_terrInfo["Savegame"]["Buildings"].keys())),
                ("Impact on revenue", territories.newturnresources(nation_terrInfo, savegame) or None)
            ]

        
        menu = MenuEmbed(
            f"[{world_terrInfo.id}] {world_terrInfo.name}", 
            "_For building information, use the command n.territory-buildings <territory name or id>_", 
            ctx.author.id,
            fields = fields
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created territory {world_terrInfo.id} menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed())

    @commands.command(aliases=['territorybuildings', 'territory-buildings'])
    async def territory_buildings(self, ctx, terrID):
        """ Show all of the available buildings in the given territory. """
        logInfo(f"territory_buildings({ctx.guild.id}, {terrID})")

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

        #Territory info from the game
        terr_owner = savegame.find_terrOwner(world_terr.name)
        if not terr_owner:
            raise InputError(f"Territory \"{terrID}\" is unowned and has no buildings")

        nation_terrInfo = savegame.nations[terr_owner].getTerritoryInfo(world_terr.name, savegame)

        menu = MenuEmbed(
            f"Buildings in {world_terr.name}", 
            "_Information about all of the buildings in this territory_", 
            ctx.author.id,
            fields = [
                (buildingName, 
                ops.combineDicts({"Status": buildingStatus}, get_blueprint(buildingName, savegame))
                )
                for buildingName, buildingStatus in nation_terrInfo["Savegame"]["Buildings"].items()
            ],
            pagesize = 20,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created buildings menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    #Building management

    @commands.command()
    async def buildings(self, ctx):
        """ Show all of the available buildings in the given server's game. """
        logInfo(f"buildings({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        menu = MenuEmbed(
            f"Buildings", 
            "_Information about all of the buildings in this game's ruleset_", 
            ctx.author.id,
            fields = [
                (buildingName, buildingInfo)
                for buildingName, buildingInfo in get_allbuildings(savegame).items()
            ],
            pagesize = 20,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created buildings menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())


    #Population Information

    def nation_population(self, ctx, nation):

        menu = MenuEmbed(
            f"Populations", 
            "_List of each individual population in this nation by territory, occupation and other identifiers_", 
            ctx.author.id,
            fields = [
                (territoryName + ' ' + ' '.join(list(pop.identifiers.values())) + ' ' + pop.occupation, 
                {
                    "Population": pop.size,
                    "Growth Rate": pop.growth
                }
                )
                for territoryName, popslist in nation.all_populations().items() for pop in popslist
            ],
            pagesize = 20,
            sortable = True,
            isPaged = True
            )

        return menu

    def territory_population(self, ctx, terrID, savegame):

        world = savegame.getWorld()
        if not (world):
            raise InputError("Savegame's world could not be retrieved")

        if terrID.isdigit(): terrID = int(terrID)

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
                    "Growth Rate": pop.growth
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

    @commands.command(aliases=['people', 'populations'])
    async def population(self, ctx, optionalID = None):
        """ Show all of the populations in a nation or a territory"""
        logInfo(f"population({ctx.guild.id}, {optionalID})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        roleid = optionalID

        if not (roleid):

            playerinfo = get_player_byGame(savegame, ctx.author.id)

            if not (playerinfo):
                raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

            roleid = playerinfo['role_discord_id']
            logInfo(f"Got default role id {roleid} for this player")

        nation = get_NationFromRole(ctx, roleid, savegame, isOptionalArg=True)

        if (nation): 
            menu = self.nation_population(ctx, nation)

        #Else, assume this is a territory, this may or may not be true, the function will handle any errors
        else:
            menu = self.territory_population(ctx, optionalID, savegame)

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created populations menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

        

async def setup(client):
    await client.add_cog(InfoCommands(client))