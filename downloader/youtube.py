import io

import pytube

from downloader import base
from models import post


class YoutubeClient(base.BaseClient):
    DOMAINS = ['youtube.com/shorts']

    async def get_post(self) -> post.Post:
        vid = pytube.YouTube(self.url)

        p = post.Post(
            url=self.url,
            author=vid.author,
            description=vid.title,
            views=vid.views,
            created=vid.publish_date,
            buffer=io.BytesIO(),
        )

        vid.streams.filter(progressive=True, file_extension='mp4').order_by(
            'resolution'
        ).desc().first().stream_to_buffer(p.buffer)

        return p
