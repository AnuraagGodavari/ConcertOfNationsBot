import json, datetime, pprint, traceback

import discord
from discord.ext import commands

from common import *
from database import *

#Log an error
def logerror(error, serverID, authorID):
	
	errorTime = str(datetime.datetime.now())
	
	errorData = {
		"ctx": {
			"Author ID": authorID,
			"Server ID": serverID
		},
		"Error Time": errorTime,
		"Exception": str(error),
		"Stack Trace": traceback.format_exception(type(error), error, error.__traceback__)
	}

	for char in ('-', ':', '.'):
		errorTime = errorTime.replace(char, '')

	try:errorFilename
		with open(f"ErrorLogs/{errorTime}.json", 'w') as json_file:
			json.dump(errorData, json_file, indent = 4)

		print(f"Above error has been saved with code <{errorTime}>")

	except: 
		with open(f"{logs_dir}/cmderror_{errorTime}.json", 'w') as f:
			f.write("THE FOLLOWING ERROR HAS NOT BEEN HANDLED PROPERLY:\n")
			f.write(str(errorData))
			f.close()
			
	return errorData

#The cog itself
class Logger(commands.Cog):
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

		errorData = logerror(error, serverID, authorID)

		await ctx.send(f"The following error has occurred: \"{str(error)}\"")
		await ctx.send(f"_Error has been logged as <{errorData['Error Time']}>._")

		print(f"Above error has been handled!\n")
		
		
	@commands.command()
	async def error(self, ctx, **args):
		await ctx.send("Testing error logging...")
		raise Exception("Testing error logging from command!")
		
def setup(client):
	client.add_cog(Logger(client))