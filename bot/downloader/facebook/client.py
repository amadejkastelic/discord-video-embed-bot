import logging
import os
import typing
from urllib import parse as urllib_parse

import facebook_scraper
from django.conf import settings

from bot import constants
from bot import domain
from bot.downloader import base
from bot.downloader.facebook import config


class FacebookClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['facebook.com', 'fb.watch']
    _CONFIG_SCHEMA = config.FacebookConfigSchema

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.FacebookConfig = cls._load_config(settings.INTEGRATION_CONFIGURATION.get('facebook', {}))

        if not conf.enabled:
            logging.info('Facebook integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        if conf.cookies_file_path is None:
            logging.warning('Not enabling facebook integration due to missing cookies')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = FacebookClient(cookies_path=conf.cookies_file_path)


class FacebookClient(base.BaseClient):
    INTEGRATION = constants.Integration.FACEBOOK

    def __init__(self, cookies_path: str):
        super().__init__()
        self.cookies_path = cookies_path

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        if url.split('?')[0].endswith('/watch') and 'v=' in url:
            return self.INTEGRATION, urllib_parse.parse_qs(urllib_parse.urlparse(url).query)['v'][0], None

        return self.INTEGRATION, url.split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        kwargs = {}
        if self.cookies_path and os.path.exists(self.cookies_path):
            kwargs['cookies'] = 'cookies.txt'

        fb_post = next(facebook_scraper.get_posts(post_urls=[url], **kwargs))

        ts = fb_post.get('time')
        post = domain.Post(
            url=url,
            author=fb_post.get('username'),
            description=fb_post.get('text'),
            likes=fb_post.get('likes'),
            created=ts.astimezone() if ts else None,
        )

        if fb_post.get('video'):
            post.buffer = await self._download(url=fb_post['video'])
        elif fb_post.get('images'):
            post.buffer = await self._download(url=fb_post['images'][0])

        return post
