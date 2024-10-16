import io

import pytubefix as pytube
from pytubefix.innertube import _default_clients

import models
from downloader import base


# Age restriction bypass - https://stackoverflow.com/a/78267693/10428848
_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]


class YoutubeClient(base.BaseClient):
    DOMAINS = ['youtube.com/shorts']

    async def get_post(self) -> models.Post:
        vid = pytube.YouTube(self.url)

        post = models.Post(
            url=self.url,
            author=vid.author,
            description=vid.title,
            views=vid.views,
            created=vid.publish_date,
            buffer=io.BytesIO(),
        )

        vid.streams.filter(progressive=True, file_extension='mp4').order_by(
            'resolution'
        ).desc().first().stream_to_buffer(post.buffer)

        return post
