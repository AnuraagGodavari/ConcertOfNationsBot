import discord
import os
from discord.ext import commands

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *

class HelpCommand(commands.HelpCommand):

    def __init__(self):
        super().__init__()

    #Default help command without any expected optional arguments
    async def send_bot_help(self, mapping):

        ctx = self.context

        menu = MenuEmbed(
            f"Command Cogs", 
            "_Cogs group together commands of a similar type.\nUse the command \"help <cog name>\" to see a cog's commands._", 
            ctx.author.id,
            fields = [
                (cog.qualified_name,
                inspect.getdoc(cog))
                for cog in mapping
                if cog
            ] + [
                ("Other", '\n'.join([command.name for command in mapping[None]]))
            ],
            pagesize = 9,
            isPaged = True
            )

        assignMenu(ctx.author.id, menu)

        logInfo(f"Created help command cogs menu and assigned it to player {ctx.author.id}")

        await ctx.send(embed = menu.toEmbed(), view = menu.embedView())

    #Pass in the name of a cog
    async def send_cog_help(self, cog):
        return await super().send_cog_help(cog)

    #Pass in a name for a group of commands
    async def send_group_help(self, group):
        return await super().send_group_help(group)

    #Pass in the name of a command
    async def send_command_help(self, command):
        return await super().send_command_help(command)