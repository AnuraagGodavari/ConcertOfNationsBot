import json, datetime, pprint, traceback

import discord
from discord.ext import commands

from common import *
from database import *
from logger import *

#The cog itself
class ErrorLogger(commands.Cog):
	""" A cog that allows its client bot to watch member statuses """
	
	def __init__(self, client):
		self.client = client
		
		   
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
			
		print(error)
		#pprint.pprint(traceback.format_exception(type(error), error, error.__traceback__))

		if (ctx.guild):
			serverID = ctx.guild.id
		else:
			serverID = None

		authorID = ctx.author.id

		errorData = log_error(error, {"Server": serverID, "Author": authorID})

		await ctx.send(f"The following error has occurred: \"{str(error)}\"")
		await ctx.send(f"_Error has been logged as <{errorData['Error Time']}>._")

		print(f"Above error has been handled!\n")
		
		
	@commands.command()
	async def error(self, ctx, **args):
		await ctx.send("Testing error logging...")
		raise Exception("Testing error logging from command!")
		
def setup(client):
	client.add_cog(ErrorLogger(client))