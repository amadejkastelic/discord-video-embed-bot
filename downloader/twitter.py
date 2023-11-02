import datetime
import json
import logging
import os
import typing

import twscrape

import models
from downloader import base

scrape_url = 'https://cdn.syndication.twimg.com/tweet-result'
headers = {
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


class TwitterClientSingleton(object):
    INSTANCE: typing.Optional[twscrape.API] = None

    @classmethod
    async def get_instance(cls) -> typing.Optional[twscrape.API]:
        username = os.getenv('TWITTER_USERNAME')
        email = os.getenv('TWITTER_EMAIL')
        password = os.getenv('TWITTER_PASSWORD')
        if not all([username, email, password]):
            return None

        if not cls.INSTANCE:
            cls.INSTANCE = twscrape.API()
            await cls.INSTANCE.pool.add_account(
                username=username, email=email, password=password, email_password=password
            )
            await cls.INSTANCE.pool.login_all()

        return cls.INSTANCE

    @classmethod
    async def relogin(cls) -> None:
        if cls.INSTANCE:
            await cls.INSTANCE.pool.relogin(usernames=[os.getenv('TWITTER_USERNAME')])


class TwitterClient(base.BaseClient):
    DOMAINS = ['twitter.com', 'x.com']

    def __init__(self, url: str):
        super(TwitterClient, self).__init__(url=url)
        metadata = url.split('/status/')[-1].split('?')[0].split('/')
        self.id = metadata[0]
        self.index = int(metadata[2]) - 1 if len(metadata) == 3 and metadata[1] == 'photo' else 0

    async def get_post(self) -> models.Post:
        client = await TwitterClientSingleton.get_instance()
        if not client:
            return await self._get_post_no_login()

        return await self._get_post_login(client=client)

    async def _get_post_login(self, client: twscrape.API, retry_count=0) -> models.Post:
        try:
            details = await client.tweet_details(int(self.id))
            p = models.Post(
                url=self.url,
                author=f'{details.user.displayname} ({details.user.username})',
                description=details.rawContent,
                views=details.viewCount,
                likes=details.likeCount,
                created=details.date.astimezone(),
            )

            if not details.media:
                return p

            if details.media.videos:
                url = max(details.media.videos[0].variants, key=lambda x: x.bitrate).url
            elif details.media.photos:
                url = details.media.photos[0].url
            elif details.media.animated:
                url = details.media.animated[0].videoUrl
            else:
                return p

            p.buffer = await self._download(url=url, cookies=(await client.pool.get_all())[0].cookies)
            return p
        except Exception as e:
            logging.error(f'Failed fetching from twitter, retrying: {str(e)}')
            if retry_count == 0:
                await TwitterClientSingleton.relogin()
                return await self._get_post_login(client=client, retry_count=retry_count + 1)
            elif retry_count == 1:
                return await self._get_post_no_login()
            else:
                raise Exception('Failed fetching from twitter')

    async def _get_post_no_login(self) -> models.Post:
        tweet = json.loads(
            await self._fetch_content(url=scrape_url, data='', headers=headers, params={'id': self.id, 'lang': 'en'})
        )
        if not tweet:
            raise ValueError(f'Failed retreiving tweet {self.url}')

        post = models.Post(
            url=self.url,
            author=tweet.get('user', {}).get('name'),
            description=tweet.get('text'),
            likes=tweet.get('favorite_count'),
            spoiler=tweet.get('possibly_sensitive', False),
            created=datetime.datetime.fromisoformat(tweet.get('created_at')).astimezone(),
        )

        media_details = tweet.get('mediaDetails')
        if media_details:
            media = media_details[self.index if self.index < len(media_details) else 0]
            if media.get('type') == 'photo':
                post.buffer = await self._download(url=media.get('media_url_https'))
            elif media.get('type') == 'video':
                video = max(media.get('video_info').get('variants'), key=lambda v: v.get('bitrate', 0))
                post.buffer = await self._download(url=video.get('url'))
        elif 'user' in tweet and 'profile_image_url_https' in tweet.get('user'):
            post.buffer = await self._download(url=tweet.get('user').get('profile_image_url_https'))

        return post
