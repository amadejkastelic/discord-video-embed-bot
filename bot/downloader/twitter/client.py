import datetime
import json
import logging
import typing

import twscrape
from django.conf import settings

from bot import constants
from bot import domain
from bot import exceptions
from bot.downloader import base
from bot.downloader.twitter import config

SCRAPE_URL = 'https://cdn.syndication.twimg.com/tweet-result'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://platform.twitter.com',
    'Connection': 'keep-alive',
    'Referer': 'https://platform.twitter.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'TE': 'trailers',
}


class TwitterClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['twitter.com', 'x.com']
    _CONFIG_SCHEMA = config.TwitterConfigSchema

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.TwitterConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('twitter', {}))

        if not conf.enabled:
            logging.info('Twitter / X integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = TwitterClient(
            username=conf.username,
            email=conf.email,
            password=conf.password,
        )


class TwitterClient(base.BaseClient):
    INTEGRATION = constants.Integration.TWITTER

    def __init__(
        self,
        username: typing.Optional[str],
        email: typing.Optional[str],
        password: typing.Optional[str],
    ):
        super().__init__()

        self.client: typing.Optional[twscrape.API] = None
        if all([username, email, password]):
            self.client = twscrape.API()

        self.logged_in = False
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def _parse_url(url: str) -> typing.Tuple[str, int]:
        metadata = url.strip('/').split('/status/')[-1].split('?')[0].split('/')
        return metadata[0], int(metadata[2]) - 1 if len(metadata) == 3 and metadata[1] == 'photo' else 0

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        uid, index = self._parse_url(url)
        return self.INTEGRATION, uid, index

    async def relogin(self) -> None:
        if self.client:
            await self.client.pool.relogin(usernames=[self.username])

    async def get_post(self, url: str) -> domain.Post:
        uid, index = self._parse_url(url)

        if self.client is None:
            return await self._get_post_no_login(url=url, uid=uid, index=index)

        if not self.logged_in:
            await self.client.pool.add_account(
                username=self.username,
                email=self.email,
                password=self.password,
                email_password=self.password,
            )
            await self.client.pool.login_all()

        return await self._get_post_login(url=url, uid=uid, index=index)

    async def _get_post_login(
        self,
        url: str,
        uid: str,
        index: int = 0,
        retry_count: int = 0,
    ) -> domain.Post:
        try:
            details = await self.client.tweet_details(int(uid))
            p = domain.Post(
                url=url,
                author=f'{details.user.displayname} ({details.user.username})',
                description=details.rawContent,
                views=details.viewCount,
                likes=details.likeCount,
                created=details.date.astimezone(),
            )

            if not details.media:
                return p

            if details.media.videos:
                url = max(details.media.videos[index].variants, key=lambda x: x.bitrate).url
            elif details.media.photos:
                url = details.media.photos[index].url
            elif details.media.animated:
                url = details.media.animated[index].videoUrl
            else:
                return p

            p.buffer = await self._download(url=url, cookies=(await self.client.pool.get_all())[0].cookies)
            return p
        except Exception as e:
            logging.error(f'Failed fetching from twitter, retrying: {str(e)}')
            if retry_count == 0:
                await self.relogin()
                return await self._get_post_login(url=url, uid=uid, index=index, retry_count=retry_count + 1)
            if retry_count == 1:
                return await self._get_post_no_login(url=url, uid=uid, index=index)

            raise exceptions.IntegrationClientError('Failed fetching from twitter') from e

    async def _get_post_no_login(self, url: str, uid: str, index: int = 0) -> domain.Post:
        tweet = json.loads(
            await self._fetch_content(url=SCRAPE_URL, data='', headers=HEADERS, params={'id': uid, 'lang': 'en'})
        )
        if not tweet:
            raise ValueError(f'Failed retreiving tweet {url}')

        post = domain.Post(
            url=url,
            author=tweet.get('user', {}).get('name'),
            description=tweet.get('text'),
            likes=tweet.get('favorite_count'),
            spoiler=tweet.get('possibly_sensitive', False),
            created=datetime.datetime.fromisoformat(tweet.get('created_at')).astimezone(),
        )

        media_details = tweet.get('mediaDetails')
        if media_details:
            media = media_details[index if index < len(media_details) else 0]
            if media.get('type') == 'photo':
                post.buffer = await self._download(url=media.get('media_url_https'))
            elif media.get('type') == 'video':
                video = max(media.get('video_info').get('variants'), key=lambda v: v.get('bitrate', 0))
                post.buffer = await self._download(url=video.get('url'))
        elif 'user' in tweet and 'profile_image_url_https' in tweet.get('user'):
            post.buffer = await self._download(url=tweet.get('user').get('profile_image_url_https'))

        return post
