import io
import logging
import sys
import time
import typing

from api_24ur import downloader
from wells import utils as wells_utils

get_url_content = downloader.m3u8.get_url_content
wells_utils.logger.addHandler(logging.NullHandler())
wells_utils.logger.propagate = False


async def download_stream(  # pylint: disable=too-many-positional-arguments
    stream_url: str,
    prefix: typing.Optional[str] = None,
    tmp_dir: str = '/tmp',
    pool_size: int = 5,
    max_bitrate: int = sys.maxsize,
    sleep: float = 0.1,
) -> io.BytesIO:
    if prefix:
        # monkeypatch
        def _get_url_content(url):
            if not url.startswith('http'):
                url = prefix + url
            time.sleep(sleep)
            return get_url_content(url)

        downloader.m3u8.get_url_content = _get_url_content

    result = await downloader.Downloader(
        url=stream_url,
        download_path=tmp_dir,
        tmp_dir=tmp_dir,
        pool_size=pool_size,
        max_bitrate=max_bitrate,
    ).download_bytes()

    downloader.m3u8.get_url_content = get_url_content

    return result
