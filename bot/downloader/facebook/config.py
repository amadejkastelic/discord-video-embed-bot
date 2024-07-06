import typing
from dataclasses import dataclass

from marshmallow import fields as marshmallow_fields

from bot.downloader import base


@dataclass
class FacebookConfig(base.BaseClientConfig):
    cookies_file_path: typing.Optional[str] = None


class FacebookConfigSchema(base.BaseClientConfigSchema):
    cookies_file_path = marshmallow_fields.Str(allow_none=True, load_default=None)
