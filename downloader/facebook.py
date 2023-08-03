import aiohttp
import io
import os

import facebook_scraper

from downloader import base
from models import post


class FacebookClient(base.BaseClient):
    DOMAINS = ['facebook.com', 'fb.watch']

    async def download(self) -> post.Post:
        if not os.path.exists('cookies.txt'):
            raise RuntimeError('cookies.txt missing, please export facebook cookies and place them in the app root')

        video = next(facebook_scraper.get_posts(post_urls=[self.url], cookies='cookies.txt', options={'video': True}))

        async with aiohttp.ClientSession() as session:
            async with session.get(video['video']) as resp:
                return post.Post(
                    url=self.url,
                    author=video.get('username'),
                    description=video.get('text'),
                    likes=video.get('likes'),
                    buffer=io.BytesIO(await resp.read()),
                )
