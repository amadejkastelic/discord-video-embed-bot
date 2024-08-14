import typing

from bot.auth.oauth2 import types
from bot.auth.oauth2.discord import constants


class DiscordUser(types.User):
    discriminator: typing.Optional[str] = None
    global_name: typing.Optional[str] = None
    avatar: typing.Optional[str] = None
    bot: bool = False
    system: bool = False
    mfa_enabled: bool = False
    banner: typing.Optional[str] = None
    accent_color: typing.Optional[int] = None
    locale: typing.Optional[str] = None
    verified: bool = False
    email: typing.Optional[str] = None
    flags: typing.Optional[int] = None
    premium_type: typing.Optional[constants.UserPremiumType] = constants.UserPremiumType.NONE
    public_flags: typing.Optional[int] = None
    avatar_decoration_data: typing.Optional[object] = None  # I don't care


class Guild(types.Server):
    icon: typing.Optional[str] = None
    permissions: typing.Optional[str] = None
    features: typing.Optional[typing.List[str]] = None
    approximate_member_count: typing.Optional[int] = None
    approximate_presence_count: typing.Optional[int] = None
