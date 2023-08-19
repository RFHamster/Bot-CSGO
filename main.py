## Imports

import discord
from discord.ext import commands

import sqlalchemy
from sqlalchemy import Column, Integer, String, BigInteger
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
    # if len(actualQueue) >= 10:
    #     start(actualQueue[:10])

@client.command()
async def show_queue(ctx):
    queue_list = "\n".join([member.name for member in actualQueue])
    await ctx.send(f"Jogadores na fila:\n{queue_list}")

# def start(players):
#     time1 = []
#     time2 = []


## Startando Bot
client.run("MTE0MjIwMDkwMTU2NjcyNjE0NA.GIDm8X.GkOmoPQO15-c0PJMnWwClqtgUZ5GzHiS_1rSOI")