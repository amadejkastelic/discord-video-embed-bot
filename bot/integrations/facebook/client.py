import ssl
import typing
from urllib import parse as urllib_parse

import aiohttp
import fake_useragent
from bs4 import BeautifulSoup as bs
from django.conf import settings

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.integrations import base
from bot.integrations.facebook import config

_API_URL = 'https://fdown.net/'
_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://fdown.net/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Alt-Used': 'fdown.net',
    'Host': 'fdown.net',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


class FacebookClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'facebook.com', 'fb.watch'}
    _CONFIG_CLASS = config.FacebookConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.FacebookConfig = cls._load_config(settings.INTEGRATION_CONFIGURATION.get('facebook', {}))

        if not conf.enabled:
            logger.info('Facebook integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        ssl_context = None
        if conf.tls1_2:
            ssl_context = ssl.create_default_context()
            ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')

        cls._INSTANCE = FacebookClient(headers=conf.headers or {}, ssl_context=ssl_context)


class FacebookClient(base.BaseClient):
    INTEGRATION = constants.Integration.FACEBOOK

    def _get_headers(self) -> typing.Dict[str, str]:
        return self.headers | {'User-Agent': fake_useragent.UserAgent().random}

    def __init__(
        self,
        headers: typing.Dict[str, str],
        ssl_context: typing.Optional[ssl.SSLContext] = None,
    ) -> None:
        super().__init__()
        self.headers = _HEADERS | (headers or {})
        self.connector = aiohttp.TCPConnector(ssl=ssl_context or True)

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        if '/watch' in url.split('?')[0] and 'v=' in url:
            return self.INTEGRATION, urllib_parse.parse_qs(urllib_parse.urlparse(url).query)['v'][0], None

        return self.INTEGRATION, url.strip('/').split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        async with aiohttp.ClientSession(
            connector=self.connector,
            headers=self._get_headers(),
            cookie_jar=aiohttp.CookieJar(unsafe=True),
        ) as session:
            # Set cookies
            async with session.get(_API_URL) as response:
                pass

            async with session.post(_API_URL + 'download.php', data=aiohttp.FormData(fields={"URLz": url})) as response:
                if response.status != 200:
                    logger.debug('Failed to fetch URL', url=url, status=response.status, response=response)
                    raise exceptions.IntegrationError(f'Failed to fetch URL: {url}')

                response_data = await response.text()

        logger.debug('Response data', url=url, response=response_data)

        post = domain.Post(url=url)

        soup = bs(response_data, 'html.parser')
        stream = soup.find('a', id='hdlink') or soup.find('a', id='sdlink')
        if stream:
            post.buffer = await self._download(url=stream['href'])

        return post

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        raise exceptions.NotSupportedError('get_comments')
