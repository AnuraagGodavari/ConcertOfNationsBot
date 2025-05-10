import json, datetime, pprint, traceback, re

import discord
from discord.ext import commands
from discord.utils import get

from common import *
from database import *
from logger import *

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *
from DiscordUtils import validationutils as validationutils

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.concertofnations_exceptions import *
from ConcertOfNationsEngine import trade as trade

from GameUtils.filehandling import *
from GameUtils import operations as ops

#Util functions

def nation_trade_offers(ctx, nation, savegame):
    """
    Create a menu embed of all pending trade offers sent to or recieved by this nation
    """

    sent_trades = [] if nation.name not in savegame.offers else [
            (f"Offered to {recipient}", ops.invertDict(trade))
            for recipient, trade in savegame.offers[nation.name].items()
        ]

    recieved_trades = [
            (f"Sent by {sender}", trade)
            for sender, trade in
        {sender: offers[nation.name] for sender, offers in savegame.offers.items() if nation.name in offers.keys()}.items()
    ]

    menu = MenuEmbed(
        f"Trade Offers", 
        "_List of each trade offer this nation has sent or recieved, in terms of effects on this nation's economy. Positive numbers will be your imports from them, and negative numbers will be your exports to them._", 
        ctx.author.id,
        fields = sent_trades + recieved_trades,
        pagesize = 3,
        sortable = True,
        isPaged = True
        )

    return menu


