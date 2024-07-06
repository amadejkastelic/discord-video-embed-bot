import io
import typing
from dataclasses import dataclass

import aiohttp
import marshmallow
from marshmallow import fields as marshmallow_fields

from bot import domain

MISSING = -1


class BaseClient(object):
    async def get_post(self, url: str) -> domain.Post:
        raise NotImplementedError()

    async def _download(self, url: str, cookies: typing.Optional[typing.Dict[str, str]] = None, **kwargs) -> io.BytesIO:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url=url, **kwargs) as resp:
                return io.BytesIO(await resp.read())

    async def _fetch_content(self, url: str, cookies: typing.Optional[typing.Dict[str, str]] = None, **kwargs) -> str:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url=url, **kwargs) as resp:
                return await resp.text()


@dataclass
class BaseClientConfig(object):
    enabled: bool = False


class BaseClientConfigSchema(marshmallow.Schema):
    _CONFIG_CLASS: typing.Type = BaseClientConfig

    enabled = marshmallow_fields.Bool(allow_none=True, load_default=False)

    @marshmallow.post_load
    def to_obj(self, data, **kwargs) -> BaseClientConfig:
        return self._CONFIG_CLASS(**data)


class BaseClientSingleton(object):
    DOMAINS: typing.List[str] = []
    _INSTANCE: typing.Optional[BaseClient] = None
    _CONFIG_SCHEMA: BaseClientConfigSchema = BaseClientConfigSchema

    @classmethod
    def _create_instance(cls) -> None:
        raise NotImplementedError()

    @classmethod
    def _load_config(cls, conf: typing.Dict) -> BaseClientConfig:
        return cls._CONFIG_SCHEMA().load(conf)

    @classmethod
    def get_instance(cls) -> typing.Optional[BaseClient]:
        if cls._INSTANCE == MISSING:
            return None

        if cls._INSTANCE is not None:
            return cls._INSTANCE

        cls._create_instance()

        return cls._INSTANCE if cls._INSTANCE != MISSING else None
