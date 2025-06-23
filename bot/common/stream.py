import io
import os
import sys
import uuid

import fake_useragent
import yt_dlp


async def download(
    stream_url: str,
    tmp_dir: str = '/tmp',
    max_bitrate: int = sys.maxsize,
) -> io.BytesIO:
    with yt_dlp.YoutubeDL(
        {
            'format': f'best[height<=1080][tbr<={max_bitrate//1000}]/best[height<=1080]',
            'outtmpl': os.path.join(tmp_dir, f'{uuid.uuid4()}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'http_headers': {
                'User-Agent': fake_useragent.UserAgent().random,
            },
        }
    ) as ydl:
        info = ydl.extract_info(stream_url, download=True)
        filename = ydl.prepare_filename(info)

    with open(filename, 'rb') as file:
        stream_data = file.read()
    os.remove(filename)

    return io.BytesIO(stream_data)
