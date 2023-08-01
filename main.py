import logging
import os
import random
import re
import typing

import discord

from downloader import registry

emoji = ['😼', '😺', '😸', '😹', '😻', '🙀', '😿', '😾', '😩', '🙈', '🙉', '🙊', '😳']


class DiscordClient(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged on as {self.user}')

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        url = self._find_first_url(message.content)
        if not url:
            return

        try:
            client = registry.get_instance(url=url)
        except Exception:
            return

        await message.delete()
        new_message = await message.channel.send('🔥 Working on it 🥵')

        try:
            text, video = await client.download()
        except Exception as e:
            logging.error(f'Failed downloading {url}: {str(e)}')
            new_message.edit(f'Failed downloading {url}. {message.author.mention}')
            return

        await message.channel.send(
            content=f'Here you go {message.author.mention} {random.choice(emoji)}.\n{text}',
            file=discord.File(fp=video, filename='video.mp4'),
            suppress_embeds=True,
        )
        await new_message.delete()

    def _find_first_url(self, string: str) -> typing.Optional[str]:
        urls = re.findall(r'(https?://[^\s]+)', string)
        return urls[0] if urls else None


intents = discord.Intents.default()
intents.message_content = True
client = DiscordClient(intents=intents)

api_key = os.environ.get('DISCORD_API_TOKEN')
if not api_key:
    raise RuntimeError('DISCORD_API_TOKEN environment variable not set, plesae set it to a valid value and try again.')

client.run(api_key)
