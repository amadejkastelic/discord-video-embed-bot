import os
import random

import discord

from downloader import registry

emoji = ['😼', '😺', '😸', '😹', '😻', '🙀', '😿', '😾', '😩']


class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}')

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        try:
            client = registry.get_instance(url=message.content.strip())
        except Exception:
            return

        await message.delete()
        new_message = await message.channel.send('🔥 Working on it 🥵')

        video = await client.download()

        await message.channel.send(
            content=f'Here you go {message.author.mention} {random.choice(emoji)}.',
            file=discord.File(fp=video, filename='video.mp4'),
        )
        await new_message.delete()


intents = discord.Intents.default()
intents.message_content = True
client = DiscordClient(intents=intents)
client.run(os.environ['DISCORD_API_TOKEN'])
