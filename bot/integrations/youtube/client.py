import io
import typing

import aiohttp
import pytubefix as pytube
from django.conf import settings
from pytubefix import exceptions as pytube_exceptions

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.integrations import base
from bot.integrations.youtube import config
from bot.integrations.youtube import types

LIKES_API_URL_TEMPLATE = 'https://returnyoutubedislikeapi.com/votes?videoId={video_id}'


class YoutubeClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'youtube.com/shorts'}
    _CONFIG_CLASS = config.YoutubeConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.YoutubeConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('youtube', {}))

        if not conf.enabled:
            logger.info('Youtube integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = YoutubeClient(post_format=conf.post_format, fetch_likes=conf.external_likes_api)


class YoutubeClient(base.BaseClient):
    INTEGRATION = constants.Integration.YOUTUBE

    def __init__(self, fetch_likes: bool, post_format: typing.Optional[str] = None) -> None:
        super().__init__(post_format)
        self.fetch_likes = fetch_likes

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
            spoiler=vid.age_restricted is True,
        )

        if self.fetch_likes:
            likes = await self._get_likes(video_id=vid.video_id)
            post.likes = likes.likes
            post.dislikes = likes.dislikes

        try:
            streams = vid.streams
        except pytube_exceptions.VideoUnavailable as e:
            logger.warning(
                'Failed to fetch video with ANDROID_VR client, falling back to MWEB',
                error=str(e),
                url=url,
            )
            streams = pytube.YouTube(url, 'MWEB').streams

        streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().stream_to_buffer(
            post.buffer
        )

        return post

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        raise exceptions.NotSupportedError('get_comments')

    async def _get_likes(self, video_id: str) -> types.Likes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=LIKES_API_URL_TEMPLATE.format(video_id=video_id)) as resp:
                return types.Likes.model_validate(await resp.json())
