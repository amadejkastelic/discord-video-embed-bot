import io
import os
import requests
import typing
from urllib.parse import urlparse, parse_qs

import instaloader

from downloader import base
from models import post


class InstagramClientSingleton(object):
    INSTANCE: typing.Optional[instaloader.Instaloader] = None

    @classmethod
    def get_instance(cls) -> typing.Optional[instaloader.Instaloader]:
        if cls.INSTANCE:
            return cls.INSTANCE

        cls.INSTANCE = instaloader.Instaloader(
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0'
        )
        if os.path.exists('instagram.sess'):
            cls.INSTANCE.load_session_from_file(username='amadejkastelic', filename='instagram.sess')

        return cls.INSTANCE


class InstagramClient(base.BaseClient):
    DOMAINS = ['instagram.com', 'ddinstagram.com']

    def __init__(self, url: str):
        super(InstagramClient, self).__init__(url=url)
        self.client = InstagramClientSingleton.get_instance()

        parsed_url = urlparse(url)
        self.id = parsed_url.path.strip('/').split('/')[-1]
        self.index = int(parse_qs(parsed_url.query).get('img_index', ['1'])[0]) - 1
        self._is_story = '/stories/' in url

    async def get_post(self) -> post.Post:
        if self._is_story:
            return self._get_story()

        return self._get_post()

    def _get_post(self) -> post.Post:
        p = instaloader.Post.from_shortcode(self.client.context, self.id)

        match p.typename:
            case 'GraphImage':
                download_url = p.url
            case 'GraphVideo':
                download_url = p.video_url
            case 'GraphSidecar':
                node = next(p.get_sidecar_nodes(start=self.index, end=self.index))
                if node.is_video:
                    download_url = node.video_url
                else:
                    download_url = node.display_url

        with requests.get(url=download_url) as resp:
            return post.Post(
                url=self.url,
                author=p.owner_profile.username,
                description=p.title or p.caption,
                likes=p.likes,
                views=p.video_view_count,
                buffer=io.BytesIO(resp.content),
                created=p.date_local,
            )

    def _get_story(self) -> post.Post:
        story = instaloader.StoryItem.from_mediaid(self.client.context, int(self.id))
        if story.is_video:
            url = story.video_url
        else:
            url = story.url

        with requests.get(url=url) as resp:
            return post.Post(
                url=self.url,
                author=story.owner_profile.username,
                description=story.caption,
                buffer=io.BytesIO(resp.content),
                created=story.date_local,
            )
