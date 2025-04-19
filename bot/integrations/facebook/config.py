import typing

from bot.integrations import base


class FacebookConfig(base.BaseClientConfig):
    cookies_file_path: typing.Optional[str] = None
    headers: typing.Optional[typing.Dict[str, str]] = None
    tls1_2: bool = False
