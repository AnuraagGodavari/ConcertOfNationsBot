#Python libraries
import sys, asyncio
import os, json, logging

#Packages
from dotenv import load_dotenv

import discord
from discord.ext import commands

#Utilities
from common import *
from database import *
from logger import *

#For NationsBot
from Testing import generategame


#CLI options
options = {
    "debug": False,
    "abort": False
}

#The bot
nationsbot = commands.Bot(command_prefix = 'n.', intents = discord.Intents().all())


@nationsbot.event
async def on_ready():
    """ Detects when the bot has been fully loaded and is online """
    logInfo("Bot ready!")

@nationsbot.command()
async def load(ctx, cog):
    pass

@nationsbot.command()
async def unload(ctx, cog):
    pass

        
@nationsbot.command()
async def ping(ctx):
    await ctx.send(f"Pong!\nLatency: **{round(nationsbot.latency * 1000)}ms**")

async def setup():

    logInitial("Initializing Bot")
    
    global options
    
    #Non-bot related setup
    if options["debug"]: 
        logInfo("Launching in Debug Mode")

        try: generategame.testSuite()
        except Exception as e: logError(e)

        if options["abort"]:
            logInfo("Aborting before bot launch\n\n")
            return

    else: logInfo("Launching in Release Mode")
    
    for filename in os.listdir(cogsDir):
        if filename.endswith(".py"):
            await nationsbot.load_extension(f"Cogs.{filename[:-3]}")

def main():
    
    load_dotenv()
    token = os.getenv('TOKEN')
    
    nationsbot.run(token)

if __name__ == "__main__":
    
    #If command line args, generate data for flags dict
    if (len(sys.argv) > 1):
        for arg in sys.argv[1:]:
            
            if 'd' in arg: 
                options["debug"] = True

            if 'a' in arg:
                options["abort"] = True
    
    asyncio.run(setup())

    if options["abort"]: exit()
    
    main()
