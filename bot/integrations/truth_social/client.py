import datetime
import typing
from urllib.parse import urlparse

from django.conf import settings
from truthbrush import api as truthbrush_api

from bot import constants
from bot import domain
from bot import logger
from bot.common import utils
from bot.integrations import base
from bot.integrations.truth_social import config


class TruthSocialClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'truthsocial.com'}
    _CONFIG_CLASS = config.TruthSocialConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.TruthSocialConfig = cls._load_config(
            conf=settings.INTEGRATION_CONFIGURATION.get('truth_social', {})
        )

        if not conf.enabled:
            logger.info('Truth Social integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        if not conf.username or not conf.password:
            logger.info('Truth Social credentials missing')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = TruthSocialClient(
            username=conf.username,
            password=conf.password,
        )


class TruthSocialClient(base.BaseClient):
    INTEGRATION = constants.Integration.TRUTH_SOCIAL

    def __init__(self, username: str, password: str):
        super().__init__()

        self.client = truthbrush_api.Api(
            username=username,
            password=password,
        )

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, url.strip('/').split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        path = urlparse(url).path.split('/')
        username, post_id = path[1].lstrip('@'), path[3]

        *_, status = self.client.pull_statuses(username=username, since_id=str(int(post_id) - 1))

        post = domain.Post(
            url=url,
            author=status.get('account', {}).get('display_name'),
            description=utils.html_to_markdown(status.get('content', '')),
            likes=int(status.get('favourites_count', 0)),
            created=datetime.datetime.fromisoformat(status.get('created_at')),
            spoiler=status.get('sensitive', False),
        )

        media_attachments = status.get('media_attachments')
        if media_attachments and media_attachments[0].get('url'):
            post.buffer = await self._download(url=media_attachments[0].get('url'))

        return post
