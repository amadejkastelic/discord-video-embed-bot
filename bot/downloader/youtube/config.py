from bot.downloader import base


class YoutubeConfig(base.BaseClientConfig):
    """
    No additional settings for Youtube integration
    """


class YoutubeConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = YoutubeConfig
