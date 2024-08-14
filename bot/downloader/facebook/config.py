import typing

from bot.downloader import base


class FacebookConfig(base.BaseClientConfig):
    cookies_file_path: typing.Optional[str] = None
