import typing

import discordoauth2

from bot.auth.oauth2 import base
from bot.auth.oauth2 import types
from bot.auth.oauth2.discord import config
from bot.auth.oauth2.discord import schemas


class DiscordOauth2Auth(base.BaseOauth2Auth):
    _CONFIG_SCHEMA = config.DiscordOauth2ConfigSchema

    def __init__(self, config: typing.Dict[str, str]) -> None:
        super().__init__(config)

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

        return types.Identity(
            user=schemas.DiscordUserSchema().load(access_token.fetch_identify()),
            servers=schemas.GuildSchema(many=True).load(access_token.fetch_guilds()),
        )
