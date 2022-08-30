import json, datetime, pprint, traceback

import discord
from discord.ext import commands

from common import *
from database import *
from logger import *

#The cog itself
class AdminCommands(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        
        
    @commands.command()
    async def admincommands_test(self, ctx, **args):
        await ctx.send("Admin Command")
        
def setup(client):
    client.add_cog(AdminCommands(client))