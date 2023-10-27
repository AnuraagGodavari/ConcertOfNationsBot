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
import ConcertOfNationsEngine.military as military
import ConcertOfNationsEngine.territories as territories


#The cog itself
class InfoCommands(commands.Cog):
    """ Commands that deliver information to a player about the gamestate or the game rules """
    
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def gamestate(self, ctx):
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
            ]
            )

        logInfo(f"Created Game State display")

        await ctx.send(embed = menu.toEmbed())

    @commands.command()
    async def nationinfo(self, ctx, roleid = None):
        """ 
        Display basic info about the author's nation or, if another role is specified, the same info about that role's nation. 
        Args:
            roleid: The nation role.
        """
        logInfo(f"nationinfo({ctx.guild.id}, {roleid})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        gamerule = savegame.getGamerule()

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
                ("Revenue", ops.combineDicts(nation.get_TurnRevenue(savegame, onlyestimate = True), {"Money": nation.get_taxincome(gamerule)})),
                ("Bureaucracy", {f"{category}": f"{cap[0]}/{cap[1]}" for category, cap in nation.bureaucracy.items()}),
                ("Modifiers", nation.modifiers)
            ]
            )

        logInfo(f"Created Nation info display")

        await ctx.send(embed = menu.toEmbed())


    # Military Information

    @commands.command(aliases=['military'])
    async def forces(self, ctx, roleid = None):
        """ 
        Show all of the forces controlled by a nation, either that of the author or one that is specified. 
        Args:
            roleid: The nation role. By default it's the nation belonging to the user.
        """
        logInfo(f"forces({ctx.guild.id}, {roleid})")

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
            pagesize = 9,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created forces menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command(aliases=['militaryforce', 'military-force', 'militaryForce', 'military_force'])
    async def force(self, ctx, forcename):
        """ 
        Show a specific force controlled by any nation in the game. 
        Args:
            forcename: A specific force's name belonging to any nation
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
                (unit.name, {
                    "Status": unit.status,
                    "Type": unit.unitType,
                    "Size": unit.size,
                    "Home Territory": unit.home
                })
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

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    @commands.command()
    async def units(self, ctx):
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
            pagesize = 20,
            sortable = True,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created units menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())


    # Territory Information

    @commands.command()
    async def territories(self, ctx, roleid = None):
        """ 
        Show all of the territories owned by a nation, either that of the author or one that is specified.
        Args:
            roleid: The nation role. By default it's the nation belonging to the user.
        """
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
                    "Natural Resources": world[terr].resources,
                    "Buildings": len(nation.territories[terr]["Buildings"])
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
        Look at the details of a territory.
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
                ("Buildings", len(nation_terrInfo["Savegame"]["Buildings"].keys())),
                ("Revenue", territories.newturnresources(nation_terrInfo, savegame) or None),
                ("Population", territories.get_totalpopulation(savegame.nations[terr_owner], world_terrInfo.name)),
                ("Manpower", nation_terrInfo["Savegame"]["Manpower"])
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
        """ 
        Show all of the available buildings in a given territory. 
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

    # Building Information

    @commands.command()
    async def buildings(self, ctx):
        """ 
        Show all of the available buildings in the given server's game. 
        """
        logInfo(f"buildings({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)
        if not (savegame): 
            return #Error will already have been handled

        menu = MenuEmbed(
            f"Buildings", 
            f"_Information about all of the buildings in this game's ruleset._\n_Valid status regular expressions: {buildings.valid_statuspatterns}_", 
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


    # Population Information

    def nation_population(self, ctx, nation):

        menu = MenuEmbed(
            f"Populations", 
            "_List of each individual population in this nation by territory, occupation and other identifiers_", 
            ctx.author.id,
            fields = [
                (territoryName + ' ' + ' '.join(list(pop.identifiers.values())) + ' ' + pop.occupation, 
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

    @commands.command(aliases=['people', 'populations'])
    async def population(self, ctx, optionalID = None):
        """ 
        Show all of the populations in a nation or a territory
        Args:
            optionalID: Either a nation role or a name or numeric ID of a territory.
        """
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