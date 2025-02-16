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

#Util functions

def nation_trade_offers(ctx, nation, savegame):
    """
    Create a menu embed of all pending trade offers sent to or recieved by this nation
    """

    sent_trades = [] if nation.name not in savegame.offers else [
            (f"Offered to {recipient}", trade)
            for recipient, trade in savegame.offers[nation.name].items()
        ]

    recieved_trades = [
            (f"Sent by {sender}", {resource: amount * -1 for resource, amount in trade.items()})
            for sender, trade in
        {sender: offers[nation.name] for sender, offers in savegame.offers.items() if nation.name in offers.keys()}.items()
    ]

    menu = MenuEmbed(
        f"Trade Offers", 
        "_List of each trade offer this nation has sent or recieved, in terms of effects on this nation's economy. Positive numbers will be your imports from them, and negative numbers will be your exports to them._", 
        ctx.author.id,
        fields = sent_trades + recieved_trades,
        pagesize = 5,
        sortable = True,
        isPaged = True
        )

    return menu


#The cog itself
class TradeCommands(commands.Cog):
    """ Commands for managing trade """
    
    def __init__(self, client):
        self.client = client
        
    @commands.command(aliases = ["offertrade", "offer-trade", "offerTrade"])
    async def offer_trade(self, ctx, target_roleid = None, *args):
        """
        Offer trade to another nation. Positive numbers will be your exports to them, and negative numbers will be your imports from them.
        Args:
            roleid: The target nation role.
            *args (tuple): A list of resources and numbers. Example:
            ("Iron", "2", "Money", "3")
        """
        logInfo(f"offer_trade({ctx.guild.id}, {target_roleid}, {args})")

        savegame = get_SavegameFromCtx(ctx)

        #Validate that the player owns this territory
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

        logInfo(f"Successfully sent trade offer", details = {"Sender": nation.name, "Recipient": target_nation.name, "Resources": nation.resources})
        await ctx.send("Successfully sent trade offer, type \"_n.trade\_offers_\" to view offer")

        save_saveGame(savegame)

    @commands.command(aliases = ["tradeoffers", "trade-offers", "tradeOffers"])
    async def trade_offers(self, ctx):
        """
        See all trade offers where your nation is either the target or the offerer.
        """
        logInfo(f"trade_offers({ctx.guild.id})")

        savegame = get_SavegameFromCtx(ctx)

        #Validate that the player owns this territory
        playerinfo = get_player_byGame(savegame, ctx.author.id)

        if not (playerinfo):
            raise InputError(f"Could not get a nation for player <@{ctx.author.id}>")

        roleid = playerinfo['role_discord_id']

        nation = get_NationFromRole(ctx, roleid, savegame)
        
        trade_menu = nation_trade_offers(ctx, nation, savegame)

        assignMenu(ctx.author.id, trade_menu)

        logInfo(f"Created trade offers menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = trade_menu.toEmbed(), view = trade_menu.embedView())
        
    @commands.command(aliases = ["accepttrade", "accept-trade", "acceptTrade"])
    async def accept_trade(self, ctx, roleid = None):
        """
        Accept another nation's trade offer.
        Args:
            roleid: The target nation role.
        """
        logInfo(f"accept_trade({ctx.guild.id}, {roleid})")

        pass
        
    @commands.command(aliases = ["canceltrade", "cancel-trade", "cancelTrade"])
    async def cancel_trade(self, ctx, roleid = None):
        """
        Cancel or reject trade or a trade offer with another nation.
        Args:
            roleid: The target nation role.
        """
        logInfo(f"cancel_trade({ctx.guild.id}, {roleid})")

        pass
        

async def setup(client):
    await client.add_cog(TradeCommands(client))