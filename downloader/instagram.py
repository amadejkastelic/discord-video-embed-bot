import io
import typing
from urllib.parse import urlparse, parse_qs

import instaloader

from downloader import base


class InstagramClient(base.BaseClient):
    DOMAINS = ['instagram.com', 'ddinstagram.com']

    def __init__(self, url: str):
        super(InstagramClient, self).__init__(url=url)
        self.client = instaloader.Instaloader()

        parsed_url = urlparse(url)
        self.id = parsed_url.path.strip('/').split('/')[-1]
        self.index = int(parse_qs(parsed_url.query).get('img_index', ['1'])[0]) - 1

    async def download(self) -> typing.Tuple[str, io.BytesIO]:
        post = instaloader.Post.from_shortcode(self.client.context, self.id)

        match post.typename:
            case 'GraphImage':
                download_url = post.url
            case 'GraphVideo':
                download_url = post.video_url
            case 'GraphSidecar':
                node = next(post.get_sidecar_nodes(start=self.index, end=self.index))
                if node.is_video:
                    download_url = node.video_url
                else:
                    download_url = node.display_url

        with self.client.context._session.get(download_url) as resp:
            return (
                self.MESSAGE.format(
                    url=self.url,
                    description=post.title or post.caption,
                    likes=post.likes,
                ),
                io.BytesIO(resp.content),
            )
