import typing
from dataclasses import dataclass

import marshmallow
from marshmallow import fields

from bot.auth.oauth2 import types


@dataclass
class BaseOauth2Config(object):
    client_id: str
    client_secret: str
    redirect_uri: str


class BaseOauth2ConfigSchema(marshmallow.Schema):
    _CONFIG_TYPE = BaseOauth2Config

    client_id = fields.Str()
    client_secret = fields.Str()
    redirect_uri = fields.Str()

    @marshmallow.post_load
    def to_obj(self, data: typing.Dict[str, str], **kwargs) -> _CONFIG_TYPE:
        return self._CONFIG_TYPE(**data)


class BaseOauth2Auth(object):
    _CONFIG_SCHEMA = BaseOauth2ConfigSchema

    def __init__(self, config: typing.Dict[str, str]) -> None:
        self.config: BaseOauth2Config = self._CONFIG_SCHEMA().load(config)

    def generate_uri(self, scope: typing.List[str]) -> str:
        raise NotImplementedError()

    def exchange_code(self, code: str) -> types.Identity:
        raise NotImplementedError()
