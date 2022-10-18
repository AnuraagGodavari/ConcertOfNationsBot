import json, datetime, pprint, traceback

import discord
from discord.ext import commands

from common import *
from database import *
from logger import *

from ConcertOfNationsEngine.CustomExceptions import *

#The cog itself
class ErrorLogger(commands.Cog):
    """ A cog that allows its client bot to watch member statuses """
    
    def __init__(self, client):
        self.client = client
        
           
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
            
        #error is an error built into discord.py, so analyze the original error
        if (isinstance(error, commands.errors.CommandInvokeError)):
            error = error.original

        if (ctx.guild):
            serverID = ctx.guild.id
        else:
            serverID = None

        authorID = ctx.author.id

        #Respond to error

        if (isinstance(error, NonFatalError)):
            await ctx.send(str(error))

        elif (isinstance(error, InputError)):
            await ctx.send(f"Input Error: \"{str(error)}\"")

        elif (isinstance(error, GameError)):
            await ctx.send(f"Game Error: \"{str(error)}\"")

        else:
            errorData = logError(error, {"Server": serverID, "Author": authorID})

            await ctx.send(f"The following error has occurred: \"{str(error)}\"")
            await ctx.send(f"_Error has been logged as <{errorData['Error Time']}>._")

        logInfo(f"Above error has been handled successfully!\n")
        
        
    @commands.command()
    async def error(self, ctx, **args):
        await ctx.send("Testing error logging...")
        raise Exception("Testing error logging from command!")
        
    @commands.command()
    async def inputError(self, ctx, **args):
        await ctx.send("Testing error logging...")
        raise InputError("Testing error logging from command!")
        
    @commands.command()
    async def gameError(self, ctx, **args):
        await ctx.send("Testing error logging...")
        raise GameError("Testing error logging from command!")
        
def setup(client):
    client.add_cog(ErrorLogger(client))