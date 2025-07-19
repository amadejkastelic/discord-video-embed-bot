import typing

import pydantic

from bot import constants


class BaseBotConfig(pydantic.BaseModel):
    """Base configuration for bot adapters."""


class BaseBot:
    VENDOR: constants.ServerVendor
    _CONFIG_CLASS = BaseBotConfig

    @classmethod
    def _load_config(cls, conf: typing.Dict) -> _CONFIG_CLASS:
        return cls._CONFIG_CLASS.model_validate(conf)

    async def run(self) -> typing.NoReturn:
        raise NotImplementedError()
