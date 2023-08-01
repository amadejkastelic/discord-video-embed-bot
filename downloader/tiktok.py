import aiohttp
import asyncio
import io
import glob
import os
import requests
import typing
import urllib

from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models import video

from downloader import base


class TiktokClient(base.BaseClient):
    DOMAINS = ['tiktok.com']

    async def download(self) -> io.BytesIO:
        clean_url = self._clean_url(self.url)

        async with AsyncTikTokAPI() as api:
            video = await api.video(clean_url)
            cookies = {cookie['name']: cookie['value'] for cookie in await api.context.cookies()}
            referer = 'https://www.tiktok.com/'
            if video.image_post:
                return await self._download_slideshow(
                    video=video,
                    cookies=cookies,
                    referer=referer,
                )
            return await self._download_video(
                video=video,
                cookies=cookies,
                referer=referer,
            )

    async def _download_video(self, video: video.Video, cookies: typing.Dict[str, str], referer: str) -> io.BytesIO:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(video.video.download_addr, headers={'referer': referer}) as resp:
                return io.BytesIO(await resp.read())

    async def _download_slideshow(self, video: video.Video, cookies: typing.Dict[str, str], referer: str) -> io.BytesIO:
        vf = (
            '"scale=iw*min(1080/iw\\,1920/ih):ih*min(1080/iw\\,1920/ih),'
            'pad=1080:1920:(1080-iw)/2:(1920-ih)/2,'
            'format=yuv420p"'
        )
        directory = '/tmp'

        for i, image_data in enumerate(video.image_post.images):
            url = image_data.image_url.url_list[-1]
            urllib.request.urlretrieve(url, os.path.join(directory, f'temp_{video.id}_{i:02}.jpg'))

        read = requests.get(video.music.play_url, cookies=cookies, headers={'referer': referer})
        with open(os.path.join(directory, f'temp_{video.id}.mp3'), 'wb') as w:
            for chunk in read.iter_content(chunk_size=512):
                if chunk:
                    w.write(chunk)

        command = [
            'ffmpeg',
            '-r 2/5',
            f'-i {directory}/temp_{video.id}_%02d.jpg',
            f'-i {directory}/temp_{video.id}.mp3',
            '-r 30',
            f'-vf {vf}',
            '-acodec copy',
            f'-t {len(video.image_post.images) * 2.5}',
            f'{directory}/temp_{video.id}.mp4',
            '-y',
        ]
        ffmpeg_proc = await asyncio.create_subprocess_shell(
            ' '.join(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await ffmpeg_proc.communicate()
        generated_files = glob.glob(os.path.join(directory, f'temp_{video.id}*'))

        if not os.path.exists(os.path.join(directory, f'temp_{video.id}.mp4')):
            for file in generated_files:
                os.remove(file)
            raise Exception('Something went wrong with piecing the slideshow together')

        with open(os.path.join(directory, f'temp_{video.id}.mp4'), 'rb') as f:
            ret = io.BytesIO(f.read())

        for file in generated_files:
            os.remove(file)

        return ret

    def _clean_url(self, url: str) -> str:
        clean_url = url
        if url.startswith('https://vm.') or url.startswith('https://www.tiktok.com/t/'):
            response = requests.get(
                url,
                {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/39.0.2171.95 Safari/537.36'
                },
            )
            clean_url = response.url
        return clean_url
