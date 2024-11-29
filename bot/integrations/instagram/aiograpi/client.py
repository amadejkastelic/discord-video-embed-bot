import typing
from urllib.parse import parse_qs, urlparse

import aiograpi
from aiograpi import exceptions as aiograpi_exceptions

from bot import constants as bot_constants
from bot import domain
from bot.integrations import base


class InstagramClient(base.BaseClient):
    INTEGRATION = bot_constants.Integration.INSTAGRAM

    def __init__(
        self,
        username: typing.Optional[str],
        password: typing.Optional[str],
        **kwargs,
    ):
        super().__init__()

        self.username = username
        self.password = password
        self.client = aiograpi.Client()

    async def login(self, relogin: bool = False):
        await self.client.login(
            username=self.username,
            password=self.password,
            relogin=relogin,
        )

    async def get_integration_data(
        self,
        url: str,
    ) -> typing.Tuple[bot_constants.Integration, str, typing.Optional[int]]:
        if 'stories' in url:
            pk = self.client.story_pk_from_url(url)
        else:
            pk = await self.client.media_pk_from_url(url)
        return self.INTEGRATION, pk, max(0, int(parse_qs(urlparse(url).query).get('img_index', ['1'])[0]) - 1)

    async def get_post(self, url: str) -> domain.Post:
        try:
            return await self._get_post(url)
        except (aiograpi_exceptions.PreLoginRequired, aiograpi_exceptions.ClientLoginRequired):
            await self.login()
        except aiograpi_exceptions.LoginRequired:
            await self.login(relogin=True)
        except aiograpi_exceptions.ReloginAttemptExceeded:
            await self.login()

        return await self._get_post(url)

    async def _get_post(self, url: str) -> domain.Post:  # noqa: C901
        _, pk, idx = await self.get_integration_data(url)

        if 'stories' in url:
            return await self._get_story(url, pk)

        media_info = await self.client.media_info(pk)

        post = domain.Post(
            url=url,
            author=media_info.user.username,
            description=media_info.caption_text,
            views=media_info.view_count,
            likes=media_info.like_count,
            created=media_info.taken_at,
        )

        media_url = None
        if media_info.video_url:
            media_url = str(media_info.video_url)
        elif len(media_info.video_versions) > 0:
            media_url = media_info.video_versions[0].get('url')
        elif len(media_info.resources) > idx:
            media_url = media_info.resources[idx].video_url
            if not media_url and len(media_info.resources) > idx:
                media_url = media_info.resources[idx].video_versions[0].get('url')
                if not media_url:
                    media_url = media_info.resources[idx].image_versions2['candidates'][0]['url']
        elif len(media_info.image_versions2.get('candidates', [])) > 0:
            media_url = media_info.image_versions2['candidates'][0]['url']

        if media_url:
            post.buffer = await self._download(url=str(media_url), cookies=self.client.cookie_dict)

        return post

    async def _get_story(self, url: str, pk: str) -> domain.Post:
        story_info = await self.client.story_info(pk)

        post = domain.Post(
            url=url,
            author=story_info.user.username or story_info.user.full_name,
            created=story_info.taken_at,
        )

        if story_info.video_url:
            post.buffer = await self._download(url=str(story_info.video_url), cookies=self.client.cookie_dict)
        elif story_info.medias:
            media_info = await self.client.media_info(story_info.medias[0].media_pk)
            post.buffer = await self._download(
                url=str(media_info.video_url or media_info.image_versions2['candidates'][0]['url']),
                cookies=self.client.cookie_dict,
            )
        elif story_info.thumbnail_url:
            post.buffer = await self._download(url=str(story_info.thumbnail_url), cookies=self.client.cookie_dict)

        return post
