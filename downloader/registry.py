import os

from downloader import base
from downloader import facebook
from downloader import instagram
from downloader import reddit
from downloader import tiktok


CLASSES = {
    instagram.InstagramClient,
    tiktok.TiktokClient,
    facebook.FacebookClient,
    reddit.RedditClient,
}


def get_instance(url: str) -> base.BaseClient:
    for klass in CLASSES:
        if any(domain in url for domain in klass.DOMAINS):
            instance = klass(url)
            if isinstance(instance, reddit.RedditClient) and not os.getenv('REDDIT_CLIENT_ID'):
                break
            return klass(url)

    raise ValueError(f'Unsupported url {url}')
