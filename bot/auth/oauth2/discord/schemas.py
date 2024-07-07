import typing

import marshmallow
from marshmallow import fields

from bot.auth.oauth2 import schemas
from bot.auth.oauth2.discord import constants
from bot.auth.oauth2.discord import types


class DiscordUserSchema(schemas.UserSchema):
    discriminator = fields.Str(allow_none=True, load_default=None)
    global_name = fields.Str(allow_none=True, load_default=None)
    avatar = fields.Str(allow_none=True, load_default=None)
    bot = fields.Bool(allow_none=True, load_default=False)
    system = fields.Bool(allow_none=True, load_default=False)
    mfa_enabled = fields.Bool(allow_none=True, load_default=False)
    banner = fields.Str(allow_none=True, load_default=None)
    accent_color = fields.Int(allow_none=True, load_default=None)
    locale = fields.Str(allow_none=True, load_default=None)
    verified = fields.Bool(allow_none=True, load_default=False)
    email = fields.Str(allow_none=True, load_default=None)
    flags = fields.Int(allow_none=True, load_default=None)
    premium_type = fields.Enum(
        enum=constants.UserPremiumType,
        by_value=True,
        allow_none=True,
        load_default=constants.UserPremiumType.NONE,
    )
    public_flags = fields.Int(allow_none=True, load_default=None)
    avatar_decoration_data = fields.Raw(allow_none=True, load_default=None)

    @marshmallow.post_load
    def to_obj(self, data: typing.Dict, **kwargs) -> types.DiscordUser:
        return types.DiscordUser(**data)


class GuildSchema(schemas.ServerSchema):
    icon = fields.Str(allow_none=True, load_default=None)
    permissions = fields.Str(allow_none=True, load_default=None)
    features = fields.List(fields.Str(), allow_none=True, load_default=None)
    approximate_member_count = fields.Int(allow_none=True, load_default=None)
    approximate_presence_count = fields.Int(allow_none=True, load_default=None)

    @marshmallow.post_load
    def to_obj(self, data: typing.Dict, **kwargs) -> types.Guild:
        return types.Guild(**data)
