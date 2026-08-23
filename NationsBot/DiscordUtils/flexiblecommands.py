from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

from common import *
from database import *
from logger import *

from DiscordUtils.menuembed import *
from DiscordUtils.getgameinfo import *

async def handle_command(command):

    async def handler(ctx, *args, **kwargs):

        result = await command(ctx, *args, **kwargs)

        if (type(result) == MenuEmbed):
            await ctx.send(
                embed = result.toEmbed(),
                view = result.embedView()
                )

    return handler

async def handle_interaction(client, interaction, command, *args, **kwargs):

    ctx = await client.get_context(interaction)

    result = await command(client, ctx, *args, **kwargs)

    # A menu object which can turn into an embed with interactable features
    if (type(result) == MenuEmbed):
        await interaction.response.send_message(
            embed = result.toEmbed(),
            view = result.embedView(),
            ephemeral = True
            )
    
    # A set of parameters for ctx.send
    elif (type(result) == dict):
        if "content" in result.keys():
            await interaction.response.send_message(
                **result,
                ephemeral = True
            )

        if "file" in result.keys():
            result["file"].close()

    # A string for ctx.send
    elif (type(result) == str):
        await interaction.response.send_message(
            content = result,
            ephemeral = True
        )

async def add_flexible_command(client, command):

    client.add_command(
        commands.Command(
            await handle_command(command),
            name = command.__name__
            )
        )