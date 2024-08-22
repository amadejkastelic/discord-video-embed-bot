import json
import re
import typing

import requests
import threads
from django.conf import settings

from bot import constants
from bot import domain
from bot import logger
from bot.downloader import base
from bot.downloader.threads import config


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

    def __init__(self) -> None:
        super().__init__()
        self.client = threads.Threads()

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, url.strip('/').split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        _, url_id, _ = await self.get_integration_data(url)

        thread = self._get_thread(url_id)
        logger.debug('Obtained thread', thread=thread)

    def _get_thread_id(self, url_id: str):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'

        thread_id = 0

        for letter in url_id:
            thread_id = (thread_id * 64) + alphabet.index(letter)

        return thread_id

    def _get_thread(self, url_id: str) -> dict:
        thread_id = self._get_thread_id(url_id)
        api_token = self._get_threads_api_token()

        headers = {
            'Authority': 'www.threads.net',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.threads.net',
            'Pragma': 'no-cache',
            'Sec-Fetch-Site': 'same-origin',
            'X-ASBD-ID': '129477',
            'X-FB-LSD': api_token,
            'X-IG-App-ID': '238260118697367',
            'X-FB-Friendly-Name': 'BarcelonaPostPageQuery',
        }

        response = requests.post(
            url=self.THREADS_API_URL,
            headers=headers,
            data={
                'lsd': api_token,
                'variables': json.dumps(
                    {
                        'postID': thread_id,
                    },
                ),
                'doc_id': '5587632691339264',
            },
        )

        return response.json()

    def _get_threads_api_token(self) -> str:
        response = requests.get(
            url='https://www.instagram.com/instagram',
            headers=self.fetch_html_headers,
        )

        token_key_value = re.search('LSD",\\[\\],{"token":"(.*?)"},\\d+\\]', response.text).group()
        token_key_value = token_key_value.replace('LSD",[],{"token":"', '')
        token = token_key_value.split('"')[0]

        return token
