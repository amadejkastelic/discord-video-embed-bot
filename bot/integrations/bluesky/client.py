import datetime
import typing
from urllib.parse import urlparse

import atproto
from atproto import models as atproto_models
from django.conf import settings

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.common import utils
from bot.common import stream
from bot.integrations import base
from bot.integrations.bluesky import config


class BlueskyClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'bsky.app'}
    _CONFIG_CLASS = config.BlueskyConfig

    @classmethod
    def should_handle(cls, url: str) -> bool:
        return super().should_handle(url) and '/post/' in url

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.BlueskyConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('bluesky', {}))

        if not conf.enabled:
            logger.info('Bluesky integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        if not conf.username or not conf.password:
            logger.warning('Missing bluesky username or password')
            cls._INSTANCE = base.MISSING
            return

        if conf.base_url:
            cls.DOMAINS = {conf.base_url}

        cls._INSTANCE = BlueskyClient(
            post_format=conf.post_format,
            username=conf.username,
            password=conf.password,
            base_url=conf.base_url,
        )


class BlueskyClient(base.BaseClient):
    INTEGRATION = constants.Integration.BLUESKY

    def __init__(
        self,
        username: str,
        password: str,
        base_url: typing.Optional[str] = None,
        post_format: typing.Optional[str] = None,
    ):
        super().__init__(post_format)
        self.client = atproto.AsyncClient(base_url=base_url)
        self.logged_in = False
        self.username = username
        self.password = password

    async def _login(self):
        if self.logged_in:
            return

        profile = await self.client.login(self.username, self.password)
        self.logged_in = True
        logger.info('Logged in', integration=self.INTEGRATION.value, display_name=profile.display_name)

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, url.strip('/').split('?')[0].split('/')[-1], None

    @classmethod
    def _url_to_uri(cls, url: str) -> atproto.AtUri:
        parsed_url = urlparse(url)

        parts = parsed_url.path.strip('/').split('/')
        if len(parts) != 4 or parts[0] != 'profile' or parts[2] != 'post':
            logger.error('Failed to parse bluesky url', url=url)
            return ValueError('Invalid Bluesky post URL format')

        did, rkey = parts[1], parts[3]
        return atproto.AtUri.from_str(f'at://{did}/app.bsky.feed.post/{rkey}')

    async def get_post(self, url: str) -> domain.Post:
        uri = self._url_to_uri(url)

        await self._login()

        thread = (await self.client.get_post_thread(uri.http)).thread
        if getattr(thread, 'not_found', False) or getattr(thread, 'blocked', False) or not thread.post:
            logger.error(
                'Post not found or blocked',
                url=url,
                uri=uri.http,
                not_found=getattr(thread, 'not_found', False),
                blocked=getattr(thread, 'blocked', False),
            )
            raise exceptions.IntegrationClientError('Failed to get post')

        post = domain.Post(
            url=url,
            author=thread.post.author.display_name,
            description=thread.post.record.text,
            created=datetime.datetime.fromisoformat(thread.post.record.created_at),
            likes=thread.post.like_count,
        )

        if thread.post.embed:
            logger.debug('Got bluesky media post', py_type=thread.post.embed.py_type)
            if atproto_models.ids.AppBskyEmbedImages in thread.post.embed.py_type:
                post.buffer = utils.combine_images(
                    [await self._download(img.fullsize or img.thumb) for img in thread.post.embed.images[:3]]
                )
            elif atproto_models.ids.AppBskyEmbedVideo in thread.post.embed.py_type:
                stream_url = thread.post.embed.playlist or thread.post.embed.alt
                post.buffer = await stream.download(stream_url=stream_url)

        return post
