import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='t!', intents=intents)

actualQueue = []  # Sua lista para armazenar os jogadores na fila

@client.event
async def on_ready():
    print(f'Bot pronto como {client.user.name}')

@client.command()
async def queue(msg):
    actualQueue.append(msg.author)
    await msg.send(f'{msg.author.mention} foi adicionado à fila.')
    if actualQueue.len >= 10:
        start(actualQueue[:10])

@client.command()
async def show_queue(msg):
    queue_list = "\n".join([member.name for member in actualQueue])
    await msg.send(f"Jogadores na fila:\n{queue_list}")

def start(players):
    time1 = []
    time2 = []

client.run("MTE0MjIwMDkwMTU2NjcyNjE0NA.GIDm8X.GkOmoPQO15-c0PJMnWwClqtgUZ5GzHiS_1rSOI")