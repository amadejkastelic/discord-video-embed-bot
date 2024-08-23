import datetime
import glob
import io
import os
import shutil
import typing
import uuid

import asyncpraw
import redvid
import requests
from RedDownloader import RedDownloader as reddit_downloader
from asyncpraw import exceptions as praw_exceptions

import models
import utils
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
        self.downloader = reddit_downloader

    async def get_post(self) -> models.Post:
        post = models.Post(url=self.url)

        did_hydrate = await self._hydrate_post(post)
        if not did_hydrate:
            raise Exception('No reddit credentials')

        return post

    async def _hydrate_post(self, post: models.Post) -> bool:
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
        elif submission.url.startswith('https://www.reddit.com/gallery/'):
            post.buffer = self._download_and_merge_gallery(url=submission.url)

        return True

    def _hydrate_post_no_login(self, post: models.Post) -> bool:
        try:
            media = self.downloader.Download(url=post.url, quality=720, destination='/tmp/', output=str(uuid.uuid4()))
        except Exception:
            return False

        post.description = media.GetPostTitle().Get()
        post.author = media.GetPostAuthor().Get()
        post.spoiler = self._is_nsfw()

        files = glob.glob(os.path.join(media.destination, f'{media.output}*'))
        if not files:
            return True

        if os.path.isfile(files[0]):
            with open(files[0], 'rb') as f:
                post.buffer = io.BytesIO(f.read())
        else:
            photos = [os.path.join(files[0], photo) for photo in os.listdir(files[0])]
            post.buffer = utils.combine_images(photos)
            for photo in photos:
                os.remove(photo)

        for file in files:
            if os.path.isfile(file):
                os.remove(file)
            else:
                os.rmdir(file)

        return True

    def _download_and_merge_gallery(self, url: str) -> typing.Optional[io.BytesIO]:
        path = f'/tmp/{uuid.uuid4()}'
        os.mkdir(path)

        self.downloader.Download(url=url, destination=path, verbose=False)
        files = os.listdir(path)
        if len(files) == 0:
            return None
        if len(files) == 1:
            fp = f'{path}/{files[0]}'
            if not os.path.isdir(fp):
                with utils.temp_open(fp, 'rb') as f:
                    return io.BytesIO(f.read())

        downloaded_path = f'{path}/downloaded'
        files = sorted(os.listdir(downloaded_path))

        image_buffer = utils.combine_images([f'{downloaded_path}/{f}' for f in files])

        shutil.rmtree(path)
        return image_buffer

    def _is_nsfw(self) -> bool:
        content = str(requests.get(self.url).content)
        return 'nsfw&quot;:true' in content or 'isNsfw&quot;:true' in content
