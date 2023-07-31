from downloader import base
from downloader import instagram
from downloader import tiktok


CLASSES = {
    instagram.InstagramClient,
    tiktok.TiktokClient,
}


def get_instance(url: str) -> base.BaseClient:
    for klass in CLASSES:
        if klass.DOMAIN in url:
            return klass(url)

    raise ValueError(f'Unsupported url {url}')
