import typing

from bot.integrations import base


class TwitterConfig(base.BaseClientConfig):
    email: typing.Optional[str] = None
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None
