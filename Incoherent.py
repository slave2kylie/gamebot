import asyncio
import discord
from discord import app_commands
import utils
import random
import db

def get_random_obj(s:str):
    print('inside get_random_obj')
    genre=db.Incoherent[s]
    print(genre)
    l = len(genre)
    print(l)
    r=random.randint(0,l-1)
    return genre[r]
    
async def send_embed_to_channel(channel,msg,url):
    print('inside send_embed_to_channel')
    embed=discord.Embed()
    print(f'{msg},{url}')
    embed.description=msg
    if url!= None:
        f = discord.File(url,filename='image.png')
        print('loaded file')
        embed.set_image(url='attachment://image.png')
        print('set embed url')
        await channel.send(file=f,embed=embed)
        print('after send')
    else:
        await channel.send(embed=embed)
    return

async def sleeper_task(task,time):
    print(f'sleeper_task {time}')
    await asyncio.sleep(time)
    print('canceling task')
    task.cancel()
    return

async def incoherent_task(client,channel,genre):
    print(f'inside incoherent_task {genre}')
    val=get_random_obj(genre)
    print(val)
    question=val[db.INCOHERENT_KEYS.QUESTION]
    hint=val[db.INCOHERENT_KEYS.HINT]
    answer=val[db.INCOHERENT_KEYS.ANSWER]
    print(f'{question},{hint},{answer}')
    qurl=None
    hurl=None
    aurl=None
    if val.get(db.INCOHERENT_KEYS.QUESTION_URL) !=None: qurl=val[db.INCOHERENT_KEYS.QUESTION_URL]
    if val.get(db.INCOHERENT_KEYS.HINT_URL) != None: hurl=val[db.INCOHERENT_KEYS.HINT_URL]
    if val.get(db.INCOHERENT_KEYS.ANSWER_URL) != None: aurl=val[db.INCOHERENT_KEYS.ANSWER_URL]
    print('assigned urls')
    print(f'{qurl},{hurl},{aurl}')
    await send_embed_to_channel(channel,question,qurl)
    setHint=True
    exitTask=False
    while True:
        print('incoherent_task')
        def check(m):
            print(f'inside check {m.content}')
            if m.channel==channel:
                return True
            return False
        
        m=await client.wait_for('message',check=check)
        cstr=m.content
        author=m.author.name
        print(f'cstr:{cstr},author:{author}')
        if cstr=='$hint' and setHint==True:
            setHint=False
            await send_embed_to_channel(channel,hint,hurl)
        if cstr==answer:
            exitTask=True
            await send_embed_to_channel(channel,f'congrats {author}, you have found the correct answer',aurl)

        if exitTask==True:
            return
    return

async def incoherent(client,interaction,genre):
    print("inside incoherent")
    channel=interaction.channel

    task=client.loop.create_task(incoherent_task(client,channel,genre))
    client.loop.create_task(sleeper_task(task,60))
    await interaction.response.send_message('Incoherent started',ephemeral=True)
    return


