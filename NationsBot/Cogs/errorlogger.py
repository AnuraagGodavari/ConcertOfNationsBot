import json, datetime, pprint, traceback

import discord
from discord.ext import commands

from common import *
from database import *
from logger import *

from ConcertOfNationsEngine.concertofnations_exceptions import *

#The cog itself
class ErrorLogger(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        
           
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
            
        #error is an error built into discord.py, so analyze the original error
        if (isinstance(error, commands.errors.CommandInvokeError)):
            logInfo("CommandInvokeError raised")
            error = error.original

        if (ctx.guild):
            serverID = ctx.guild.id
        else:
            serverID = None

        authorID = ctx.author.id

        #Respond to error
        #If the error is that permissions are missing, very little info needs to be logged
        if (isinstance(error, commands.errors.MissingPermissions)):
            await ctx.send(str(error))
            logInfo(str(error), {"Server": serverID, "Author": authorID})
            return

        #Custom Exceptions
        if (isinstance(error, NonFatalError)):
            await ctx.send(str(error))

        elif (isinstance(error, InputError)):
            await ctx.send(f"Input Error: \"{str(error)}\"")

        elif (isinstance(error, LogicError)):
            await ctx.send(f"Game Error: \"{str(error)}\"")

        #Something unforseen happened, so document to the maximum
        else:
            errorData = logError(error, {"Server": serverID, "Author": authorID})

            await ctx.send(f"[{errorData['Error Time']}] The following error has occurred and been logged: \"{str(error)}\"")

        logInfo(f"Error has been handled successfully!\n")
        
async def setup(client):
    await client.add_cog(ErrorLogger(client))