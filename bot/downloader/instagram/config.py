import typing
from dataclasses import dataclass

from marshmallow import fields as marshmallow_fields

from bot.downloader import base


@dataclass
class InstagramConfig(base.BaseClientConfig):
    session_file_path: typing.Optional[str] = None
    username: typing.Optional[str] = None
    user_agent: typing.Optional[str] = None


class InstagramConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = InstagramConfig

    session_file_path = marshmallow_fields.Str(allow_none=True, load_default=None)
    username = marshmallow_fields.Str(allow_none=True, load_default=None)
    user_agent = marshmallow_fields.Str(allow_none=True, load_default=None)
