import io
import sys

from api_24ur import downloader


async def download_stream(
    stream_url: str,
    tmp_dir: str = '/tmp',
    pool_size: int = 5,
    max_bitrate: int = sys.maxsize,
) -> io.BytesIO:
    return await downloader.Downloader(
        url=stream_url,
        download_path=tmp_dir,
        tmp_dir=tmp_dir,
        pool_size=pool_size,
        max_bitrate=max_bitrate,
    ).download_bytes()
