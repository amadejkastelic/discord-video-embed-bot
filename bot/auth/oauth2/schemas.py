import typing

import marshmallow
from marshmallow import fields

from bot.auth.oauth2 import types


class UserSchema(marshmallow.Schema):
    id = fields.Str()
    username = fields.Str()

    @marshmallow.post_load
    def to_obj(self, data: typing.Dict[str, str], **kwargs) -> types.User:
        return types.User(**data)

    class Meta:
        unknown = marshmallow.EXCLUDE


class ServerSchema(marshmallow.Schema):
    id = fields.Str()
    name = fields.Str()
    owner = fields.Bool(allow_none=True, load_default=False)

    @marshmallow.post_load
    def to_obj(self, data: typing.Dict[str, str], **kwargs) -> types.Server:
        return types.Server(**data)

    class Meta:
        unknown = marshmallow.EXCLUDE
