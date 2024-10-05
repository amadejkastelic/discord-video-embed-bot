import io
import typing

import aiohttp
import pydantic

from bot import constants
from bot import domain
from bot import logger

MISSING = -1
DEFAULT_TIMEOUT = (3.0, 3.0)


class BaseClient:
    INTEGRATION: constants.Integration

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        raise NotImplementedError()

    async def get_post(self, url: str) -> domain.Post:
        raise NotImplementedError()

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        raise NotImplementedError()

    async def _download(self, url: str, cookies: typing.Optional[typing.Dict[str, str]] = None, **kwargs) -> io.BytesIO:
        logger.debug('Downloading data', integration=self.INTEGRATION.value, url=url)
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url=url, **kwargs) as resp:
                return io.BytesIO(await resp.read())

    async def _fetch_content(self, url: str, cookies: typing.Optional[typing.Dict[str, str]] = None, **kwargs) -> str:
        logger.debug('Fetching content', integration=self.INTEGRATION.value, url=url)
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url=url, **kwargs) as resp:
                return await resp.text()


class BaseClientConfig(pydantic.BaseModel):
    enabled: bool = False


class BaseClientSingleton:
    DOMAINS: typing.List[str] = []
    _INSTANCE: typing.Optional[typing.Union[BaseClient, int]] = None
    _CONFIG_CLASS = BaseClientConfig

    @classmethod
    def _create_instance(cls) -> None:
        raise NotImplementedError()

    @classmethod
    def _load_config(cls, conf: object) -> _CONFIG_CLASS:
        return cls._CONFIG_CLASS.model_validate(conf)

    @classmethod
    def get_instance(cls) -> typing.Optional[BaseClient]:
        if cls._INSTANCE == MISSING:
            return None

        if cls._INSTANCE is not None:
            return cls._INSTANCE

        cls._create_instance()

        return cls._INSTANCE if cls._INSTANCE != MISSING else None
