import datetime
import io
import logging
import os
import typing

import asyncpraw
import redvid
import requests
from asyncpraw import exceptions as praw_exceptions
from django.conf import settings

from bot import constants
from bot import domain
from bot.downloader import base
from bot.downloader.reddit import config


class RedditClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['reddit.com', 'redd.it']
    _CONFIG_SCHEMA = config.RedditConfigSchema

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.RedditConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('reddit', {}))

        if not conf.enabled and not all([conf.client_id, conf.client_secret, conf.user_agent]):
            logging.info('Reddit integration not enabled or missing credentials')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = RedditClient(
            client_id=conf.client_id,
            client_secret=conf.client_secret,
            user_agent=conf.user_agent,
        )


class RedditClient(base.BaseClient):
    INTEGRATION = constants.Integration.REDDIT

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        super(RedditClient, self).__init__()
        self.client = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        return self.INTEGRATION, url.split('?')[0].split('/')[-2], None

    async def get_post(self, url: str) -> domain.Post:
        post = domain.Post(url=url)

        did_hydrate = await self._hydrate_post(post)
        if not did_hydrate:
            raise Exception('Failed hydrating reddit post')

        return post

    async def _hydrate_post(self, post: domain.Post) -> bool:
        if not self.client:
            return False

        try:
            submission = await self.client.submission(url=post.url)
        except praw_exceptions.InvalidURL:
            # Hack for new reddit urls generated in mobile app
            # Does another request, which redirects to the correct url
            post.url = requests.get(post.url).url.split('?')[0]
            submission = await self.client.submission(url=post.url)

        content = ''
        if submission.selftext:
            content = f'\n\n{submission.selftext}'

        post.author = submission.author
        post.description = f'{submission.title}{content}'
        post.likes = submission.score
        post.spoiler = submission.over_18 or submission.spoiler
        post.created = datetime.datetime.fromtimestamp(submission.created_utc).astimezone()

        if submission.url.startswith('https://i.redd.it/'):
            post.buffer = await self._download(url=submission.url)
        elif submission.url.startswith('https://v.redd.it/'):
            redvid.Downloader(
                url=submission.url, path='/tmp', filename=f'{submission.id}.mp4', max_q=True, log=False
            ).download()
            with open(f'/tmp/{submission.id}.mp4', 'rb') as f:
                post.buffer = io.BytesIO(f.read())
            os.remove(f'/tmp/{submission.id}.mp4')

        return True

    @staticmethod
    def _is_nsfw(url: str) -> bool:
        content = str(requests.get(url).content)
        return 'nsfw&quot;:true' in content or 'isNsfw&quot;:true' in content
