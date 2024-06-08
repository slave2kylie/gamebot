import asyncio
import discord
from discord import app_commands
import utils
import random
import db
from types import SimpleNamespace

players_joined = dict()
players_score = dict()

max_score=5
time_out=30

class IncoherentView(discord.ui.View):
    def __init__(self,genre,client,user_id,embed):
        super().__init__()
        print('inside IncoherentView')
        self.genre=genre
        self.client=client
        self.user_id=user_id
        self.embed=embed

    @discord.ui.button(label="Start",style=discord.ButtonStyle.blurple)
    async def Start(self,interaction:discord.Interaction,button:discord.ui.Button):
        print('inside Start')
        if self.user_id != interaction.user.id:
            await interaction.response.send_message('Only the user who has invited can start the game',ephemeral=True)
            return
        key=str(interaction.channel_id)
        print(f'players_joined: {players_joined}')
        if len(players_joined[key])<2:
            await interaction.response.send_message('You need atleast one more person to join the game',ephemeral=True)
            return

        self.clear_items()
        embed=discord.Embed()
        embed.description="Game has started"
        await interaction.response.edit_message(embed=embed,view=self)
        self.client.loop.create_task(incoherent(self.client,interaction,self.genre,self.user_id))
        return
    
    @discord.ui.button(label="Join",style=discord.ButtonStyle.green)
    async def Join(self,interaction:discord.Interaction,button:discord.ui.Button):
        print('inside joined')
        key=str(interaction.channel_id)
        name=interaction.user.nick
        if name==None:name=interaction.user.name
        players_joined[key][str(interaction.user.id)]=name
        self.embed.clear_fields()
        players_list=''
        for keys,val in players_joined[key].items():
            players_list+=val+'\n'
        players_list=players_list[:-1]
        self.embed.add_field(name="Players", value=players_list)
        await interaction.response.edit_message(embed=self.embed,view=self)
        
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
    await asyncio.sleep(time_out)
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
    
    while len(a)>0:
        print(a)
        b=[]
        for x in range(len(a)):
            print(f'{x} is chosen {a}')
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
                return 0
            if ret.r==3:
                print('Game finished')
                return 1
        a=b
        random.shuffle(a)
    return 1

async def incoherent_task1(client,channel,val,user_id,event,lock,ret):
    print(f'inside incoherent_task1 ')
    question=val[db.INCOHERENT_KEYS.QUESTION]
    hint=val[db.INCOHERENT_KEYS.HINT]
    answer=val[db.INCOHERENT_KEYS.ANSWER]
    description=''
    if val.get(db.INCOHERENT_KEYS.DESCRIPTION)!=None : description=val[db.INCOHERENT_KEYS.DESCRIPTION]
    print(f'{question},{hint},{answer},{description}')
    await send_embed_to_channel(channel,question,None)
    key=str(channel.id)
    setHint=True
    while True:
        def check(m):
            print(f'inside check {m.content}')
            if players_joined[key].get(str(m.author.id)) == None: return False
            if m.channel==channel: return True
            return False

        m=await client.wait_for('message',check=check)

        cstr=str(m.content).lower()
        author=m.author
        print(f'cstr:{cstr},author:{author},author_id:{m.author.id}')
        if cstr=='hint':
            if setHint:
                await send_embed_to_channel(channel,hint,None)
                setHint=False
            else:
                await send_embed_to_channel(channel,"Hint already given",None)
        elif cstr=='cancel' and author.id==user_id:
            ret.r=2
            event.set()
            return
        elif cstr==answer.lower():
            await lock.acquire()
            v=0
            if players_score[key].get(str(author.id))==None:
                players_score[key][str(author.id)]=1
            else:
                v=players_score[key][str(author.id)]
                players_score[key][str(author.id)]=v+1
            s=f'You got it <@{m.author.id}>\n\n'
            s+=f'The answer is **{answer}**\n\n'
            s+=f'***{description}***'
            await send_embed_to_channel(channel,s,None)
            ret.r=1
            if v+1>=max_score: ret.r=3
            event.set()
            lock.release()
            return
    return

async def incoherent(client,interaction,genre,user_id):
    print("inside incoherent")

    channel=interaction.channel

    gs=await incoherent_task(client,channel,genre,user_id)
    print(f'gs:{gs}')
    key=str(interaction.channel_id)
    s='***INCOHEARENT SCORE CARD***\n'
   
    ld=dict()

    for k,val in players_joined[key].items():
        scr=0
        if players_score[key].get(k)!=None:
            scr=players_score[key][k]
        ld[f'{val}']=scr
#        if k!=None: s+=f'\n{k}  :  {scr}'
    cleardata(interaction.channel_id, False, None)
    print(ld)
    if len(ld) >0:
        lst=sorted(ld.items(),key=lambda x:x[1],reverse=True)
        ky,vl= lst[0]
        
        for k,v in lst:
            s+=f'\n{k}   :  {v}'
            if gs==1:
                if v==vl:s+=' 🎉'
    await send_embed_to_channel(channel,s,None)
    return

def cleardata(channel_id,init,user):
    print ('inside cleardata')
    key=str(channel_id)
    print('before popping')
    print(players_joined)
    print(players_score)
    if(players_joined.get(key)!=None):
        players_joined.pop(key)
    if(players_score.get(key)!=None):
        players_score.pop(key)
    print('after popping')
    print(players_joined)
    print(players_score)
    if init:
        players_joined[key]=dict()
        players_score[key]=dict()
        name=user.nick
        if name==None: name=user.name
        players_joined[key][str(user.id)]=name

        print(f'players_joined: {players_joined}')
    return