import io


class BaseClient(object):
    DOMAIN: str

    def __init__(self, url: str):
        self.url = url

    async def download(self) -> io.BytesIO:
        raise NotImplementedError()
