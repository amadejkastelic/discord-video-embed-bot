from bot.adapters import base


class DiscordConfig(base.BaseBotConfig):
    api_token: str


class DiscordConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = DiscordConfig
