import typing
from dataclasses import dataclass

from marshmallow import fields as marshmallow_fields

from bot.downloader import base


@dataclass
class RedditConfig(base.BaseClientConfig):
    client_id: typing.Optional[str] = None
    client_secret: typing.Optional[str] = None
    user_agent: typing.Optional[str] = None


class RedditConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = RedditConfig

    client_id = marshmallow_fields.Str(allow_none=True, load_default=None)
    client_secret = marshmallow_fields.Str(allow_none=True, load_default=None)
    user_agent = marshmallow_fields.Str(allow_none=True, load_default=None)
