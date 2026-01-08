import asyncio
import io
import os
import tempfile
import typing

import requests
from django.conf import settings

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

        cls._INSTANCE = TiktokClient(conf.post_format)


class TiktokClient(base.BaseClient):
    INTEGRATION = constants.Integration.TIKTOK

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        clean_url = self._clean_url(url)
        return self.INTEGRATION, clean_url.strip('/').split('?')[0].split('/')[-1], None

    async def get_post(self, url: str) -> domain.Post:
        clean_url = self._clean_url(url)

        # First, get metadata
        metadata_cmd = [
            'yt-dlp',
            clean_url,
            '--user-agent',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--dump-json',
            '--no-playlist',
            '--quiet',
        ]

        result = await asyncio.create_subprocess_exec(
            *metadata_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=60)

        if result.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
            logger.error('yt-dlp metadata failed', url=clean_url, error=error_msg)
            raise exceptions.IntegrationClientError(f'yt-dlp metadata failed: {error_msg}')

        import json

        info = json.loads(stdout.decode('utf-8'))

        # Then download the video
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'video.mp4')

            cmd = [
                'yt-dlp',
                clean_url,
                '--user-agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-f',
                'best',
                '-o',
                output_path,
                '--no-playlist',
                '--quiet',
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=120)

            if result.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
                logger.error('yt-dlp download failed', url=clean_url, error=error_msg)
                raise exceptions.IntegrationClientError(f'yt-dlp download failed: {error_msg}')

            if not os.path.exists(output_path):
                logger.error('No video file created', url=clean_url)
                raise exceptions.IntegrationClientError('No video downloaded')

            with open(output_path, 'rb') as f:
                buffer = io.BytesIO(f.read())

            buffer.seek(0)

            from datetime import datetime

            upload_date = info.get('upload_date')
            created_at = datetime.strptime(upload_date, '%Y%m%d') if upload_date else None

            return domain.Post(
                url=url,
                author=info.get('uploader', '') or info.get('channel', ''),
                description=info.get('description', ''),
                views=info.get('view_count', 0),
                likes=info.get('like_count', 0),
                buffer=buffer,
                created=created_at,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=120)

            if result.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
                logger.error('yt-dlp failed', url=clean_url, error=error_msg)
                raise exceptions.IntegrationClientError(f'yt-dlp failed: {error_msg}')

            if not os.path.exists(output_path):
                logger.error('No video file created', url=clean_url)
                raise exceptions.IntegrationClientError('No video downloaded')

            with open(output_path, 'rb') as f:
                buffer = io.BytesIO(f.read())

            buffer.seek(0)

            return domain.Post(
                url=url,
                author='',
                description='',
                views=0,
                likes=0,
                buffer=buffer,
                created=None,
            )

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
