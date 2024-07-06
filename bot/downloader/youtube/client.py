import io
import logging

import pytube
from django.conf import settings
from pytube.innertube import _default_clients

from bot import domain
from bot.downloader import base
from bot.downloader.youtube import config


# Age restriction bypass - https://stackoverflow.com/a/78267693/10428848
_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]


class YoutubeClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['youtube.com/shorts']
    _CONFIG_SCHEMA = config.YoutubeConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.YoutubeConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('youtube', {}))

        if not conf.enabled:
            logging.info('Youtube integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = YoutubeClient()


class YoutubeClient(base.BaseClient):
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
