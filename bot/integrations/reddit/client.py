import asyncio
import datetime
import glob
import io
import os
import re
import shutil
import typing
import uuid

import asyncpraw
import asyncpraw.models
import redvid
import requests
from RedDownloader import RedDownloader as reddit_downloader
from asyncpraw import exceptions as praw_exceptions
from django.conf import settings

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.common import utils
from bot.integrations import base
from bot.integrations.reddit import config

NEW_REDDIT_URL_PATTERN = '^https://www.reddit.com/r/[^/]+/s/[^/]+$'


class RedditClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'reddit.com', 'redd.it'}
    BLACKLIST_DOMAINS = {
        'i.redd.it',
        'v.redd.it',
        'preview.redd.it',
        'gallery.redd.it',
        'i.redd.it',
        'preview.redd.it',
        'v.redd.it',
    }
    _CONFIG_CLASS = config.RedditConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.RedditConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('reddit', {}))

        if not conf.enabled:
            logger.info('Reddit integration not enabled')
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
        super().__init__()
        self.client = None
        if all([client_id, client_secret, user_agent]):
            self.client = asyncpraw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
        else:
            logger.warning('Basic reddit integration (no credentials)')

        self.downloader = reddit_downloader

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        id_url_index = -2
        if re.match(NEW_REDDIT_URL_PATTERN, url) or url.startswith(
            'https://redd.it/'
        ):  # New and short url contains id as last element
            id_url_index = -1

        return self.INTEGRATION, url.strip('/').split('?')[0].split('/')[id_url_index], None

    async def get_post(self, url: str) -> domain.Post:
        post = domain.Post(url=url)

        did_hydrate = await self._hydrate_post(post)
        if not did_hydrate:
            raise exceptions.IntegrationClientError('Failed hydrating reddit post')

        return post

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        if not self.client:
            raise exceptions.ConfigurationError('Reddit credentials not configured')

        try:
            submission = await self.client.submission(url=url)
        except praw_exceptions.InvalidURL:
            # Hack for new reddit urls generated in mobile app
            # Does another request, which redirects to the correct url
            url = requests.get(url, timeout=base.DEFAULT_TIMEOUT).url.split('?')[0]
            submission = await self.client.submission(url=url)

        return [
            domain.Comment(
                author=comment.author,
                created=datetime.datetime.fromtimestamp(comment.created_utc).astimezone(),
                likes=comment.score,
                comment=comment.body,
            )
            for comment in submission.comments[:n]
        ]

    async def _hydrate_post(self, post: domain.Post) -> bool:
        if not self.client:
            return self._hydrate_post_no_login(post)

        submission: asyncpraw.models.Submission = await self.client.submission(url=post.url)

        content = ''
        if submission.selftext:
            content = f'\n\n{submission.selftext}'

        post.author = submission.author
        post.description = f'{submission.title}{content}'
        post.likes, post.dislikes = self._calculate_votes(upvotes=submission.score, ratio=submission.upvote_ratio)
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
            image_urls = []
            for media_id in [item['media_id'] for item in submission.gallery_data['items']]:
                image_urls.append(
                    submission.media_metadata[media_id]['p'][0]['u'].split('?')[0].replace('preview', 'i')
                )
            post.buffer = utils.combine_images(
                await asyncio.gather(*[self._download(url=image_url) for image_url in image_urls[:3]])
            )

        return True

    def _hydrate_post_no_login(self, post: domain.Post) -> bool:
        if self._is_mobile_url(url=post.url):
            post.url = requests.get(post.url, timeout=base.DEFAULT_TIMEOUT).url.split('?')[0]

        try:
            media = self.downloader.Download(url=post.url, quality=720, destination='/tmp/', output=str(uuid.uuid4()))
        except Exception as e:
            logger.error('Failed to fetch reddit post', error=str(e))
            return False

        post.description = media.GetPostTitle().Get()
        post.author = media.GetPostAuthor().Get()
        post.spoiler = self._is_nsfw(post.url)

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

    @staticmethod
    def _is_nsfw(url: str) -> bool:
        content = str(requests.get(url, timeout=base.DEFAULT_TIMEOUT).content)
        return 'nsfw&quot;:true' in content or 'isNsfw&quot;:true' in content

    @staticmethod
    def _calculate_votes(upvotes: int, ratio: float) -> typing.Tuple[int, int]:
        downvotes = (upvotes / ratio) - upvotes
        return (upvotes, int(downvotes))

    @staticmethod
    def _is_mobile_url(url: str) -> bool:
        return bool(re.match(NEW_REDDIT_URL_PATTERN, url))
