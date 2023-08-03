import aiohttp
import json

from downloader import base
from models import post

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


class TwitterClient(base.BaseClient):
    DOMAINS = ['twitter.com', 'x.com']

    def __init__(self, url: str):
        super(TwitterClient, self).__init__(url=url)
        self.id = url.split('/')[-1].split('?')[0]

    async def get_post(self) -> post.Post:
        tweet = json.loads(
            await self._fetch_content(url=scrape_url, data='', headers=headers, params={'id': self.id, 'lang': 'en'})
        )
        if not tweet:
            raise ValueError(f'Failed retreiving tweet {self.url}')

        p = post.Post(
            url=self.url,
            author=tweet.get('user', {}).get('name'),
            description=tweet.get('text'),
            likes=tweet.get('favorite_count'),
            spoiler=tweet.get('possibly_sensitive', False),
        )

        media_details = tweet.get('mediaDetails')
        if media_details:
            media = media_details[0]
            if media.get('type') == 'photo':
                p.buffer = await self._download(url=media.get('media_url_https'))
            elif media.get('type') == 'video':
                video = max(media.get('video_info').get('variants'), key=lambda v: v.get('bitrate', 0))
                p.buffer = await self._download(url=video.get('url'))
        elif 'user' in tweet and 'profile_image_url_https' in tweet.get('user'):
            p.buffer = await self._download(url=tweet.get('user').get('profile_image_url_https'))

        return p
