from dataclasses import dataclass

from marshmallow import fields

from bot.auth.oauth2 import base


@dataclass
class DiscordOauth2Config(base.BaseOauth2Config):
    api_token: str


class DiscordOauth2ConfigSchema(base.BaseOauth2ConfigSchema):
    _CONFIG_TYPE = DiscordOauth2Config

    api_token = fields.Str()
