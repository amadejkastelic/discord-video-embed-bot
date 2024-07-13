from bot.downloader import base


class TwitchConfig(base.BaseClientConfig):
    """
    No additional settings for Twitch integration
    """


class TwitchConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = TwitchConfig
