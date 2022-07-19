import json, datetime, pprint, traceback

import discord
from discord.ext import commands

from common import *
from database import *


#The cog itself

class Logger(commands.Cog):
	""" A cog that allows its client bot to watch member statuses """
	
	def __init__(self, client):
		self.client = client
		
		   
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		errorTime = str(datetime.datetime.now())
		
		print(error)
		#pprint.pprint(traceback.format_exception(type(error), error, error.__traceback__))
		
		if (ctx.guild):
			serverID = ctx.guild.id
		else:
			serverID = None
		
		errorData = {
			"ctx": {
				"Author ID": ctx.author.id,
				"Server ID": serverID
			},
			"Error Time": errorTime,
			"Exception": str(error),
			"Stack Trace": traceback.format_exception(type(error), error, error.__traceback__)
		}
		
		for char in ('-', ':', '.'):
			errorTime = errorTime.replace(char, '')
		
		try:
			with open(f"ErrorLogs/{errorTime}.json", 'w') as json_file:
				json.dump(errorData, json_file, indent = 4)
				
			print(f"Above error has been saved with code <{errorTime}>")
				
		except: 
			with open(f"{logs_dir}/cmderror_{errorTime}.json", 'w') as f:
				f.write("THE FOLLOWING ERROR HAS NOT BEEN HANDLED PROPERLY:\n")
				f.write(str(errorData))
				f.close()
		
		await ctx.send(f"The following error has occurred: \"{str(error)}\"")
		await ctx.send(f"_Error has been logged as <{errorTime}>._")
		
		print(f"Above error has been handled!\n")
		
	'''	   
	@commands.Cog.listener()
	async def on_error(self, ctx, error):
		errorTime = str(datetime.datetime.now())
		
		pprint.pprint(traceback.format_exception(type(error), error, error.__traceback__))
		
		if (ctx.guild):
			serverID = ctx.guild.id
		else:
			serverID = None
		
		errorData = {
			"ctx": {
				"Author ID": ctx.author.id,
				"Server ID": serverID
			},
			"Error Time": errorTime,
			"Exception": str(error),
			"Stack Trace": traceback.format_exception(type(error), error, error.__traceback__)
		}
		
		for char in ('-', ':', '.'):
			errorTime = errorTime.replace(char, '')
		
		try:
			with open(f"ErrorLogs/{errorTime}.json", 'w') as json_file:
				json.dump(errorData, json_file, indent = 4)
				
			print(f"Above error has been saved with code <{errorTime}>")
				
		except: 
			with open(f"{logs_dir}/error{errorTime}.json", 'w') as f:
				f.write("THE FOLLOWING ERROR HAS NOT BEEN HANDLED PROPERLY:\n")
				f.write(str(errorData))
				f.close()
		
		await ctx.send(f"The following error has occurred: \"{str(error)}\"")
		await ctx.send(f"_Error has been logged as <{errorTime}>._")
		
		print(f"Above error has been handled!\n")
	'''
		
	@commands.command()
	async def error(self, ctx, **args):
		await ctx.send("Testing error logging...")
		raise Exception("Testing error logging!")
		
def setup(client):
	client.add_cog(Logger(client))