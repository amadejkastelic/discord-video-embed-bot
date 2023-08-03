import uuid
import io
import glob
import os
import requests

from RedDownloader import RedDownloader

from downloader import base
from models import post


class RedditClient(base.BaseClient):
    DOMAINS = ['reddit.com', 'redd.it']

    def __init__(self, url: str):
        super(RedditClient, self).__init__(url=url)

    async def download(self) -> post.Post:
        media = RedDownloader.Download(url=self.url, quality=720, destination='/tmp/', output=str(uuid.uuid4()))

        p = post.Post(
            url=self.url,
            description=media.GetPostTitle().Get(),
            author=media.GetPostAuthor().Get(),
            spoiler=self._is_nsfw,
        )

        files = glob.glob(os.path.join(media.destination, f'{media.output}*'))
        if files:
            with open(files[0], 'rb') as f:
                p.buffer = io.BytesIO(f.read())

            for file in files:
                os.remove(file)

        return p

    def _is_nsfw(self) -> bool:
        return 'nsfw' in str(requests.get(self.url).content)
