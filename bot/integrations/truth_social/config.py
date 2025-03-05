import typing

from bot.integrations import base


class TruthSocialConfig(base.BaseClientConfig):
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None
