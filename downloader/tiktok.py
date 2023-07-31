import aiohttp
import io
import requests
import typing

from tiktokapipy.async_api import AsyncTikTokAPI

from downloader import base


class TiktokClient(base.BaseClient):
    DOMAIN = 'tiktok.com'

    async def download(self) -> io.BytesIO:
        clean_url = self._clean_url(self.url)

        async with AsyncTikTokAPI() as api:
            video = await api.video(clean_url)
            return await self._download_video(
                video.video.download_addr,
                {
                    cookie['name']: cookie['value']
                    for cookie in await api.context.cookies()
                },
                referer='https://www.tiktok.com/',
            )

    async def _download_video(
        self, url: str, cookies: typing.Dict[str, str], referer: str
    ) -> io.BytesIO:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url, headers={"referer": referer}) as resp:
                return io.BytesIO(await resp.read())

    def _clean_url(self, url: str) -> str:
        clean_url = url
        if url.startswith('https://vm.') or url.startswith('https://www.tiktok.com/t/'):
            response = requests.get(
                url,
                {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36'
                    ' (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
                },
            )
            clean_url = response.url
        return clean_url
