import datetime
import json
import re
import typing

import requests
from django.conf import settings

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.downloader import base
from bot.downloader.threads import config
from bot.downloader.threads import types


HEADERS = {
    'Authority': 'www.threads.net',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.threads.net',
    'Pragma': 'no-cache',
    'Sec-Fetch-Site': 'same-origin',
    'X-ASBD-ID': '129477',
    'X-IG-App-ID': '238260118697367',
    'X-FB-Friendly-Name': 'BarcelonaPostPageQuery',
}


class ThreadsClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['threads.net']
    _CONFIG_SCHEMA = config.ThreadsConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.ThreadsConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('threads', {}))

        if not conf.enabled:
            logger.info('Threads integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = ThreadsClient()


class ThreadsClient(base.BaseClient):
    INTEGRATION = constants.Integration.THREADS

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, url.strip('/').split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        _, url_id, _ = await self.get_integration_data(url)

        thread = self._get_thread(url_id)

        if len(thread.data.data.edges) == 0 or len(thread.data.data.edges[0].node.thread_items) == 0:
            raise exceptions.IntegrationClientError('No threads found')

        thread = thread.data.data.edges[0].node.thread_items[0].post

        return domain.Post(
            url=url,
            author=thread.user.username,
            description=thread.caption.text,
            likes=thread.like_count,
            created=datetime.datetime.fromtimestamp(thread.taken_at),
        )

    def _get_thread_id(self, url_id: str):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'

        thread_id = 0

        for letter in url_id:
            thread_id = (thread_id * 64) + alphabet.index(letter)

        return thread_id

    def _get_thread(self, url_id: str) -> types.Thread:
        thread_id = self._get_thread_id(url_id)
        api_token = self._get_threads_api_token()

        response = requests.post(
            url='https://www.threads.net/api/graphql',
            timeout=base.DEFAULT_TIMEOUT,
            headers=HEADERS | {'X-FB-LSD': api_token},
            data={
                'lsd': api_token,
                'variables': json.dumps(
                    {
                        'postID': thread_id,
                    },
                ),
                'doc_id': '25460088156920903',
            },
        )

        with open('temp.json', 'w') as f:
            f.write(json.dumps(response.json()))

        return types.Thread.model_validate(response.json())

    def _get_threads_api_token(self) -> str:
        response = requests.get(
            url='https://www.instagram.com/instagram',
            timeout=base.DEFAULT_TIMEOUT,
            headers=HEADERS,
        )

        token_key_value = re.search('LSD",\\[\\],{"token":"(.*?)"},\\d+\\]', response.text).group()
        token_key_value = token_key_value.replace('LSD",[],{"token":"', '')
        token = token_key_value.split('"')[0]

        return token
