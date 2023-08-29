## Imports
import json

import discord
from discord.ext import commands

import sqlalchemy
from sqlalchemy import Column, Integer, String, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='t!', intents=intents)

## Id's dos Admin
admin = [248549066672308225, 330553991433945088, 355120851970031628]

## Banco De Dados

engine = sqlalchemy.create_engine('sqlite:///cs.db', echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    idUser = Column(BigInteger, primary_key=True)
    IdGuild = Column(BigInteger, primary_key=True)
    nome = Column(String)
    win = Column(Integer)
    lose = Column(Integer)
    pdl = Column(Integer)

    def to_dict(self):
        return {
            "idUser": self.idUser,
            "IdGuild": self.IdGuild,
            "nome": self.nome,
            "win": self.win,
            "lose": self.lose,
            "pdl": self.pdl
        }

    def __repr__(self):
        return "<User(idUser={}, idGuild={}, nome={}, pdl={})".format(self.idUser,self.IdGuild,self.nome,self.pdl)
    

class Partida(Base):
    __tablename__ = 'partidas'

    idPartida = Column(Integer, primary_key=True,autoincrement=True)
    vencedor = Column(String)
    time1 = Column(String)
    time2 = Column(String)

    def __init__(self, time1, time2):
        self.time1 = json.dumps([user.to_dict() for user in time1])
        self.time2 = json.dumps([user.to_dict() for user in time2])
        self.vencedor = None

    def get_time1(self):
        return [User(**data) for data in json.loads(self.time1)]

    def get_time2(self):
        return [User(**data) for data in json.loads(self.time2)]

    def __repr__(self):
        return "<User(idPartida={}, time1={},time2={}, ganhador={})".format(self.idPartida,self.time1,self.time2,self.vencedor)

Base.metadata.create_all(engine)


## Codigo Bot

guild_queues = {}

@client.event
async def on_ready():
    print(f'Bot pronto como {client.user.name}')

@client.command()
async def go(ctx):
    guild_id = ctx.guild.id

    if guild_id not in guild_queues:
        guild_queues[guild_id] = []

    user_id = ctx.author.id

    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    
    user = session.query(User).filter_by(idUser=user_id, IdGuild=guild_id).first()

    if not user:
        user = User(idUser=user_id, IdGuild=guild_id, nome=ctx.author.name, win=0, lose=0, pdl=20)
        session.add(user)
        session.commit()

    if user.idUser not in (member.idUser for member in guild_queues[guild_id]):
        guild_queues[guild_id].append(user)
        await ctx.send(f'{ctx.author.mention} foi adicionado à fila.')
    else:
        await ctx.send(f'{ctx.author.mention} já está na fila.')     

    await queue(ctx)

    if len(guild_queues[guild_id]) >= 10:
        await startPartida(guild_queues[guild_id][:10], ctx)
        guild_queues[guild_id][:10] = []

@client.command()
async def leave(ctx):
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    
    user = session.query(User).filter_by(idUser=user_id, IdGuild=guild_id).first()

    if user and user.idUser in [member.idUser for member in guild_queues.get(guild_id, [])]:
        guild_queues[guild_id] = [member for member in guild_queues[guild_id] if member.idUser != user.idUser]
        await ctx.send(f'{ctx.author.mention} saiu da fila.')
    else:
        await ctx.send(f'{ctx.author.mention} nao esta na fila.')

    await queue(ctx)


@client.command()
async def queue(ctx):
    guild_id = ctx.guild.id

    if guild_id not in guild_queues:
        await ctx.send("Nenhum jogador na fila.")
        return

    print(guild_queues[guild_id])
    queue_list = "\n".join(user.nome for user in guild_queues[guild_id])
    await ctx.send(f"Jogadores na fila:\n{queue_list}")

async def startPartida(players, ctx):
    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    
    players.sort(key=lambda player: player.pdl, reverse=True)

    time1 = []
    time2 = []

    for index, player in enumerate(players):
        if index % 2 == 0:
            time1.append(player)
        else:
            time2.append(player)

    partida = Partida(time1, time2)

    session.add(partida)
    session.commit()

    time1_mention = ", ".join([player.nome for player in time1])
    time2_mention = ", ".join([player.nome for player in time2])

    message = "Times criados:\n"
    message += f"Id da Partida = {partida.idPartida}\n"
    message += f"Time 1: {time1_mention}\n"
    message += f"Time 2: {time2_mention}"

    await ctx.send(message)

@client.command()
async def rank(ctx):
    session = sqlalchemy.orm.sessionmaker(bind=engine)()

    guild_id = ctx.guild.id
    users = session.query(User).filter_by(IdGuild=guild_id).order_by(User.pdl.desc()).all()

    rank_message = "Ranking:\n"
    for index, user in enumerate(users, start=1):
        rank_message += f"{index}. {user.nome} -> Vitorias: {user.win}, PDL: {user.pdl}\n"

    await ctx.send(rank_message)

@client.command()
async def end(ctx, id_partida: int, time_vencedor: str):

    if ctx.author.id not in admin:
        return
    
    try:
      session = sqlalchemy.orm.sessionmaker(bind=engine)()
  
      partida = session.query(Partida).filter_by(idPartida=id_partida).first()
  
      if not partida:
          await ctx.send(f"Partida com ID {id_partida} não encontrada.")
          return
      if partida.vencedor is not None:
          await ctx.send(f"Partida com ID {id_partida} já encerrada.")
          return
      if time_vencedor not in ['time1', 'time2']:
          await ctx.send("Time vencedor inválido. Use 'time1' ou 'time2'.")
          return
  
      partida.vencedor = time_vencedor
      session.commit()
      await ctx.send(f"Partida com ID {id_partida} encerrada. Time vencedor: {time_vencedor}")
    except Exception as e:
      await ctx.send("Ocorreu um erro ao encerrar a partida.")
      session.close()
      print(e)
      return
        

    partida.vencedor = time_vencedor
    session.commit()

    equipe_vencedora = partida.get_time1() if time_vencedor == 'time1' else partida.get_time2()
    equipe_perdedora = partida.get_time2() if time_vencedor == 'time1' else partida.get_time1()

    vencedores = []

    for user in equipe_vencedora:
        userAtt = session.query(User).filter_by(idUser=user.idUser, IdGuild=ctx.guild.id).first()
        userAtt.win += 1
        userAtt.pdl += 7
        vencedores.append(userAtt)
        session.commit()

    for user in equipe_perdedora:
        userAtt = session.query(User).filter_by(idUser=user.idUser, IdGuild=ctx.guild.id).first()
        userAtt.pdl -= 7
        userAtt.lose += 1
        
        if userAtt.pdl < 0:
                userAtt.pdl = 0
        session.commit()

    mensagem = "\n".join([vencedor.nome for vencedor in vencedores])


    await ctx.send(f"Partida {id_partida} encerrada. Time vencedor: {mensagem}")

## Startando Bot
client.run("MTE0MjIwMDkwMTU2NjcyNjE0NA.G-rtme._7jYoevo2tJk5cn2cc5RwIyy8sZ99xj1ics8gQ")
