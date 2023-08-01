from downloader import base
from downloader import facebook
from downloader import instagram
from downloader import tiktok


CLASSES = {
    instagram.InstagramClient,
    tiktok.TiktokClient,
    facebook.FacebookClient,
}


def get_instance(url: str) -> base.BaseClient:
    for klass in CLASSES:
        if any(domain in url for domain in klass.DOMAINS):
            return klass(url)

    raise ValueError(f'Unsupported url {url}')
