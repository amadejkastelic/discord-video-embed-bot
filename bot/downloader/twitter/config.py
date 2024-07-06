import typing
from dataclasses import dataclass

from marshmallow import fields as marshmallow_fields

from bot.downloader import base


@dataclass
class TwitterConfig(base.BaseClientConfig):
    email: typing.Optional[str] = None
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None


class TwitterConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = TwitterConfig

    email = marshmallow_fields.Email(allow_none=True, load_default=None)
    username = marshmallow_fields.Str(allow_none=True, load_default=None)
    password = marshmallow_fields.Str(allow_none=True, load_default=None)
