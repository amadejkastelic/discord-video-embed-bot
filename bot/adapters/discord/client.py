import asyncio
import datetime
import typing
from functools import partial
from itertools import batched

import discord
from discord import app_commands
from discord import ui
from discord.app_commands import checks

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot import service
from bot.common import utils
from bot.adapters import mixins


class CustomView(ui.View):
    @ui.button(label='❌')
    async def on_click_delete(
        self,
        interaction: discord.Interaction,
        _: ui.Button,
    ) -> None:
        if interaction.message is None:
            logger.warning('Invoked delete on a missing message')
            return

        if interaction.user.mentioned_in(interaction.message):
            await interaction.message.delete()
            logger.info('User performed a delete action', user=interaction.user.id, message=interaction.message.id)
        else:
            logger.warning(
                'User tried to perform an illegal delete action',
                user=interaction.user.id,
                message=interaction.message.id,
            )


class CustomViewWithReload(CustomView):
    def __init__(self, *args, **kwargs):
        self.client: DiscordClient = kwargs.pop('client')
        super().__init__(*args, **kwargs)

    @ui.button(label='🔄')
    async def on_click_reload(
        self,
        interaction: discord.Interaction,
        _: ui.Button,
    ) -> None:
        if interaction.message is None:
            logger.warning('Invoked reload on a missing message')
            return

        if interaction.user.mentioned_in(interaction.message):
            await self.client._handle_message(message=interaction.message, user=interaction.user)
            logger.info('User performed a reload action', user=interaction.user.id, message=interaction.message.id)
        else:
            logger.warning(
                'User tried to perform an illegal reload action',
                user=interaction.user.id,
                message=interaction.message.id,
            )


