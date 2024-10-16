import typing

from bot.integrations import base


class FacebookConfig(base.BaseClientConfig):
    cookies_file_path: typing.Optional[str] = None