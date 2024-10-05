import typing

from bot.integrations import base


class RedditConfig(base.BaseClientConfig):
    client_id: typing.Optional[str] = None
    client_secret: typing.Optional[str] = None
    user_agent: typing.Optional[str] = None
