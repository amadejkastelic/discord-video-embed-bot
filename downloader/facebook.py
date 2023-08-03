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

        fb_post = next(facebook_scraper.get_posts(post_urls=[self.url], cookies='cookies.txt'))

        p = post.Post(
            url=self.url,
            author=fb_post.get('username'),
            description=fb_post.get('text'),
            likes=fb_post.get('likes'),
        )

        if fb_post.get('video'):
            p.buffer = await self._download(url=fb_post['video'])
        elif fb_post.get('images'):
            p.buffer = await self._download(url=fb_post['images'][0])

        return p

    async def _download(self, url: str) -> io.BytesIO:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                return io.BytesIO(await resp.read())
