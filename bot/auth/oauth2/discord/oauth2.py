import typing

import discordoauth2

from bot.auth.oauth2 import base
from bot.auth.oauth2 import types
from bot.auth.oauth2.discord import config


class DiscordOAuth2Auth(base.BaseOauth2Auth):
    _CONFIG_CLASS = config.DiscordOAuth2Config

    def __init__(self, conf: typing.Dict[str, str]) -> None:
        super().__init__(conf)

        self.client = discordoauth2.Client(
            id=int(self.config.client_id),
            secret=self.config.client_secret,
            redirect=self.config.redirect_uri,
            bot_token=self.config.api_token,
        )

    def generate_uri(self, scope: typing.List[str]) -> str:
        return self.client.generate_uri(scope=scope)

    def exchange_code(self, code: str) -> types.Identity:
        access_token = self.client.exchange_code(code=code)

        access_token.update_metadata('EmbedBot', 'Username')

        return types.Identity.model_validate(
            {
                'user': access_token.fetch_identify(),
                'servers': access_token.fetch_guilds(),
            }
        )
