import typing

import pydantic

from bot.auth.oauth2 import types


class BaseOAuth2Config(pydantic.BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str


class BaseOauth2Auth:
    _CONFIG_CLASS: BaseOAuth2Config = BaseOAuth2Config

    def __init__(self, config: typing.Dict[str, str]) -> None:
        self.config: BaseOAuth2Config = self._CONFIG_CLASS.model_validate(config)

    def generate_uri(self, scope: typing.List[str]) -> str:
        raise NotImplementedError()

    def exchange_code(self, code: str) -> types.Identity:
        raise NotImplementedError()
