import asyncio
import datetime
import logging
import typing
from functools import partial

import discord
from discord import app_commands
from discord import ui

import models
import utils
from downloader import registry


class CustomView(ui.View):
    @ui.button(label='❌')
    async def on_click(
        self,
        interaction: discord.Interaction,
        button: ui.Button,
    ) -> None:
        await interaction.message.delete()


class DiscordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: typing.Any) -> None:
        super().__init__(intents=intents, **options)

        self.tree = app_commands.CommandTree(client=self)
        self.tree.add_command(
            app_commands.Command(
                name='embed',
                description='Embeds media directly into discord',
                callback=self.command_embed,
            )
        )

    async def on_ready(self):
        await self.tree.sync()
        logging.info(f'Logged on as {self.user}')

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        url = utils.find_first_url(message.content)
        if not url:
            return

        try:
            client = registry.get_instance(url=url)
        except Exception as e:
            logging.error(f'Failed to obtain a strategy for url {url}. Error: {str(e)}')
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
            msg = await self._send_post(post=post, send_func=message.channel.send, author=message.author)
            logging.info(f'User {message.author.display_name} sent message with url {url}')
        except Exception as e:
            logging.error(f'Failed sending message {url}: {str(e)}')
            msg = await message.channel.send(
                content=f'Failed sending discord message for {url} ({message.author.mention}).\nError: {str(e)}'
            )

        await asyncio.gather(msg.add_reaction('❌'), new_message.delete())

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

    async def command_embed(self, interaction: discord.Interaction, url: str, spoiler: bool = False) -> None:
        await interaction.response.defer()

        try:
            client = registry.get_instance(url=url)
        except Exception as e:
            logging.error(f'Failed to obtain a strategy for url {url}. Error: {str(e)}')
            return

        try:
            post = await client.get_post()
            if not post.spoiler:
                post.spoiler = spoiler
        except Exception as e:
            logging.error(f'Failed downloading {url}: {str(e)}')
            await interaction.followup.send(f'Failed fetching {url} ({interaction.user.mention}).\nError: {str(e)}')
            raise e

        await self._send_post(
            post=post,
            send_func=partial(interaction.followup.send, view=CustomView()),
            author=interaction.user,
        )

    async def _send_post(
        self,
        post: models.Post,
        send_func: typing.Callable,
        author: discord.User,
    ) -> discord.Message:
        send_kwargs = {
            'suppress_embeds': True,
        }
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
            send_kwargs['file'] = file

        try:
            content = f'Here you go {author.mention} {utils.random_emoji()}.\n{str(post)}'
            if len(content) > 2000:
                if post.spoiler:
                    content = content[:1995] + '||...'
                else:
                    content = content[:1997] + '...'

            send_kwargs['content'] = content

            return await send_func(**send_kwargs)
        except discord.HTTPException as e:
            if e.status != 413:  # Payload too large
                raise e
            logging.info('File too large, resizing...')
            file.fp.seek(0)
            post.buffer = await utils.resize(buffer=file.fp, extension=extension)
            return await self._send_post(post=post, send_func=send_func, author=author)
