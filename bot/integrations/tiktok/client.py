import asyncio
import glob
import io
import os
import typing
import urllib

import ffmpeg
import requests
from django.conf import settings
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models import user
from tiktokapipy.models import video as tiktok_video

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.integrations import base
from bot.integrations.tiktok import config

HEADERS = {'referer': 'https://www.tiktok.com/'}


class TiktokClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'tiktok.com'}
    _CONFIG_CLASS = config.TiktokConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.TiktokConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('tiktok', {}))

        if not conf.enabled:
            logger.info('Tiktok integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = TiktokClient()


class TiktokClient(base.BaseClient):
    INTEGRATION = constants.Integration.TIKTOK

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        clean_url = self._clean_url(url)
        return self.INTEGRATION, clean_url.strip('/').split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        clean_url = self._clean_url(url)

        async with AsyncTikTokAPI() as api:
            video = await api.video(clean_url)
            cookies = {cookie['name']: cookie['value'] for cookie in await api.context.cookies()}

            logger.debug('Trying to download tiktok video', url=video.video.play_addr, cookies=str(cookies))

            if video.image_post:
                buffer = await self._download_slideshow(
                    video=video,
                    cookies=cookies,
                )
            else:
                buffer = await self._download(
                    url=video.video.play_addr or video.video.download_addr,
                    cookies=cookies,
                    headers=HEADERS,
                )

            return domain.Post(
                url=url,
                author=video.author.unique_id if isinstance(video.author, user.LightUser) else video.author,
                description=video.desc,
                views=video.stats.play_count,
                likes=video.stats.digg_count,
                buffer=buffer,
                created=video.create_time.astimezone(),
            )

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        clean_url = self._clean_url(url)

        async with AsyncTikTokAPI() as api:
            video = await api.video(clean_url)

            logger.debug('Trying to fetch tiktok comments', url=url)

            return [
                domain.Comment(
                    author=comment.user.unique_id if isinstance(comment.user, user.LightUser) else comment.user,
                    likes=comment.digg_count,
                    comment=comment.text,
                )
                async for comment in video.comments.limit(n)
            ]

    async def _download_slideshow(self, video: tiktok_video.Video, cookies: typing.Dict[str, str]) -> io.BytesIO:
        vf = (
            '"scale=iw*min(1080/iw\\,1920/ih):ih*min(1080/iw\\,1920/ih),'
            'pad=1080:1920:(1080-iw)/2:(1920-ih)/2,'
            'format=yuv420p"'
        )
        directory = '/tmp'

        for i, image_data in enumerate(video.image_post.images):
            url = image_data.image_url.url_list[-1]
            urllib.request.urlretrieve(url, os.path.join(directory, f'temp_{video.id}_{i:02}.jpg'))

        read = requests.get(video.music.play_url, cookies=cookies, headers=HEADERS, timeout=base.DEFAULT_TIMEOUT)
        with open(os.path.join(directory, f'temp_{video.id}.mp3'), 'wb') as w:
            for chunk in read.iter_content(chunk_size=512):
                if chunk:
                    w.write(chunk)

        audio_duration = float(ffmpeg.probe(f'{directory}/temp_{video.id}.mp3')['format']['duration'])

        if audio_duration <= (len(video.image_post.images) * 2.5):
            command = [
                'ffmpeg',
                '-y',
                '-r 2/5',
                f'-i {directory}/temp_{video.id}_%02d.jpg',
                f'-i {directory}/temp_{video.id}.mp3',
                '-r 30',
                f'-vf {vf}',
                '-acodec copy',
                f'-t {len(video.image_post.images) * 2.5}',
                f'{directory}/temp_{video.id}.mp4',
            ]
        else:
            command = [
                'ffmpeg',
                '-y',
                '-loop 1',
                '-framerate 1/2.5',
                f'-i {directory}/temp_{video.id}_%02d.jpg',
                f'-i {directory}/temp_{video.id}.mp3',
                '-shortest',
                '-acodec aac',
                '-vcodec libx264',
                '-movflags +faststart',
                f'-vf {vf}',
                f'{directory}/temp_{video.id}.mp4',
            ]

        ffmpeg_proc = await asyncio.create_subprocess_shell(
            ' '.join(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await ffmpeg_proc.communicate()
        generated_files = glob.glob(os.path.join(directory, f'temp_{video.id}*'))

        if not os.path.exists(os.path.join(directory, f'temp_{video.id}.mp4')):
            for file in generated_files:
                os.remove(file)
            raise exceptions.IntegrationClientError('Something went wrong with piecing the slideshow together')

        with open(os.path.join(directory, f'temp_{video.id}.mp4'), 'rb') as f:
            ret = io.BytesIO(f.read())

        for file in generated_files:
            os.remove(file)

        return ret

    @staticmethod
    def _clean_url(url: str) -> str:
        clean_url = url
        if url.startswith('https://vm.') or url.startswith('https://www.tiktok.com/t/'):
            response = requests.get(
                url,
                params={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/39.0.2171.95 Safari/537.36'
                },
                timeout=base.DEFAULT_TIMEOUT,
            )
            clean_url = response.url
        return clean_url
