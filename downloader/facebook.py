import os

import facebook_scraper

import domain
from downloader import base


class FacebookClient(base.BaseClient):
    DOMAINS = ['facebook.com', 'fb.watch']

    async def get_post(self) -> domain.Post:
        kwargs = {}
        if os.path.exists('cookies.txt'):
            kwargs['cookies'] = 'cookies.txt'

        fb_post = next(facebook_scraper.get_posts(post_urls=[self.url], **kwargs))

        ts = fb_post.get('time')
        post = domain.Post(
            url=self.url,
            author=fb_post.get('username'),
            description=fb_post.get('text'),
            likes=fb_post.get('likes'),
            created=ts.astimezone() if ts else None,
        )

        if fb_post.get('video'):
            post.buffer = await self._download(url=fb_post['video'])
        elif fb_post.get('images'):
            post.buffer = await self._download(url=fb_post['images'][0])

        return post
