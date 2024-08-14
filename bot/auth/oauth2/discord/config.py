from bot.auth.oauth2 import base


class DiscordOAuth2Config(base.BaseOAuth2Config):
    api_token: str
