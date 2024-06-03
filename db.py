import json

mp={"0":"0"}

global Incoherent

with open('Incoherent.json') as f:
    global Incoherent
    Incoherent=json.load(f)
    print(f'loaded Incoherent.json {Incoherent}')

Incoherent_Keys=[]
for key in Incoherent:
    Incoherent_Keys.append(key)
print(f'(loaded incoherent keys,{Incoherent_Keys}')

class KEYS:
    CMD_ROLE = 'cmd_role'
    EMBED_COLOR = 'embed_color'

class INCOHERENT_KEYS:
    QUESTION = 'question'
    QUESTION_URL = 'question_url'
    HINT = 'hint'
    HINT_URL = 'hint_url'
    ANSWER = 'answer'
    ANSWER_URL = 'answer_url'

def set(guild:str,key:str,value):
    global mp
    mp[guild+key]=value
    
def get(guild:str,key:str):
    global mp
    return mp.get(guild+key)
