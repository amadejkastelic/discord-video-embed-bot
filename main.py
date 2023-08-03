import io
import logging
import mimetypes
import os
import random
import re
import typing

import discord
import magic

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
            post = await client.get_post()
        except Exception as e:
            logging.error(f'Failed downloading {url}: {str(e)}')
            await new_message.edit(content=f'Failed downloading {url}. {message.author.mention}')
            raise e

        file = None
        if post.buffer:
            file = discord.File(
                fp=post.buffer,
                filename='{spoiler}file.{extension}'.format(
                    spoiler='SPOILER_' if post.spoiler else '',
                    extension=self._guess_extension_from_buffer(buffer=post.buffer),
                ),
            )

        await message.channel.send(
            content=f'Here you go {message.author.mention} {random.choice(emoji)}.\n{str(post)}',
            file=file,
            suppress_embeds=True,
        )
        await new_message.delete()

    def _find_first_url(self, string: str) -> typing.Optional[str]:
        urls = re.findall(r'(https?://[^\s]+)', string)
        return urls[0] if urls else None

    def _guess_extension_from_buffer(self, buffer: io.BytesIO) -> str:
        extension = mimetypes.guess_extension(type=magic.from_buffer(buffer.read(2048), mime=True))
        buffer.seek(0)
        return extension


intents = discord.Intents.default()
intents.message_content = True
client = DiscordClient(intents=intents)

api_key = os.environ.get('DISCORD_API_TOKEN')
if not api_key:
    raise RuntimeError('DISCORD_API_TOKEN environment variable not set, plesae set it to a valid value and try again.')

client.run(api_key)
