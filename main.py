## Imports
import json

import discord
from discord.ext import commands

import sqlalchemy
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='t!', intents=intents)


## Banco De Dados

engine = sqlalchemy.create_engine('sqlite:///cs.db', echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    idUser = Column(BigInteger, primary_key=True)
    IdGuild = Column(BigInteger, primary_key=True)
    win = Column(Integer)
    lose = Column(Integer)
    pdl = Column(Integer)

    def __repr__(self):
        return "<User(idUser={}, idGuild={}, pdl={})".format(self.idUser,self.IdGuild,self.pdl)
    


class Partida(Base):
    __tablename__ = 'partidas'

    idPartida = Column(Integer, primary_key=True)
    vencedor = Column(String)
    equipe1 = Column(String) 
    equipe2 = Column(String)

    def __init__(self, equipe1, equipe2):
        self.equipe1 = json.dumps(equipe1)
        self.equipe2 = json.dumps(equipe2)

    def get_equipe1(self):
        return json.loads(self.equipe1)

    def get_equipe2(self):
        return json.loads(self.equipe2)

    def __repr__(self):
        return "<User(idPartida={}, equipe1={},equipe2={}, ganhador={})".format(self.idPartida,self.equipe1,self.equipe2,self.vencedor)

Base.metadata.create_all(engine)


## Codigo Bot

actualQueue = [] 

@client.event
async def on_ready():
    print(f'Bot pronto como {client.user.name}')

@client.command()
async def queue(ctx):

    user_id = ctx.author.id
    guild_id = ctx.guild.id

    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    
    user = session.query(User).filter_by(idUser=user_id, IdGuild=guild_id).first()

    if not user:
        new_user = User(idUser=user_id, IdGuild=guild_id, win=0, lose=0, pdl=20)
        session.add(new_user)
        session.commit()

    actualQueue.append(ctx.author)

    await ctx.send(f'{ctx.author.mention} foi adicionado à fila.')
    if len(actualQueue) >= 2:
        await startPartida(actualQueue[:2], ctx)

@client.command()
async def show_queue(ctx):
    queue_list = "\n".join([member.name for member in actualQueue])
    await ctx.send(f"Jogadores na fila:\n{queue_list}")

async def startPartida(players,ctx):
    time1 = players[:1]
    time2 = players[1:]

    time1_mention = ", ".join([player.mention for player in time1])
    time2_mention = ", ".join([player.mention for player in time2])

    message = "Times criados:\n"
    message += f"Time 1: {time1_mention}\n"
    message += f"Time 2: {time2_mention}"

    # Enviar a mensagem para o canal
    # Certifique-se de que você tenha o contexto (ctx) disponível para enviar a mensagem
    # ctx é o contexto do comando original que invocou a função startPartida
    await ctx.send(message)


## Startando Bot
client.run("MTE0MjIwMDkwMTU2NjcyNjE0NA.GIDm8X.GkOmoPQO15-c0PJMnWwClqtgUZ5GzHiS_1rSOI")