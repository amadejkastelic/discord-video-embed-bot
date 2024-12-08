import typing

from bot.integrations import base


class BlueskyConfig(base.BaseClientConfig):
    username: typing.Optional[str] = None
    password: typing.Optional[str] = None
    base_url: typing.Optional[str] = None
