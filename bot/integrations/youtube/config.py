from bot.integrations import base


class YoutubeConfig(base.BaseClientConfig):
    external_likes_api: bool = False
