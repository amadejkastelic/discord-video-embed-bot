import enum
import io
import os
import typing
from urllib.parse import parse_qs, urlparse

import instaloader
import requests

import models
from downloader import base


class LinkType(enum.Enum):
    MEDIA = 1
    PROFILE = 2
    STORY = 3

    @classmethod
    def from_url(cls, url: str) -> typing.Self:
        if '/p/' in url or '/reel/' in url:
            return cls.MEDIA
        if '/stories/' in url or '/story/' in url:
            return cls.STORY
        return cls.PROFILE


class InstagramClientSingleton(object):
    INSTANCE: typing.Optional[instaloader.Instaloader] = None

    @classmethod
    def get_instance(cls) -> typing.Optional[instaloader.Instaloader]:
        if cls.INSTANCE:
            return cls.INSTANCE

        cls.INSTANCE = instaloader.Instaloader(
            user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0'
        )
        if os.path.exists('instagram.sess') and os.getenv('INSTAGRAM_USERNAME') is not None:
            cls.INSTANCE.load_session_from_file(username=os.getenv('INSTAGRAM_USERNAME'), filename='instagram.sess')

        return cls.INSTANCE


class InstagramClient(base.BaseClient):
    DOMAINS = ['instagram.com', 'ddinstagram.com']

    def __init__(self, url: str):
        super(InstagramClient, self).__init__(url=url)
        self.client = InstagramClientSingleton.get_instance()

        parsed_url = urlparse(url)
        self.id = parsed_url.path.strip('/').split('/')[-1]
        self.index = int(parse_qs(parsed_url.query).get('img_index', ['1'])[0]) - 1
        self._link_type = LinkType.from_url(url=url)

    async def get_post(self) -> models.Post:
        match self._link_type:
            case LinkType.STORY:
                return self._get_story()
            case LinkType.MEDIA:
                return self._get_post()
            case LinkType.PROFILE:
                return self._get_profile()

        raise NotImplementedError(f'Not yet implemented for {self.url}')

    def _get_post(self) -> models.Post:
        p = instaloader.Post.from_shortcode(context=self.client.context, shortcode=self.id)

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
            return models.Post(
                url=self.url,
                author=p.owner_profile.username,
                description=p.title or p.caption,
                likes=p.likes,
                views=p.video_view_count,
                buffer=io.BytesIO(resp.content),
                created=p.date_local,
            )

    def _get_story(self) -> models.Post:
        story = instaloader.StoryItem.from_mediaid(context=self.client.context, mediaid=int(self.id))
        if story.is_video:
            url = story.video_url or story.url
        else:
            url = story.url or story.video_url

        with requests.get(url=url) as resp:
            return models.Post(
                url=self.url,
                author=story.owner_profile.username,
                description=story.caption,
                buffer=io.BytesIO(resp.content),
                created=story.date_local,
            )

    def _get_profile(self) -> models.Post:
        profile = instaloader.Profile.from_username(context=self.client.context, username=self.id)

        with requests.get(url=profile.profile_pic_url) as resp:
            return models.Post(
                url=self.url,
                author=profile.username,
                description=profile.biography,
                buffer=io.BytesIO(resp.content),
                likes=profile.followers,
            )
