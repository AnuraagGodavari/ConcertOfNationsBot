#Python libraries
import sys
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
from Testing import GenerateGame


#CLI options
options = {
	"debug": False
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

def main():
	
	logInitial("Initializing Bot")
	
	global options
	
	load_dotenv()
	token = os.getenv('TOKEN')
	
	#Non-bot related setup
	if options["debug"]: 
		logInfo("Launching in Debug Mode")
		GenerateGame.generateGame()
	else: logInfo("Launching in Release Mode")
	
	for filename in os.listdir(cogsDir):
		if filename.endswith(".py"):
			nationsbot.load_extension(f"Cogs.{filename[:-3]}")
	
	nationsbot.run(token)

if __name__ == "__main__":
	
	#If command line args, generate data for flags dict
	if (len(sys.argv) > 1):
		for arg in sys.argv:
			
			if arg == "-d": 
				options["debug"] = True
	
	main()
