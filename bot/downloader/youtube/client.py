import io
import logging
import typing

import pytube
from django.conf import settings

from bot import constants
from bot import domain
from bot.downloader import base
from bot.downloader.youtube import config


class YoutubeClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['youtube.com/shorts']
    _CONFIG_SCHEMA = config.YoutubeConfigSchema

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.YoutubeConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('youtube', {}))

        if not conf.enabled:
            logging.info('Youtube integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = YoutubeClient()


class YoutubeClient(base.BaseClient):
    INTEGRATION = constants.Integration.YOUTUBE

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, url.strip('/').split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        vid = pytube.YouTube(url)

        post = domain.Post(
            url=url,
            author=vid.author,
            description=vid.title,
            views=vid.views,
            created=vid.publish_date,
            buffer=io.BytesIO(),
        )

        vid.streams.filter(progressive=True, file_extension='mp4').order_by(
            'resolution'
        ).desc().first().stream_to_buffer(post.buffer)

        return post
