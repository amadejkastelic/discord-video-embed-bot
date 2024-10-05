import datetime
import typing
from urllib.parse import urlparse

import aiohttp
from django.conf import settings

from bot import constants
from bot import domain
from bot import logger
from bot.integrations import base
from bot.integrations.four_chan import config
from bot.integrations.four_chan import types

API_URL_TEMPLATE = 'https://a.4cdn.org/{board}/thread/{thread_id}.json'
IMAGE_URL_TEMPLATE = 'https://i.4cdn.org/{board}/{image_id}{extension}'


class FourChanClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['4chan.org']
    _CONFIG_CLASS = config.FourChanConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.FourChanConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('4chan', {}))

        if not conf.enabled:
            logger.info('4chan integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = FourChanClient()


class FourChanClient(base.BaseClient):
    INTEGRATION = constants.Integration.FOUR_CHAN

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        path = urlparse(url).path.strip('/').split('/')
        return self.INTEGRATION, f'{path[0]}_{path[-1]}', None

    async def _get_posts(self, board: str, thread_id: str) -> types.Posts:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=API_URL_TEMPLATE.format(
                    board=board,
                    thread_id=thread_id,
                )
            ) as resp:
                return types.Posts.model_validate(await resp.json())

    async def get_post(self, url: str) -> domain.Post:
        _, data, _ = await self.get_integration_data(url.strip())
        board, thread_id = data.split('_')

        logger.debug('Parsed 4chan url', url=url, board=board, thread_id=thread_id)

        response = await self._get_posts(board=board, thread_id=thread_id)

        post = domain.Post(
            url=url,
            author=response.posts[0].name,
            description=response.posts[0].com,
            spoiler=True if response.posts[0].spoiler == 1 else False,
            created=datetime.datetime.fromtimestamp(response.posts[0].time) if response.posts[0].time else None,
        )

        if response.posts[0].tim:
            post.buffer = await self._download(
                IMAGE_URL_TEMPLATE.format(
                    board=board,
                    image_id=response.posts[0].tim,
                    extension=response.posts[0].ext,
                )
            )

        return post

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        _, data, _ = await self.get_integration_data(url.strip())
        board, thread_id = data.split('_')

        logger.debug('Parsed 4chan url', url=url, board=board, thread_id=thread_id)

        response = await self._get_posts(board=board, thread_id=thread_id)

        comments: typing.List[domain.Comment] = []
        for i in range(1, len(response.posts), 1):
            if i > n:
                break

            comments.append(
                domain.Comment(
                    author=response.posts[i].name,
                    comment=response.posts[i].com,
                    spoiler=True if response.posts[i].spoiler == 1 else False,
                    created=datetime.datetime.fromtimestamp(response.posts[i].time) if response.posts[i].time else None,
                )
            )

        return comments
