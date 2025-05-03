import hashlib
import typing

from api_24ur import client
from django.conf import settings

from bot import constants
from bot import domain
from bot import logger
from bot.common import utils
from bot.integrations import base
from bot.integrations.twenty4ur import config


class Twenty4UrClientSingleton(base.BaseClientSingleton):
    DOMAINS = {
        '24ur.com',
        'zadovoljna.si',
        'bibaleze.si',
        'vizita.si',
        'cekin.si',
        'moskisvet.com',
        'dominvrt.si',
        'okusno.je',
    }
    _CONFIG_CLASS = config.Twenty4UrConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.Twenty4UrConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('24ur', {}))

        if not conf.enabled:
            logger.info('24ur integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = Twenty4UrClient(conf.post_format)


class Twenty4UrClient(base.BaseClient):
    INTEGRATION = constants.Integration.TWENTY4_UR

    def __init__(self, post_format: typing.Optional[str] = None) -> None:
        super().__init__(post_format)
        self.client = client.Client()

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, hashlib.md5(self.client._path_from_url(url).encode()).hexdigest(), None

    async def get_post(self, url: str) -> domain.Post:
        article = await self.client.get_article_by_url(url=url)

        buffer = None
        if len(article.videos) > 0:
            buffer = await self.client.download_video_bytes(stream_url=article.videos[0].url, max_bitrate=2000000)
        elif len(article.images) > 0:
            buffer = await self._download(url=article.images[0].url)

        return domain.Post(
            url=url,
            author=article.author,
            description=utils.html_to_markdown(article.summary),
            created=article.posted_at,
            views=article.num_views,
            buffer=buffer,
        )

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        return [
            domain.Comment(
                author=comment.author,
                created=comment.posted_at,
                likes=comment.score,
                comment=utils.html_to_markdown(comment.content),
            )
            for comment in (await self.client.get_article_by_url(url=url, num_comments=n)).comments
        ]
