import io
import typing

import aiohttp

import models


class BaseClient(object):
    DOMAINS: typing.List[str]
    MESSAGE = '🔗 URL: {url}\n📕 Description: {description}\n👍 Likes: {likes}\n'

    def __init__(self, url: str):
        self.url = url

    async def get_post(self) -> models.Post:
        raise NotImplementedError()

    async def _download(self, url: str, cookies: typing.Optional[typing.Dict[str, str]] = None, **kwargs) -> io.BytesIO:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url=url, **kwargs) as resp:
                return io.BytesIO(await resp.read())

    async def _fetch_content(self, url: str, cookies: typing.Optional[typing.Dict[str, str]] = None, **kwargs) -> str:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url=url, **kwargs) as resp:
                return await resp.text()
