import typing
from dataclasses import dataclass

import marshmallow
from marshmallow import fields as marshmallow_fields

from bot import constants


@dataclass
class BaseBotConfig:
    enabled: bool = False
    api_token: typing.Optional[str] = None


class BaseBotConfigSchema(marshmallow.Schema):
    _CONFIG_CLASS: typing.Type = BaseBotConfig

    enabled = marshmallow_fields.Bool(allow_none=True, load_default=False)
    api_token = marshmallow_fields.Str(allow_none=True, load_default=None)

    @marshmallow.post_load
    def to_obj(self, data, **kwargs) -> BaseBotConfig:
        return self._CONFIG_CLASS(**data)


class BaseBot:
    VENDOR: constants.ServerVendor
    _CONFIG_SCHEMA: BaseBotConfigSchema = BaseBotConfigSchema

    def _load_config(self, conf: typing.Dict) -> BaseBotConfig:
        return self._CONFIG_SCHEMA().load(conf)

    async def run(self) -> typing.NoReturn:
        raise NotImplementedError()
