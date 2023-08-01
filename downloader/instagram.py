import aiohttp
import io
from urllib.parse import urlparse

import instaloader

from downloader import base


class InstagramClient(base.BaseClient):
    DOMAINS = ['instagram.com', 'ddinstagram.com']

    def __init__(self, url: str):
        self.client = instaloader.Instaloader()
        self.id = urlparse(url).path.strip('/').split('/')[-1]

    async def download(self) -> io.BytesIO:
        post = instaloader.Post.from_shortcode(self.client.context, self.id)

        async with aiohttp.ClientSession() as session:
            async with session.get(post.video_url) as resp:
                return io.BytesIO(await resp.read())
