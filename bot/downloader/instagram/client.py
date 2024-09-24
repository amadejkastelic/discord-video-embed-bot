import io
import os
import typing
from urllib.parse import parse_qs, urlparse

import instaloader
import requests
from django.conf import settings

from bot import constants as bot_constants
from bot import domain
from bot import logger
from bot.downloader import base
from bot.downloader.instagram import config
from bot.downloader.instagram import constants


class InstagramClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['instagram.com', 'ddinstagram.com']
    _CONFIG_CLASS = config.InstagramConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.InstagramConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('instagram', {}))

        if not conf.enabled:
            logger.info('Instagram integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = InstagramClient(
            username=conf.username,
            password=conf.password,
            session_file_path=conf.session_file_path,
            user_agent=conf.user_agent,
        )


class InstagramClient(base.BaseClient):
    INTEGRATION = bot_constants.Integration.INSTAGRAM

    def __init__(
        self,
        username: typing.Optional[str],
        password: typing.Optional[str],
        session_file_path: typing.Optional[str],
        user_agent: typing.Optional[str],
    ):
        super().__init__()

        self.client = instaloader.Instaloader(user_agent=user_agent)
        if username and session_file_path and os.path.exists(session_file_path):
            self.client.load_session_from_file(username=username, filename=session_file_path)
        elif username and password:
            self.client.login(username, password)

    async def get_integration_data(
        self,
        url: str,
    ) -> typing.Tuple[bot_constants.Integration, str, typing.Optional[int]]:
        uid, index, _ = self._parse_url(url)
        return self.INTEGRATION, uid, index

    async def get_post(self, url: str) -> domain.Post:
        uid, index, link_type = self._parse_url(url)

        match link_type:
            case constants.LinkType.STORY:
                return self._get_story(url=url, uid=uid)
            case constants.LinkType.MEDIA:
                return self._get_post(url=url, uid=uid, index=index)
            case constants.LinkType.PROFILE:
                return self._get_profile(url=url, uid=uid)

        raise NotImplementedError(f'Not yet implemented for {url}')

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        uid, _, _ = self._parse_url(url)
        p = instaloader.Post.from_shortcode(context=self.client.context, shortcode=uid)

        comments = []
        for i, comment in enumerate(p.get_comments()):
            comments.append(
                domain.Comment(
                    author=comment.owner.username,
                    created=comment.created_at_utc,
                    likes=comment.likes_count,
                    comment=comment.text,
                )
            )
            if i + 1 == n:
                break

        return comments

    @staticmethod
    def _parse_url(url: str) -> typing.Tuple[str, int, constants.LinkType]:
        parsed_url = urlparse(url)
        uid = parsed_url.path.strip('/').split('/')[-1]
        index = int(parse_qs(parsed_url.query).get('img_index', ['1'])[0]) - 1
        link_type = constants.LinkType.from_url(url=url)

        return uid, index, link_type

    def _get_post(self, url: str, uid: str, index: int = 0) -> domain.Post:
        p = instaloader.Post.from_shortcode(context=self.client.context, shortcode=uid)

        match p.typename:
            case 'GraphImage':
                download_url = p.url
            case 'GraphVideo':
                download_url = p.video_url
            case 'GraphSidecar':
                node = next(p.get_sidecar_nodes(start=index, end=index))
                if node.is_video:
                    download_url = node.video_url
                else:
                    download_url = node.display_url

        with requests.get(url=download_url, timeout=base.DEFAULT_TIMEOUT) as resp:
            return domain.Post(
                url=url,
                author=p.owner_profile.username,
                description=p.title or p.caption,
                likes=p.likes,
                views=p.video_view_count,
                buffer=io.BytesIO(resp.content),
                created=p.date_local,
            )

    def _get_story(self, url: str, uid: str) -> domain.Post:
        story = instaloader.StoryItem.from_mediaid(context=self.client.context, mediaid=int(uid))
        if story.is_video:
            url = story.video_url or story.url
        else:
            url = story.url or story.video_url

        with requests.get(url=url, timeout=base.DEFAULT_TIMEOUT) as resp:
            return domain.Post(
                url=url,
                author=story.owner_profile.username,
                description=story.caption,
                buffer=io.BytesIO(resp.content),
                created=story.date_local,
            )

    def _get_profile(self, url: str, uid: str) -> domain.Post:
        profile = instaloader.Profile.from_username(context=self.client.context, username=uid)

        with requests.get(url=profile.profile_pic_url, timeout=base.DEFAULT_TIMEOUT) as resp:
            return domain.Post(
                url=url,
                author=profile.username,
                description=profile.biography,
                buffer=io.BytesIO(resp.content),
                likes=profile.followers,
            )
