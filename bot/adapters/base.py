import typing

import pydantic

from bot import constants


class BaseBotConfig(pydantic.BaseModel):
    enabled: bool = False
    api_token: typing.Optional[str] = None


class BaseBot:
    VENDOR: constants.ServerVendor
    _CONFIG_CLASS: BaseBotConfig = BaseBotConfig

    def _load_config(self, conf: typing.Dict) -> BaseBotConfig:
        return self._CONFIG_CLASS.model_validate(conf)

    async def run(self) -> typing.NoReturn:
        raise NotImplementedError()
