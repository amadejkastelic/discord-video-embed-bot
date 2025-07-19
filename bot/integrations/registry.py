import typing

from bot.integrations import base
from bot.integrations.bluesky import client as bluesky_client
from bot.integrations.facebook import client as facebook_client
from bot.integrations.four_chan import client as four_chan_client
from bot.integrations.instagram import singleton as instagram_client
from bot.integrations.linkedin import client as linkedin_client
from bot.integrations.ninegag import client as ninegag_client
from bot.integrations.reddit import client as reddit_client
from bot.integrations.threads import client as threads_client
from bot.integrations.tiktok import client as tiktok_client
from bot.integrations.truth_social import client as truth_social_client
from bot.integrations.twenty4ur import client as twenty4ur_client
from bot.integrations.twitch import client as twitch_client
from bot.integrations.twitter import client as twitter_client
from bot.integrations.youtube import client as youtube_client

CLASSES: typing.Set[typing.Type[base.BaseClientSingleton]] = {
    bluesky_client.BlueskyClientSingleton,
    facebook_client.FacebookClientSingleton,
    four_chan_client.FourChanClientSingleton,
    instagram_client.InstagramClientSingleton,
    linkedin_client.LinkedinClientSingleton,
    ninegag_client.NineGagClientSingleton,
    reddit_client.RedditClientSingleton,
    threads_client.ThreadsClientSingleton,
    tiktok_client.TiktokClientSingleton,
    truth_social_client.TruthSocialClientSingleton,
    twenty4ur_client.Twenty4UrClientSingleton,
    twitch_client.TwitchClientSingleton,
    twitter_client.TwitterClientSingleton,
    youtube_client.YoutubeClientSingleton,
}


def should_handle(url: str) -> bool:
    for klass in CLASSES:
        if klass.should_handle(url):
            return klass.get_instance() is not None

    return False


def get_instance(url: str) -> typing.Optional[base.BaseClient]:
    for klass in CLASSES:
        if any(domain in url for domain in klass.DOMAINS):
            return klass.get_instance()

    raise ValueError(f'Unsupported url {url}')