class DiscordClient(mixins.BotMixin, discord.Client):
    VENDOR = constants.ServerVendor.DISCORD

    def __init__(self, *, intents: discord.Intents, **options: typing.Any) -> None:
        super().__init__(intents=intents, **options)

        commands: typing.List[app_commands.Command] = [
            app_commands.Command(
                name='embed',
                description='Embeds media directly into discord',
                callback=self.embed_cmd,
            ),
            app_commands.Command(
                name='comments',
                description='Fetches comments for a post',
                callback=self.get_comments_cmd,
            ),
            app_commands.Command(
                name='help',
                description='Prints configuration for this server',
                callback=self.help_cmd,
            ),
            app_commands.Command(
                name='silence',
                description='(Un)Ban a user from using embed commands',
                callback=self.silence_user_cmd,
            ),
            app_commands.Command(
                name='postfmt',
                description='Fetches post format for specified site',
                callback=self.get_post_format_cmd,
            ),
            app_commands.Command(
                name='clear_cache',
                description='Clears post cache for server',
                callback=self.clear_cache_cmd,
            ),
            app_commands.Command(
                name='provision',
                description='Provisions a server',
                callback=self.provision_cmd,
            ),
        ]

        self.tree = app_commands.CommandTree(client=self)
        for command in commands:
            self.tree.add_command(command)

    async def on_ready(self):
        await self.tree.sync()
        logger.info('Logged on', bot_user=self.user)

    async def _handle_message(self, message: discord.Message, user: discord.User):  # noqa: C901
        url = utils.find_first_url(message.content)
        if not url:
            return

        if service.should_handle_url(url) is False:
            logger.debug(
                'Handling for URL not enabled',
                url=url,
                server_uid=str(message.guild.id),
                server_vendor=self.VENDOR.value,
            )
            return

        new_message = (
            await asyncio.gather(
                message.delete(),
                message.channel.send(content='🔥 Working on it 🥵', reference=message.reference),
            )
        )[1]

        try:
            post = await service.get_post(
                url=url,
                server_vendor=constants.ServerVendor.DISCORD,
                server_uid=str(message.guild.id),
                author_uid=str(message.author.id),
            )
            if not post:
                raise exceptions.IntegrationClientError('Failed to fetch post')
        except Exception as e:
            logger.exception('Failed downloading', url=url, error=str(e))
            await asyncio.gather(
                new_message.edit(
                    content=f'{user.mention}\nFailed downloading {url}\nError: {str(e)}.',
                    suppress=True,
                ),
                new_message.add_reaction('❌'),
                new_message.add_reaction('🔄'),
            )
            raise e

        try:
            msg = await self._send_post(
                post=post,
                send_func=message.channel.send,
                author=user,
                reference=message.reference,
            )
            logger.info('User sent message with url', user=user.display_name, url=url)
        except Exception as e:
            logger.exception('Failed sending message', url=url, error=str(e))
            msg = await message.channel.send(
                content=f'Failed sending discord message for {url} ({user.mention}).\nError: {str(e)}'
            )

        await asyncio.gather(msg.add_reaction('❌'), new_message.delete())

    async def on_message(self, message: discord.Message):
        if message.author == self.user or message.guild is None:
            return

        await self._handle_message(message=message, user=message.author)

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if not self.user:
            logger.warning('Discord bot not logged in')
            return

        if user.id == self.user.id:
            return

        if self.user.id not in [user.id async for user in reaction.users(limit=50)]:
            return

        if (
            reaction.message.author.id == self.user.id
            and user.mentioned_in(message=reaction.message)
            and reaction.message.created_at.replace(tzinfo=None)
            >= (datetime.datetime.utcnow() - datetime.timedelta(minutes=5))
        ):
            if reaction.emoji == '❌':
                logger.info(
                    'User deleted message',
                    user=reaction.message.author.id,
                    url=utils.find_first_url(reaction.message.content),
                )
                await reaction.message.delete()
            elif reaction.emoji == '🔄':
                logger.info(
                    'User retried processing of message',
                    user=reaction.message.author.id,
                    url=utils.find_first_url(reaction.message.content),
                )
                await self._handle_message(message=reaction.message, user=user)

    async def embed_cmd(self, interaction: discord.Interaction, url: str, spoiler: bool = False) -> None:
        await interaction.response.defer()

        if service.should_handle_url(url) is False:
            return

        try:
            post = await service.get_post(
                url=url,
                server_vendor=constants.ServerVendor.DISCORD,
                server_uid=str(interaction.guild_id),
                author_uid=str(interaction.user.id),
            )
            if not post:
                raise exceptions.IntegrationClientError('Failed to fetch post')
            if not post.spoiler:
                post.spoiler = spoiler
        except Exception as e:
            logger.exception('Failed downloading', url=url, error=str(e))
            await interaction.followup.send(
                content=f'Failed fetching {url} ({interaction.user.mention}).\nError: {str(e)}',
                view=CustomViewWithReload(client=self),
            )
            raise e

        await self._send_post(
            post=post,
            send_func=partial(interaction.followup.send, view=CustomView()),
            author=interaction.user,
        )

    async def get_comments_cmd(
        self,
        interaction: discord.Interaction,
        url: str,
        n: int = 5,
        spoiler: bool = False,
    ) -> None:
        await interaction.response.defer()

        if service.should_handle_url(url) is False:
            return

        try:
            comments = await service.get_comments(
                url=url,
                n=n,
                server_vendor=constants.ServerVendor.DISCORD,
                server_uid=str(interaction.guild_id),
                author_uid=str(interaction.user.id),
            )
        except Exception as e:
            logger.exception('Failed downloading', url=url, error=str(e))
            await interaction.followup.send(
                content=f'Failed fetching {url} ({interaction.user.mention}).\nError: {str(e)}',
                view=CustomView(),
            )
            raise e

        # Override spoiler
        for comment in comments:
            if not comment.spoiler:
                comment.spoiler = spoiler

        for batch in batched(comments, 5):
            await self._send_comments(
                url=url,
                comments=batch,
                send_func=partial(interaction.followup.send, view=CustomView()),
                author=interaction.user,
            )

    async def help_cmd(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        response = service.get_server_info(
            server_vendor=constants.ServerVendor.DISCORD,
            server_uid=str(interaction.guild_id),
        )
        if not response:
            await interaction.followup.send(
                content='Failed retreiving server configuration.',
                view=CustomView(),
            )
            return

        await interaction.followup.send(content=f'{interaction.user.mention}\n{response}', view=CustomView())

    @checks.has_permissions(administrator=True)
    async def silence_user_cmd(
        self, interaction: discord.Interaction, member: discord.Member, unban: bool = False
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if not isinstance(interaction.user, discord.Member):
            await interaction.followup.send(
                content='Something went wrong',
                ephemeral=True,
            )
            return

        if interaction.user.guild.id == member.id:
            response = 'Can\'t ban yourself..'
        else:
            try:
                service.change_server_member_banned_status(
                    server_vendor=constants.ServerVendor.DISCORD,
                    server_uid=str(interaction.guild_id),
                    member_uid=str(member.id),
                    banned=not unban,
                )
                response = 'User {display_name} {banned}banned.'
            except Exception as e:
                logger.error('Failed banning user', error=str(e))
                response = 'Failed to {banned}ban user {display_name}.'

            response = response.format(
                display_name=member.display_name,
                banned='un' if unban else '',
            )

        await interaction.followup.send(
            content=response,
            ephemeral=True,
        )

    @checks.has_permissions(administrator=True)
    async def get_post_format_cmd(self, interaction: discord.Interaction, integration: constants.Integration) -> None:
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            content=service.get_post_format(
                server_vendor=constants.ServerVendor.DISCORD,
                server_uid=str(interaction.guild_id),
                integration=integration,
            ),
            ephemeral=True,
        )

    @checks.has_permissions(administrator=True)
    async def clear_cache_cmd(
        self,
        interaction: discord.Interaction,
        integration: typing.Optional[constants.Integration],
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        res = self.clear_cache(server_vendor_uid=str(interaction.guild_id), integration=integration)
        logger.info(
            'Admin cleared post cache',
            deleted_cnt=res,
            integration=integration.value if integration else 'all',
            admin=interaction.user.id,
        )

        await interaction.followup.send(
            content=f'Deleted {res} posts from cache.',
            ephemeral=True,
        )

    @checks.has_permissions(administrator=True)
    async def provision_cmd(
        self,
        interaction: discord.Interaction,
        tier: constants.ServerTier,
        integration: typing.Optional[constants.Integration] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        service.provision_server(
            server_vendor=constants.ServerVendor.DISCORD,
            server_vendor_uid=str(interaction.guild_id),
            tier=tier,
            integrations=[integration] if integration else [],
        )

        logger.info(
            'Admin provisioned server',
            tier=tier.value,
            integration=integration.value if integration else 'all',
            admin=interaction.user.id,
            server_id=interaction.guild_id,
        )

        await interaction.followup.send(
            content='Provisioned server',
            ephemeral=True,
        )

    async def _send_post(
        self,
        post: domain.Post,
        send_func: typing.Callable,
        author: typing.Union[discord.User, discord.Member],
        reference: typing.Optional[discord.MessageReference] = None,
    ) -> discord.Message:
        send_kwargs = {
            'suppress_embeds': True,
        }
        if reference is not None:
            send_kwargs['reference'] = reference
        file = None
        if post.buffer:
            extension = utils.guess_extension_from_buffer(buffer=post.buffer)
            file = discord.File(
                fp=post.buffer,
                filename=f'{'SPOILER_' if post.spoiler else ''}file{extension}',
            )
            send_kwargs['file'] = file

        def trim_content(post: domain.Post, content: str) -> str:
            if len(content) < 2000: return content
            if post.spoiler: return content[:1995] + '||...'
            return content[:1997] + '...'

        resize_tries, MAX_RESIZE_TRIES = 0, 3
        try:
            content = f'Here you go {author.mention} {utils.random_emoji()}.\n{str(post)}'
            content = trim_content(post, content)

            send_kwargs['content'] = content

            return await send_func(**send_kwargs)
        except discord.HTTPException as e:
            if e.status != 413:  # Payload too large
                raise e
            if post.buffer is not None and resize_tries < MAX_RESIZE_TRIES:
                logger.info('File too large, resizing...', size=post.buffer.getbuffer().nbytes)
                resize_tries += 1
                post.buffer.seek(0)
                post.buffer = await utils.resize(buffer=post.buffer, extension=extension)
                return await self._send_post(post=post, send_func=send_func, author=author)
            if (resize_tries >= MAX_RESIZE_TRIES):
                try:
                    content = (f'I\'m sorry {author.mention}, your post was too big '
                        f'and I couldn\'t make it small enough. \U0001F622\n{str(post)}'
                    )
                    content = trim_content(content, post)
                    post.buffer = None

                    send_kwargs['content'] = content

                    return await send_func(**send_kwargs)
                except discord.HTTPException:
                    raise exceptions.BotError('Couldn\'t even send error message???')

            raise exceptions.BotError('Failed to send message') from e
        except utils.SSL_ERRORS as e:
            # Retry on SSL errors
            logger.error("SSL Error, retrying", error=str(e))
            return await self._send_post(post=post, send_func=send_func, author=author)

    async def _send_comments(
        self,
        url: str,
        comments: typing.List[domain.Comment],
        send_func: typing.Callable,
        author: typing.Union[discord.User, discord.Member],
    ) -> discord.Message:
        send_kwargs = {
            'suppress_embeds': True,
        }

        content = f'Here you go {author.mention} {utils.random_emoji()}.\n{url}\n{domain.comments_to_string(comments)}'
        if len(content) > 2000:
            if any(comment.spoiler is True for comment in comments):
                content = content[:1995] + '||...'
            else:
                content = content[:1997] + '...'

        send_kwargs['content'] = content

        try:
            return await send_func(**send_kwargs)
        except discord.HTTPException as e:
            raise exceptions.BotError('Failed to send message') from e
