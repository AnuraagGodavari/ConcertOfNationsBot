import json, datetime, pprint, traceback

import discord
from discord.ext import commands
from discord import app_commands

from common import *
from database import *
from logger import *

from ConcertOfNationsEngine.concertofnations_exceptions import *

async def handle_error(ctx, error):
            
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
        return str(error)
        logInfo(str(error), {"Server": serverID, "Author": authorID})
        return

    #Custom Exceptions
    if (isinstance(error, NonFatalError)):
        return str(error)

    elif (isinstance(error, InputError)):
        return f"Input Error: \"{str(error)}\""

    elif (isinstance(error, LogicError)):
        return f"Game Error: \"{str(error)}\""

    #Something unforseen happened, so document to the maximum
    else:
        errorData = logError(error, {"Server": serverID, "Author": authorID})

        return f"[{errorData['Error Time']}] The following error has occurred and been logged: \"{str(error)}\""

    logInfo(f"Error has been handled successfully!\n")

#The cog itself
class ErrorLogger(commands.Cog):
    """ A cog without any commands - this is what manages error handling """
    
    def __init__(self, client):
        self.client = client
                       
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        errorMsg = await handle_error(ctx, error)

        await ctx.send(error)
        
async def on_tree_error(interaction: discord.Interaction, error):

    ctx = await interaction.client.get_context(interaction)
    errorMsg = await handle_error(ctx, error)

    await interaction.response.send_message(errorMsg, ephemeral = True)
        
async def setup(client):
    await client.add_cog(ErrorLogger(client))
    client.tree.on_error = on_tree_error