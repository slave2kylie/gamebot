from typing import Optional, Union, List

import discord
import os
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import commands
import Incoherent
import db
import random

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
    cmdrole = db.get(str(interaction.guild_id),db.KEYS.CMD_ROLE)
    for role in interaction.user.roles:
        if(role.name == cmdrole):
            return True
    return False




@client.tree.command()
@app_commands.autocomplete(genre=incoherent_autocomplete)
async def incohearent(interaction: discord.Interaction,genre: str):
    """Guess the gibberish"""
    await interaction.response.defer()
    print('inside command incoherent')
    Incoherent.cleardata(interaction.channel_id,True,interaction.user)
    guild_id=str(interaction.guild_id)
    embed=discord.Embed(color=db.get(guild_id,db.KEYS.EMBED_COLOR),title='**INCOHEARENT**')
    embed.description="> Guess the gibberish"
    name=interaction.user.nick
    if name==None: name=interaction.user.name
    embed.add_field(name="Players",value=name)
    v=Incoherent.IncoherentView(genre,client,interaction.user.id,embed)
    await interaction.followup.send(embed=embed,view=v)
    return


@client.tree.command(name='roll-dice')
async def roll_dice(interaction: discord.Interaction,sides:Optional[int]=6,amount:Optional[int]=1):
    """Roll some dice"""
    await interaction.response.defer()
    print('inside roll_dice')
    if amount>10: 
        await interaction.followup.send("Max only 10 dices are allowed")
        return
    rolls=[]
    for x in range(amount):
        rolls.append(random.randint(1,sides))
    
    guild_id=str(interaction.guild_id)
    embed=discord.Embed(color=db.get(guild_id,db.KEYS.EMBED_COLOR))
    embed.description=f'Lucky you! You just rolled:\n\n{str(rolls)[1:-1]}'
    #url="https://images.rawpixel.com/image_png_social_square/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTA4L3JtNTU4LWVsZW1lbnQtZGljZS1waW5rLTAwMS5wbmc.png"
    url="images/lowqualitypinkdices.png"
    f = discord.File(url,filename='image.png')
    #print('loaded file')
    embed.set_thumbnail(url='attachment://image.png')
    #print('set embed url')
    await interaction.followup.send(file=f,embed=embed)
    return

@client.tree.command(name='8-ball')
async def eight_ball(interaction: discord.Interaction,question: str):
    """Ask the magic 8-ball a question"""
    await interaction.response.defer()
    print('inside eight_ball')
    guild_id=str(interaction.guild_id)
    embed=discord.Embed(color=db.get(guild_id,db.KEYS.EMBED_COLOR),title='***Magic 8-Ball***')
   # s="Your Question\n"
    #s+=f'> {question}\n'
    #s+='The Answer\n'
    #s+=f'> {db.eight_ball[random.randint(0,len(db.eight_ball)-1)]}'
    embed.add_field(name="Your Question", value=f'> {question}',inline=False)
    embed.add_field(name='The Answer', value=f'> {db.eight_ball[random.randint(0,len(db.eight_ball)-1)]}',inline=False)
    
    #embed.description='> **Magic 8-ball**'
    #embed.description=s
    
    await interaction.followup.send(embed=embed)
    return

@client.tree.command(name='setup')
@app_commands.check(is_owner)
async def setup(interaction: discord.Interaction,embed_color: str,role: discord.Role):
    """Set up game-bot for this server"""
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