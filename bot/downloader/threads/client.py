import datetime
import io
import json
import re
import typing

import requests
from django.conf import settings

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.common import utils
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
        api_token = self._get_threads_api_token()

        thread = self._get_thread(url_id=url_id, api_token=api_token)

        if len(thread.data.data.edges) == 0 or len(thread.data.data.edges[0].node.thread_items) == 0:
            raise exceptions.IntegrationClientError('No threads found')

        thread = thread.data.data.edges[0].node.thread_items[0].post

        post = domain.Post(
            url=url,
            author=thread.user.username,
            description=thread.caption.text,
            likes=thread.like_count,
            created=datetime.datetime.fromtimestamp(thread.taken_at),
        )

        headers = HEADERS | {'X-FB-LSD': api_token}

        media_url = None
        match thread.media_type:
            case types.MediaType.IMAGE:
                media_url = self._find_suitable_image_url(thread.image_versions2.candidates)
            case types.MediaType.VIDEO:
                media_url = thread.video_versions[0].url
            case types.MediaType.CAROUSEL:
                post.buffer = utils.combine_images(
                    [
                        await self._download(img.image_versions2.candidates[0].url, headers=headers)
                        for img in thread.carousel_media
                    ]
                )

        logger.debug('Fetched thread', media_type=thread.media_type, url=url, media_url=media_url)

        if media_url:
            with requests.get(url=media_url, timeout=base.DEFAULT_TIMEOUT) as resp:
                post.buffer = io.BytesIO(resp.content)

        return post

    def _get_thread_id(self, url_id: str) -> str:
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'

        thread_id = 0

        for letter in url_id:
            thread_id = (thread_id * 64) + alphabet.index(letter)

        return thread_id

    def _get_thread_raw(self, url_id: str, api_token: str) -> dict:
        return requests.post(
            url='https://www.threads.net/api/graphql',
            timeout=base.DEFAULT_TIMEOUT,
            headers=HEADERS | {'X-FB-LSD': api_token},
            data={
                'lsd': api_token,
                'variables': json.dumps(
                    {
                        'postID': self._get_thread_id(url_id),
                    },
                ),
                'doc_id': '25460088156920903',
            },
        ).json()

    def _get_thread(self, url_id: str, api_token: str) -> types.Thread:
        return types.Thread.model_validate(self._get_thread_raw(url_id=url_id, api_token=api_token))

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

    @staticmethod
    def _find_suitable_image_url(candidates: typing.List[types.Candidate], max_quality: int = 1440) -> str:
        """
        Returns image url with highest quality that is below max quality
        """
        return sorted(
            list(filter(lambda candidate: candidate.width <= max_quality, candidates)),
            key=lambda candidate: candidate.width,
            reverse=True,
        )[0].url