#The cog itself
class TradeCommands(commands.Cog):
    """ Commands for managing trade """
    
    def __init__(self, client):
        self.client = client
        

    # Trade Information

    @commands.command()
    async def trade(self, ctx, roleid = None):
        """ 
        Show all of a nation's ongoing trade.
        Args:
            roleid: The nation role. By default it's the nation belonging to the user.
        """
        logInfo(f"trade({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)

        if (not roleid):

            playerinfo = get_player_byGame(savegame, ctx.author.id)

            if not (playerinfo):
                raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

            roleid = playerinfo['role_discord_id']
            logInfo(f"Got default role id {roleid} for this player")

        nation = get_NationFromRole(ctx, roleid, savegame)

        trade_menu = MenuEmbed(
        f"{nation.name} Trade", 
        "_Positive numbers are imports, and negative numbers are exports._", 
        ctx.author.id,
        fields = [(target, trade) for target, trade in nation.trade.items()],
        pagesize = 3,
        sortable = True,
        isPaged = True
        )

        assignMenu(ctx.author.id, trade_menu)

        logInfo(f"Created trade menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = trade_menu.toEmbed(), view = trade_menu.embedView())

    @commands.command(aliases = ["tradeoffers", "trade-offers", "tradeOffers"])
    async def trade_offers(self, ctx):
        """
        See all trade offers where your nation is either the target or the offerer.
        """
        logInfo(f"trade_offers({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)
        
        trade_menu = nation_trade_offers(ctx, nation, savegame)

        assignMenu(ctx.author.id, trade_menu)

        logInfo(f"Created trade offers menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = trade_menu.toEmbed(), view = trade_menu.embedView())

    @commands.command(aliases = ["offertrade", "offer-trade", "offerTrade"])
    async def offer_trade(self, ctx, target_roleid, *args):
        """
        Offer trade to another nation. Positive numbers will be your exports to them, and negative numbers will be your imports from them.
        Args:
            roleid: The target nation role.
            *args (tuple): A list of resources and numbers. Example:
            ("Iron", "2", "Money", "3")
        """
        logInfo(f"offer_trade({ctx.guild.id}, {target_roleid}, {args})")

        savegame = get_SavegameFromCtx(ctx)

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        target_nation = get_NationFromRole(ctx, target_roleid, savegame)

        if (nation == target_nation):
            raise InputError(f"Cannot trade with self!")
        
        #Get and validate resources
        resources_toadd = validationutils.get_resources_input(args, savegame)

        nation.offer_trade(savegame, target_nation, resources_toadd)

        logInfo(f"Successfully sent trade offer", details = {"Sender": nation.name, "Recipient": target_nation.name, "Trade": resources_toadd})
        await ctx.send("Successfully sent trade offer, type \"_n.trade\_offers_\" to view offer")

        save_saveGame(savegame)
 
    @commands.command(aliases = ["accepttrade", "accept-trade", "acceptTrade"])
    async def accept_trade(self, ctx, target_roleid):
        """
        Accept another nation's trade offer.
        Args:
            roleid: The target nation role.
        """
        logInfo(f"accept_trade({ctx.guild.id}, {target_roleid})")

        savegame = get_SavegameFromCtx(ctx)

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        target_nation = get_NationFromRole(ctx, target_roleid, savegame)

        if (nation == target_nation):
            raise InputError(f"Cannot trade with self!")

        if not(target_nation.name in savegame.offers.keys()):
            raise InputError(f"No offers exist from other nation!")

        if not(nation.name in savegame.offers[target_nation.name].keys()):
            raise InputError(f"No offer exists to you from other nation!")

        accepted_trade = nation.accept_trade(savegame, target_nation)

        logInfo(f"Successfully accepted trade offer", details = {"Nation": nation.name, "Sender": target_nation.name, "Trade": accepted_trade})
        await ctx.send(f"Successfully accepted trade offer from {nation.name}, type \"_n.trade_\" to view offer")

        save_saveGame(savegame)

    @commands.command(aliases = ["rejecttrade", "reject-trade", ])
    async def reject_trade(self, ctx, target_roleid):
        """
        Reject another nation's trade offer.
        Args:
            roleid: The target nation role.
        """
        logInfo(f"reject_trade({ctx.guild.id}, {target_roleid})")

        savegame = get_SavegameFromCtx(ctx)

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        target_nation = get_NationFromRole(ctx, target_roleid, savegame)

        if (nation == target_nation):
            raise InputError(f"Cannot trade with self!")

        if not(target_nation.name in savegame.offers.keys()):
            raise InputError(f"No offers exist from other nation!")

        if not(nation.name in savegame.offers[target_nation.name].keys()):
            raise InputError(f"No offer exists to you from other nation!")

        rejected_trade = nation.reject_trade(savegame, target_nation)

        logInfo(f"Successfully rejected trade offer", details = {"Nation": nation.name, "Sender": target_nation.name, "Trade": rejected_trade})
        await ctx.send(f"Rejected trade offer from {target_roleid}")

        save_saveGame(savegame)

    @commands.command(aliases = ["canceltradeoffer", "cancel-trade-offer", "cancelTradeOffer"])
    async def cancel_trade_offer(self, ctx, target_roleid):
        """
        Cancel your trade offer to another nation.
        Args:
            roleid: The target nation role.
        """
        logInfo(f"cancel_trade_offer({ctx.guild.id}, {target_roleid})")

        savegame = get_SavegameFromCtx(ctx)

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        target_nation = get_NationFromRole(ctx, target_roleid, savegame)

        if (nation == target_nation):
            raise InputError(f"Cannot trade with self!")

        if not(nation.name in savegame.offers.keys()):
            raise InputError(f"No offers exist from you!")

        if not(target_nation.name in savegame.offers[nation.name].keys()):
            raise InputError(f"No offer exists from you to other nation!")

        cancelled_trade = nation.cancel_trade_offer(savegame, target_nation)

        logInfo(f"Successfully cancelled trade offer", details = {"Nation": nation.name, "Sender": target_nation.name, "Trade": cancelled_trade})
        await ctx.send(f"Cancelled trade offer to {target_roleid}")

        save_saveGame(savegame)
        
    @commands.command(aliases = ["canceltrade", "cancel-trade", "cancelTrade"])
    async def cancel_trade(self, ctx, roleid):
        """
        Cancel ongoing trade with another nation.
        Args:
            roleid: The target nation role.
        """
        logInfo(f"cancel_trade({ctx.guild.id}, {roleid})")

        savegame = get_SavegameFromCtx(ctx)

        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)

        target_nation = get_NationFromRole(ctx, target_roleid, savegame)

        if (nation == target_nation):
            raise InputError(f"Cannot trade with self!")

        if not(target_nation.name in nation.trade.keys()):
            raise InputError(f"No ongoing trade exists with other nation!")

        cancelled_trade = nation.cancel_trade(savegame, target_nation)

        logInfo(f"Successfully cancelled ongoing trade", details = {"Nation": nation.name, "Sender": target_nation.name, "Trade": cancelled_trade})
        await ctx.send(f"Cancelled ongoing trade to {target_roleid}")

        save_saveGame(savegame)
        

async def setup(client):
    await client.add_cog(TradeCommands(client))