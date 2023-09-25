import asyncio
import datetime
import logging
import os
import random

import discord

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
            await new_message.edit(content=f'Failed downloading {url}. {message.author.mention}')
            raise e

        file = None
        if post.buffer:
            file = discord.File(
                fp=post.buffer,
                filename='{spoiler}file{extension}'.format(
                    spoiler='SPOILER_' if post.spoiler else '',
                    extension=utils.guess_extension_from_buffer(buffer=post.buffer),
                ),
            )

        try:
            msg = await message.channel.send(
                content=f'Here you go {message.author.mention} {random.choice(emoji)}.\n{str(post)}',
                file=file,
                suppress_embeds=True,
            )
            await msg.add_reaction('❌')
            logging.info(f'User {message.author.display_name} sent message with url {url}')
        except Exception as e:
            logging.error(f'Failed sending message {url}: {str(e)}')
            await message.channel.send(
                content=f'Failed sending discord message for {url} ({message.author.mention}).\nError: {str(e)}'
            )
        await new_message.delete()

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if (
            reaction.emoji == '❌'
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
