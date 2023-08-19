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

    def __repr__(self):
        return "<User(idUser={}, idGuild={}, pdl={})".format(self.idUser,self.IdGuild,self.pdl)
    

class Partida(Base):
    __tablename__ = 'partidas'

    idPartida = Column(Integer, primary_key=True,autoincrement=True)
    vencedor = Column(String)
    time1 = Column(String)
    time2 = Column(String)

    def __init__(self, time1, time2):
        self.time1 = json.dumps(time1)
        self.time2 = json.dumps(time2)

    def get_time1(self):
        return json.loads(self.time1)

    def get_time2(self):
        return json.loads(self.time2)

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

    # Verifique se a guilda já possui uma fila, senão crie uma
    if guild_id not in guild_queues:
        guild_queues[guild_id] = []

    user_id = ctx.author.id

    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    
    user = session.query(User).filter_by(idUser=user_id, IdGuild=guild_id).first()

    if not user:
        new_user = User(idUser=user_id, IdGuild=guild_id, nome=ctx.author.name, win=0, lose=0, pdl=20)
        session.add(new_user)
        session.commit()

    if ctx.author in guild_queues[guild_id]:
        await ctx.send(f'{ctx.author.mention} já está na fila.')
    else:
        guild_queues[guild_id].append(ctx.author)
        await ctx.send(f'{ctx.author.mention} foi adicionado à fila.')

    await queue(ctx)

    if len(guild_queues[guild_id]) >= 2:
        await startPartida(guild_queues[guild_id][:2], ctx)
        guild_queues[guild_id][:2] = []

@client.command()
async def leave(ctx):
    guild_id = ctx.guild.id
    user_id = ctx.author

    if user_id in guild_queues[guild_id]:
        guild_queues[guild_id].remove(user_id)
        await ctx.send(f"{ctx.author.mention} saiu da fila.")
    else:
        await ctx.send(f"{ctx.author.mention} não está na fila.")

    await queue(ctx)

@client.command()
async def queue(ctx):
    guild_id = ctx.guild.id

    if guild_id not in guild_queues:
        await ctx.send("Nenhum jogador na fila.")
        return

    queue_list = "\n".join([member.name for member in guild_queues[guild_id]])
    await ctx.send(f"Jogadores na fila:\n{queue_list}")

async def startPartida(players, ctx):
    
    time1 = [player.id for player in players[:1]]
    time2 = [player.id for player in players[1:]]

    partida = Partida(time1, time2)

    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    session.add(partida)
    session.commit()

    time1_mention = ", ".join([player.mention for player in players[:1]])
    time2_mention = ", ".join([player.mention for player in players[1:]])

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
    session = sqlalchemy.orm.sessionmaker(bind=engine)()

    partida = session.query(Partida).filter_by(idPartida=id_partida).first()

    if not partida:
        await ctx.send(f"Partida com ID {id_partida} não encontrada.")
        return

    if time_vencedor not in ['time1', 'time2']:
        await ctx.send("Time vencedor inválido. Use 'time1' ou 'time2'.")
        return

    partida.vencedor = time_vencedor
    session.commit()

    equipe_vencedora = partida.get_time1() if time_vencedor == 'time1' else partida.get_time2()

    vencedores = []

    # Atualizar vitórias e derrotas dos usuários
    for user_id in partida.get_time1() + partida.get_time2():
        user = session.query(User).filter_by(idUser=user_id, IdGuild=ctx.guild.id).first()

        if user:
            if user_id in partida.get_time1() and time_vencedor == 'time1':
                user.win += 1
                user.pdl += 7
                vencedores.append(user)
            elif user_id in partida.get_time2() and time_vencedor == 'time2':
                user.win += 1
                user.pdl += 7
                vencedores.append(user)
            else:
                user.lose += 1
                user.pdl -= 7
                if user.pdl < 0:
                    user.pdl = 0

    session.commit()

    mensagem = "\n".join([vencedor.nome for vencedor in vencedores])


    await ctx.send(f"Partida {id_partida} encerrada. Time vencedor: {mensagem}")

## Startando Bot
client.run("MTE0MjIwMDkwMTU2NjcyNjE0NA.GIDm8X.GkOmoPQO15-c0PJMnWwClqtgUZ5GzHiS_1rSOI")