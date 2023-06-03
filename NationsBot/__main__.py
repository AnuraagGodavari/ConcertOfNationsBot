#Python libraries
import sys, asyncio
import os, json, logging
import importlib

#Packages
from dotenv import load_dotenv

import discord
from discord.ext import commands

#Utilities
from common import *
from database import *
from logger import *

#For NationsBot
from Testing import tests


#CLI options
options = {
    "debug": False,
    "test bot": False,
    "abort": False
}

#The bot
nationsbot = commands.Bot(command_prefix = 'n.', intents = discord.Intents().all())

async def test_bot(ctx):

    #Non-bot related setup
    if options["test bot"]: 
        logInfo("Bot ready in bot testing mode")
    
        load_dotenv()
        testsuite = None

        logInfo("Loading Test Suite from module specified under 'TESTSUITE_SCRIPT_BOT' in .env")

        try: 
            testsuite_module = importlib.import_module(os.getenv('TESTSUITE_SCRIPT_BOT'))
            testsuite = testsuite_module.test_bot
        except Exception as e: 
            logError(e)
            options["abort"] = True
            return

        logInfo("Executing Test Suite...")

        try: 
            start_ctx = await nationsbot.get_context(await ctx.send("Starting Bot Test"))
            await testsuite(start_ctx, nationsbot)

            start_ctx = await ctx.send("Bot testing ended without any unexpected errors")

        except Exception as e: logError(e)

        logInfo("Bot Test Suite successfully executed")
    pass

@nationsbot.event
async def on_ready():
    """ Detects when the bot has been fully loaded and is online """
    logInfo("Bot ready!")

    if (options["test bot"]):
        await test_bot(nationsbot.get_channel(int(os.getenv('TEST_CHANNEL_ID'))))

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
    
        load_dotenv()
        testsuite = None

        logInfo("Loading Test Suite from module specified under 'TESTSUITE_SCRIPT' in .env")

        try: 
            testsuite_module = importlib.import_module(os.getenv('TESTSUITE_SCRIPT'))
            testsuite = testsuite_module.testsuite
        except Exception as e: 
            logError(e)
            options["abort"] = True
            return

        logInfo("Executing Test Suite...")

        try: testsuite()
        except Exception as e: logError(e)

        logInfo("Test Suite successfully executed")

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

            if 't' in arg:
                options["test bot"] = True
    
    asyncio.run(setup())

    if options["abort"]: exit()
    
    main()
