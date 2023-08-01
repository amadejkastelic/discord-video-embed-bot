import aiohttp
import io
import os

import facebook_scraper

from downloader import base


class FacebookClient(base.BaseClient):
    DOMAINS = ['facebook.com', 'fb.watch']

    async def download(self) -> io.BytesIO:
        if not os.path.exists('cookies.txt'):
            raise RuntimeError('cookies.txt missing, please export facebook cookies and place them in the app root')

        post = next(facebook_scraper.get_posts(post_urls=[self.url], cookies='cookies.txt', options={'video': True}))

        async with aiohttp.ClientSession() as session:
            async with session.get(post['video']) as resp:
                return io.BytesIO(await resp.read())
