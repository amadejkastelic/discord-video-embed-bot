from bot.downloader import base


class DiscordConfig(base.BaseClientConfig):
    """
    No additional settings for Discord bot integration
    """


class DiscordConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = DiscordConfig
