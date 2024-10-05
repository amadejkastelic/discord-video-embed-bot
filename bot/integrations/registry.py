import typing

from bot.integrations import base
from bot.integrations.facebook import client as facebook_client
from bot.integrations.instagram import singleton as instagram_client
from bot.integrations.reddit import client as reddit_client
from bot.integrations.threads import client as threads_client
from bot.integrations.tiktok import client as tiktok_client
from bot.integrations.twenty4ur import client as twenty4ur_client
from bot.integrations.twitch import client as twitch_client
from bot.integrations.twitter import client as twitter_client
from bot.integrations.youtube import client as youtube_client


CLASSES: typing.Set[typing.Type[base.BaseClientSingleton]] = {
    facebook_client.FacebookClientSingleton,
    instagram_client.InstagramClientSingleton,
    reddit_client.RedditClientSingleton,
    threads_client.ThreadsClientSingleton,
    tiktok_client.TiktokClientSingleton,
    twenty4ur_client.Twenty4UrClientSingleton,
    twitch_client.TwitchClientSingleton,
    twitter_client.TwitterClientSingleton,
    youtube_client.YoutubeClientSingleton,
}


def should_handle(url: str) -> bool:
    for klass in CLASSES:
        if any(domain in url for domain in klass.DOMAINS):
            return klass.get_instance() is not None

    return False


def get_instance(url: str) -> typing.Optional[base.BaseClient]:
    for klass in CLASSES:
        if any(domain in url for domain in klass.DOMAINS):
            return klass.get_instance()

    raise ValueError(f'Unsupported url {url}')
