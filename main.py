import discord

intents = discord.Intents.default()  # Define os intents padrão
intents.message_content = True       # Permite o acesso ao conteúdo das mensagens

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run("MTE0MjIwMDkwMTU2NjcyNjE0NA.GIDm8X.GkOmoPQO15-c0PJMnWwClqtgUZ5GzHiS_1rSOI")