import datetime
import io
import logging
import typing

import requests
from django.conf import settings
from twitchdl import twitch
from twitchdl import utils as twitch_utils
from twitchdl.commands import download as twitch_download

from bot import domain
from bot.downloader import base
from bot.downloader.twitch import config


class TwitchClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['twitch.tv']
    _CONFIG_SCHEMA = config.TwitchConfigSchema

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.TwitchConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('twitch', {}))

        if not conf.enabled:
            logging.info('Twitch integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = TwitchClient()


class TwitchClient(base.BaseClient):
    async def get_post(self, url: str) -> domain.Post:
        uid = twitch_utils.parse_clip_identifier(url)
        if not uid:
            raise Exception('Only Twitch clips are supported')

        clip = twitch.get_clip(uid)

        clip_url = twitch_download.get_clip_authenticated_url(
            slug=clip['slug'], quality=str(self._find_quality(qualities=clip['videoQualities']))
        )
        with requests.get(url=clip_url) as resp:
            return domain.Post(
                url=url,
                author=clip['broadcaster']['displayName'],
                description=f'{clip['title']} - {clip['game']['name']}',
                views=clip['viewCount'],
                created=datetime.datetime.fromisoformat(clip['createdAt']),
                buffer=io.BytesIO(resp.content),
            )

    @staticmethod
    def _find_quality(qualities: typing.List[twitch.VideoQuality], max_quality: int = 720) -> int:
        return int(
            sorted(
                list(filter(lambda quality: int(quality['quality']) <= max_quality, qualities)),
                key=lambda quality: quality['quality'],
                reverse=True,
            )[0]['quality']
        )
