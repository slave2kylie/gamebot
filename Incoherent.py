import asyncio
import discord
from discord import app_commands
import utils
import random
import db
from types import SimpleNamespace

players_joined = {None:{None:None}}
players_score = {None:{None:None}}

class IncoherentView(discord.ui.View):
    def __init__(self,genre,client,user_id):
        super().__init__()
        print('inside IncoherentView')
        self.genre=genre
        self.client=client
        self.user_id=user_id

    @discord.ui.button(label="Start",style=discord.ButtonStyle.blurple)
    async def Start(self,interaction:discord.Interaction,button:discord.ui.Button):
        if self.user_id != interaction.user.id:
            await interaction.response.send_message('Only the user who has invited can start the game',ephemeral=True)
            return
        self.clear_items()
        key=str(interaction.channel_id)
        if players_joined.get(key)==None:
            players_joined[key]={None:None}
        players_joined[key][interaction.user.name]=1
        embed=discord.Embed()
        embed.description="Game has started"
        await interaction.response.edit_message(embed=embed,view=self)
        self.client.loop.create_task(incoherent(self.client,interaction,self.genre,self.user_id))
        return
    
    @discord.ui.button(label="Join",style=discord.ButtonStyle.green)
    async def Join(self,interaction:discord.Interaction,button:discord.ui.Button):
        print('inside joined')
        key=str(interaction.channel_id)
        if players_joined.get(key)==None:
            players_joined[key]={None:None}
        players_joined[key][interaction.user.name]=1
        await interaction.response.send_message('You have joined the game',ephemeral=True)
        return
    
   
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

async def sleeper_task(event):
    print(f'sleeper_task')
    await asyncio.sleep(30)
    event.set()
    return

async def incoherent_task(client,channel,genre,user_id):
    print('inside incoherent_task')
    a = []
    genreval=db.Incoherent[genre]
    l = len(genreval)
    for x in range(l):
        a.append(x)
    random.shuffle(a)
    print(a)
    print(len(a))
    while len(a)>0:
        print('outer_loop')
        b=[]
        for x in range(len(a)):
            print('inner_loop')
            print(f'card {a[x]} is shown')
            ret=SimpleNamespace()
            ret.r=0
            event = asyncio.Event(loop=client.loop)
            lock = asyncio.Lock()
            task1=client.loop.create_task(incoherent_task1(client,channel,genreval[a[x]],user_id,event,lock,ret))
            task2=client.loop.create_task(sleeper_task(event))
            print('waiting for event')
            await event.wait()
            print('got event')
            await lock.acquire()
            task1.cancel()
            task2.cancel()
            lock.release()
            if ret.r==0:
                b.append(a[x])                

            print(f'res:{ret.r}')
            if ret.r==2:
                print('cancelled, so returning')
                return
        a=b
        random.shuffle(a)
    return

async def incoherent_task1(client,channel,val,user_id,event,lock,ret):
    print(f'inside incoherent_task1 ')
    question=val[db.INCOHERENT_KEYS.QUESTION]
    hint=val[db.INCOHERENT_KEYS.HINT]
    answer=val[db.INCOHERENT_KEYS.ANSWER]
    print(f'{question},{hint},{answer}')
    await send_embed_to_channel(channel,question,None)
    while True:
        def check(m):
            print(f'inside check {m.content}')
            if m.channel==channel:
                return True
            return False
        m=await client.wait_for('message',check=check)

        cstr=m.content
        author=m.author.name
        print(f'cstr:{cstr},author:{author},author_id:{m.author.id}')
        if cstr=='hint':
            await send_embed_to_channel(channel,hint,None)
        if cstr=='cancel' and m.author.id==user_id:
            ret.r=2
            event.set()
            return
        if cstr==answer:
            key=str(channel.id)
            key2=str(channel.id)
            if players_joined.get(key2) != None:
                if players_joined[key2].get(author) != None:
                    await lock.acquire()
                    v=0
                    if players_score.get(key)==None:
                        players_score[key]={None:None}
                    if players_score[key].get(author)==None:
                        players_score[key][author]=1
                    else:
                        v=players_score[key][author]
                        players_score[key][author]=v+1
                    await send_embed_to_channel(channel,f'congrats {author}, you have found the correct answer',None)
                    ret.r=1
                    if v+1==5: ret.r=2
                    event.set()
                    lock.release()
    return

async def incoherent(client,interaction,genre,user_id):
    print("inside incoherent")
    channel=interaction.channel

    await incoherent_task(client,channel,genre,user_id)
    s='SCORE CARD\n'
    key1=str(interaction.channel_id)
    key2=str(interaction.channel_id)
   
    ld=dict()

    if players_joined.get(key1)!=None:
        for k in players_joined[key1]:
            scr=0
            if players_score[key2].get(k)!=None:
                scr=players_score[key2][k]
                ld[f'{k}']=scr
    #        if k!=None: s+=f'\n{k}  :  {scr}'

    print(ld)
    if len(ld) >0:
        lst=sorted(ld.items(),key=lambda x:x[1],reverse=True)
        ky,vl= lst[0]
        
        for k,v in lst:
            s+=f'\n{k}   :  {v}'
            if v==vl:s+=' 🎉'
    await send_embed_to_channel(channel,s,None)
    return

def cleardata(channel_id):
    print ('inside cleardata')
    key1=str(channel_id)
    key2=str(channel_id)
    print('before popping')
    print(players_joined)
    print(players_score)
    if(players_joined.get(key1)!=None):
        players_joined.pop(key1)
    if(players_score.get(key2)!=None):
        players_score.pop(key2)
    print('after popping')
    print(players_joined)
    print(players_score)
