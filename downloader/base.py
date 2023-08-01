import io
import typing


class BaseClient(object):
    DOMAINS: typing.List[str]
    MESSAGE = '🔗 URL: {url}\n📕 Title: {title}\n👍 Likes: {likes}\n'

    def __init__(self, url: str):
        self.url = url

    async def download(self) -> typing.Tuple[str, io.BytesIO]:
        raise NotImplementedError()
