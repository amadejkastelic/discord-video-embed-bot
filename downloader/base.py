import io
import typing


class BaseClient(object):
    DOMAINS: typing.List[str]

    def __init__(self, url: str):
        self.url = url

    async def download(self) -> io.BytesIO:
        raise NotImplementedError()
