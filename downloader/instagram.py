import io
from urllib.parse import urlparse, parse_qs

import instaloader

from downloader import base
from models import post


class InstagramClient(base.BaseClient):
    DOMAINS = ['instagram.com', 'ddinstagram.com']

    def __init__(self, url: str):
        super(InstagramClient, self).__init__(url=url)
        self.client = instaloader.Instaloader()

        parsed_url = urlparse(url)
        self.id = parsed_url.path.strip('/').split('/')[-1]
        self.index = int(parse_qs(parsed_url.query).get('img_index', ['1'])[0]) - 1

    async def get_post(self) -> post.Post:
        p = instaloader.Post.from_shortcode(self.client.context, self.id)

        match p.typename:
            case 'GraphImage':
                download_url = p.url
            case 'GraphVideo':
                download_url = p.video_url
            case 'GraphSidecar':
                node = next(p.get_sidecar_nodes(start=self.index, end=self.index))
                if node.is_video:
                    download_url = node.video_url
                else:
                    download_url = node.display_url

        with self.client.context._session.get(download_url) as resp:
            return post.Post(
                url=self.url,
                author=p.owner_profile.username,
                description=p.title or p.caption,
                likes=p.likes,
                views=p.video_view_count,
                buffer=io.BytesIO(resp.content),
            )
