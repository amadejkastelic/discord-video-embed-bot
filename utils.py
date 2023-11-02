import asyncio
import io
import mimetypes
import re
import tempfile
import typing

import magic


def find_first_url(string: str) -> typing.Optional[str]:
    urls = re.findall(r'(https?://[^\s]+)', string)
    return urls[0] if urls else None


def guess_extension_from_buffer(buffer: io.BytesIO) -> str:
    extension = mimetypes.guess_extension(type=magic.from_buffer(buffer.read(2048), mime=True))
    buffer.seek(0)
    return extension or '.mp4'


async def resize(buffer: io.BytesIO, extension: str = 'mp4') -> io.BytesIO:
    with tempfile.NamedTemporaryFile(suffix=extension) as input_tmp, tempfile.NamedTemporaryFile(
        suffix=extension
    ) as output_tmp:
        # with open('/tmp/temp', 'w+b') as tmp:
        input_tmp.write(buffer.read())

        command = [
            'ffmpeg',
            '-y',
            f'-i {input_tmp.name}',
            '-vf "scale=trunc(iw/4)*2:trunc(ih/4)*2"',
            '-c:v',
            '-c:a',
            '-vcodec libx264',
            '-crf 28',
            f'{output_tmp.name}',
        ]
        ffmpeg_proc = await asyncio.create_subprocess_shell(
            ' '.join(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await ffmpeg_proc.communicate()

        return io.BytesIO(output_tmp.read())
