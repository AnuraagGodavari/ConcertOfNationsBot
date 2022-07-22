import os, json, logging
from dotenv import load_dotenv

import discord
from discord.ext import commands

from common import *
from database import *

import logger

#The bot
nationsbot = commands.Bot(command_prefix = 'n.', intents = discord.Intents().all())


@nationsbot.event
async def on_ready():
	""" Detects when the bot has been fully loaded and is online """
	print("Bot ready!")

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
	
	load_dotenv()
	token = os.getenv('TOKEN')
	
	for filename in os.listdir(f"{pwdir}/Cogs"):
		if filename.endswith(".py"):
			nationsbot.load_extension(f"Cogs.{filename[:-3]}")
	
	nationsbot.run(token)

if __name__ == "__main__":
	main()
