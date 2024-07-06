import typing

from bot.downloader import base
from bot.downloader.facebook import client as facebook_client
from bot.downloader.instagram import client as instagram_client
from bot.downloader.reddit import client as reddit_client
from bot.downloader.tiktok import client as tiktok_client
from bot.downloader.twitter import client as twitter_client
from bot.downloader.youtube import client as youtube_client


CLASSES: typing.Set[base.BaseClientSingleton] = {
    facebook_client.FacebookClientSingleton,
    instagram_client.InstagramClientSingleton,
    reddit_client.RedditClientSingleton,
    tiktok_client.TiktokClientSingleton,
    twitter_client.TwitterClientSingleton,
    youtube_client.YoutubeClientSingleton,
}


def get_instance(url: str) -> base.BaseClient:
    for klass in CLASSES:
        if any(domain in url for domain in klass.DOMAINS):
            return klass.get_instance()

    raise ValueError(f'Unsupported url {url}')
