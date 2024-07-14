import typing
from dataclasses import dataclass

from marshmallow import fields as marshmallow_fields

from bot.downloader import base


@dataclass
class FacebookConfig(base.BaseClientConfig):
    cookies_file_path: typing.Optional[str] = None


class FacebookConfigSchema(base.BaseClientConfigSchema):
    _CONFIG_CLASS = FacebookConfig

    cookies_file_path = marshmallow_fields.Str(allow_none=True, load_default=None)
