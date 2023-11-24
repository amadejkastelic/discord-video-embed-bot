import asyncio
import datetime
import logging
import os
import random

import discord

import models
import utils
from downloader import registry

emoji = ['😼', '😺', '😸', '😹', '😻', '🙀', '😿', '😾', '😩', '🙈', '🙉', '🙊', '😳']


class DiscordClient(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged on as {self.user}')

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        url = utils.find_first_url(message.content)
        if not url:
            return

        try:
            client = registry.get_instance(url=url)
        except Exception:
            return

        new_message = (await asyncio.gather(message.delete(), message.channel.send('🔥 Working on it 🥵')))[1]

        try:
            post = await client.get_post()
        except Exception as e:
            logging.error(f'Failed downloading {url}: {str(e)}')
            await asyncio.gather(
                new_message.edit(content=f'Failed downloading {url}. {message.author.mention}'),
                new_message.add_reaction('❌'),
            )
            raise e

        try:
            msg = await self._send_post(post=post, channel=message.channel, author=message.author)
            logging.info(f'User {message.author.display_name} sent message with url {url}')
        except Exception as e:
            logging.error(f'Failed sending message {url}: {str(e)}')
            msg = await message.channel.send(
                content=f'Failed sending discord message for {url} ({message.author.mention}).\nError: {str(e)}'
            )

        await asyncio.gather(msg.add_reaction('❌'), new_message.delete())

    async def _send_post(
        self, post: models.Post, channel: discord.GroupChannel, author: discord.User
    ) -> discord.Message:
        file = None
        if post.buffer:
            extension = utils.guess_extension_from_buffer(buffer=post.buffer)
            file = discord.File(
                fp=post.buffer,
                filename='{spoiler}file{extension}'.format(
                    spoiler='SPOILER_' if post.spoiler else '',
                    extension=extension,
                ),
            )

        try:
            content = f'Here you go {author.mention} {random.choice(emoji)}.\n{str(post)}'
            if len(content) > 2000:
                content = content[:1997] + '...'

            return await channel.send(
                content=content,
                file=file,
                suppress_embeds=True,
            )
        except discord.HTTPException as e:
            if e.status != 413:  # Payload too large
                raise e
            logging.info('File too large, resizing...')
            file.fp.seek(0)
            post.buffer = await utils.resize(buffer=file.fp, extension=extension)
            return await self._send_post(post=post, channel=channel, author=author)

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if (
            reaction.message.author.id == self.user.id
            and reaction.emoji == '❌'
            and user.mentioned_in(message=reaction.message)
            and reaction.message.created_at.replace(tzinfo=None)
            >= (datetime.datetime.utcnow() - datetime.timedelta(minutes=5))
        ):
            logging.info(f'User {user.display_name} deleted message {utils.find_first_url(reaction.message.content)}')
            await reaction.message.delete()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)

intents = discord.Intents.default()
intents.message_content = True
client = DiscordClient(intents=intents)

api_key = os.environ.get('DISCORD_API_TOKEN')
if not api_key:
    raise RuntimeError('DISCORD_API_TOKEN environment variable not set, plesae set it to a valid value and try again.')

client.run(api_key)
