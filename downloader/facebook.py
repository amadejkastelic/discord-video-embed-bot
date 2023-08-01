import aiohttp
import io
import os
import typing

import facebook_scraper

from downloader import base


class FacebookClient(base.BaseClient):
    DOMAINS = ['facebook.com', 'fb.watch']

    async def download(self) -> typing.Tuple[str, io.BytesIO]:
        if not os.path.exists('cookies.txt'):
            raise RuntimeError('cookies.txt missing, please export facebook cookies and place them in the app root')

        post = next(facebook_scraper.get_posts(post_urls=[self.url], cookies='cookies.txt', options={'video': True}))
        title = post.get('text', '')
        likes = post.get('likes', 0)

        async with aiohttp.ClientSession() as session:
            async with session.get(post['video']) as resp:
                return self.MESSAGE.format(url=self.url, title=title, likes=likes), io.BytesIO(await resp.read())
