import typing

from models import post


class BaseClient(object):
    DOMAINS: typing.List[str]
    MESSAGE = '🔗 URL: {url}\n📕 Description: {description}\n👍 Likes: {likes}\n'

    def __init__(self, url: str):
        self.url = url

    async def download(self) -> post.Post:
        raise NotImplementedError()
