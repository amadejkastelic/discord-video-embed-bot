import typing

from bot.downloader import base


class InstagramConfig(base.BaseClientConfig):
    session_file_path: typing.Optional[str] = None
    username: typing.Optional[str] = None
    user_agent: typing.Optional[str] = None
    password: typing.Optional[str] = None
    version: int = 1
