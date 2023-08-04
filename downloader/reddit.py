import datetime
import io
import logging
import glob
import os
import requests
import typing
import uuid

import asyncpraw
from RedDownloader import RedDownloader

from downloader import base
from models import post


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

    async def get_post(self) -> post.Post:
        media = None
        try:
            media = RedDownloader.Download(url=self.url, quality=720, destination='/tmp/', output=str(uuid.uuid4()))
        except Exception as e:
            logging.error(f'Failed download video: {str(e)}')

        p = post.Post(url=self.url)

        did_hydrate = await self._hydrate_post(p)
        if not did_hydrate and not media:
            raise RuntimeError('Failed fetching reddit post')
        elif not did_hydrate:
            p.description = media.GetPostTitle().Get()
            p.author = media.GetPostAuthor().Get()
            p.spoiler = self._is_nsfw()

        if not media:
            return p

        files = glob.glob(os.path.join(media.destination, f'{media.output}*'))
        if files:
            with open(files[0], 'rb') as f:
                p.buffer = io.BytesIO(f.read())

            for file in files:
                os.remove(file)

        return p

    async def _hydrate_post(self, p: post.Post) -> bool:
        if not self.client:
            return False

        submission = await self.client.submission(url=self.url)
        p.author = submission.author
        p.description = submission.title
        p.likes = submission.score
        p.spoiler = submission.over_18 or submission.spoiler
        p.created = datetime.datetime.fromtimestamp(submission.created_utc)
        return True

    def _is_nsfw(self) -> bool:
        content = str(requests.get(self.url).content)
        return 'nsfw&quot;:true' in content or 'isNsfw&quot;:true' in content
