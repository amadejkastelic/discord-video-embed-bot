import datetime
import io
import os
import typing

import asyncpraw
import redvid
import requests
from asyncpraw import exceptions as praw_exceptions

import domain
from downloader import base


class RedditClientSingleton(object):
    INSTANCE: typing.Optional[asyncpraw.Reddit] = None

    @classmethod
    def get_instance(cls) -> typing.Optional[asyncpraw.Reddit]:
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        if not all([client_id, client_secret, user_agent]):
            return None

        if not cls.INSTANCE:
            cls.INSTANCE = asyncpraw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )

        return cls.INSTANCE


class RedditClient(base.BaseClient):
    DOMAINS = ['reddit.com', 'redd.it']

    def __init__(self, url: str):
        super(RedditClient, self).__init__(url=url)
        self.client = RedditClientSingleton.get_instance()

    async def get_post(self) -> domain.Post:
        post = domain.Post(url=self.url)

        did_hydrate = await self._hydrate_post(post)
        if not did_hydrate:
            raise Exception('No reddit credentials')

        return post

    async def _hydrate_post(self, post: domain.Post) -> bool:
        if not self.client:
            return False

        try:
            submission = await self.client.submission(url=self.url)
        except praw_exceptions.InvalidURL:
            self.url = requests.get(self.url).url.split('?')[0]
            submission = await self.client.submission(url=self.url)

        content = ''
        if submission.selftext:
            content = f'\n\n{submission.selftext}'

        post.url = self.url
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

    def _is_nsfw(self) -> bool:
        content = str(requests.get(self.url).content)
        return 'nsfw&quot;:true' in content or 'isNsfw&quot;:true' in content
