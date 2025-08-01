import datetime
import io
import typing

import requests
from django.conf import settings
from twitchdl import entities as twitch_entities
from twitchdl import twitch
from twitchdl import utils as twitch_utils
from twitchdl.commands import download as twitch_download

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.integrations import base
from bot.integrations.twitch import config


class TwitchClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'twitch.tv'}
    _CONFIG_CLASS = config.TwitchConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.TwitchConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('twitch', {}))

        if not conf.enabled:
            logger.info('Twitch integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = TwitchClient(conf.post_format)

    @classmethod
    def should_handle(cls, url: str) -> bool:
        return super().should_handle(url) and '/clip/' in url


class TwitchClient(base.BaseClient):
    INTEGRATION = constants.Integration.TWITCH

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, twitch_utils.parse_clip_identifier(url), None

    async def get_post(self, url: str) -> domain.Post:
        uid = twitch_utils.parse_clip_identifier(url)
        if not uid:
            raise exceptions.IntegrationClientError('Only Twitch clips are supported')

        clip = twitch.get_clip(uid)

        clip_url = twitch_download.get_clip_authenticated_url(
            slug=clip['slug'], quality=str(self._find_quality(qualities=clip['videoQualities']))
        )
        with requests.get(url=clip_url, timeout=base.DEFAULT_TIMEOUT) as resp:
            return domain.Post(
                url=url,
                author=clip['broadcaster']['displayName'],
                description=f'{clip["title"]} - {clip["game"]["name"]}',
                views=clip['viewCount'],
                created=datetime.datetime.fromisoformat(clip['createdAt']),
                buffer=io.BytesIO(resp.content),
            )

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        raise exceptions.NotSupportedError('get_comments')

    @staticmethod
    def _find_quality(qualities: typing.List[twitch_entities.VideoQuality], max_quality: int = 720) -> int:
        """
        Filters out qualities higher than max_quality and returns the highest one left.
        """
        return int(
            sorted(
                list(filter(lambda quality: int(quality['quality']) <= max_quality, qualities)),
                key=lambda quality: quality['quality'],
                reverse=True,
            )[0]['quality']
        )
