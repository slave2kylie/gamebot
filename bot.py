from typing import Optional, Union, List

import discord
import os
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import commands
import Incoherent
import db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True
client = commands.Bot(intents=intents,command_prefix='/')


async def incoherent_autocomplete(interaction: discord.Interaction,current: str) -> List[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=msg, value=msg)
        for msg in db.Incoherent_Keys if current.lower() in msg.lower()
    ]


def is_owner(interaction: discord.Interaction):
    if interaction.user.id == interaction.guild.owner_id:
        return True
    else:
        return False

def check_command_permission(interaction: discord.Interaction):
    cmdrole = dbi.get(str(interaction.guild_id),db.KEYS.CMD_ROLE)
    for role in interaction.user.roles:
        if(role.name == cmdrole):
            return True
    return False




@client.tree.command()
@app_commands.autocomplete(genre=incoherent_autocomplete)
async def incoherent(interaction: discord.Interaction,genre: str):
     print('inside command incoherent')
     Incoherent.cleardata(interaction.channel_id)
     v=Incoherent.IncoherentView(genre,client,interaction.user.id)
     await interaction.response.send_message("Game Invite",view=v)
     return


@client.tree.command(name='setup')
@app_commands.check(is_owner)
async def setup(interaction: discord.Interaction,embed_color: str,role: discord.Role):
    """Set up bot for this server"""
    print("inside setup")
    embed_color="0x"+embed_color
    embed_color_int=int(embed_color,16)
    role_name=role.name
    guild_id=str(interaction.guild_id)
    db.set(guild_id,db.KEYS.EMBED_COLOR,embed_color_int)
    db.set(guild_id,db.KEYS.CMD_ROLE,role_name)
    await interaction.response.send_message('Set up complete',ephemeral=True)
    return

@setup.error
async def setup_error(interaction: discord.Interaction,error):
    print("setup_error",error)
    await interaction.response.send_message("Only the server owner can access this command",ephemeral=True)
    return



@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

    #print(cmdrole)
    #client.tree = app_commands.CommandTree(client)
    for guild in client.guilds:
        print("id: ",guild.id,"name: ",guild.name)
        client.tree.copy_global_to(guild=guild)
        await client.tree.sync(guild=guild)
    return

@client.event
async def on_guild_join(guild):
    print("on_guild_join")
    client.tree.copy_global_to(guild=guild)
    await client.tree.sync(guild=guild)
    return

client.run(TOKEN)
