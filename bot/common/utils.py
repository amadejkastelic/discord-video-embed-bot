import asyncio
import io
import mimetypes
import os
import random
import re
import tempfile
import typing
from contextlib import contextmanager

import magic
from PIL import Image as pil_image
from django import db as django_db

emoji = ['😼', '😺', '😸', '😹', '😻', '🙀', '😿', '😾', '😩', '🙈', '🙉', '🙊', '😳']


def find_first_url(string: str) -> typing.Optional[str]:
    urls = re.findall(r'(https?://[^\s]+)', string)
    return urls[0] if urls else None


def guess_extension_from_buffer(buffer: io.BytesIO) -> str:
    extension = mimetypes.guess_extension(type=magic.from_buffer(buffer.read(2048), mime=True))
    buffer.seek(0)
    return extension or '.mp4'


async def resize(buffer: io.BytesIO, extension: str = 'mp4') -> io.BytesIO:
    if extension in ['.jpeg', '.png', '.jpg', '.gif']:
        return resize_image(buffer)

    with (
        tempfile.NamedTemporaryFile(suffix=extension) as input_tmp,
        tempfile.NamedTemporaryFile(suffix=extension) as output_tmp,
    ):
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


def random_emoji() -> str:
    return random.choice(emoji)


def recover_from_db_error(exc: Exception):
    if isinstance(exc, django_db.OperationalError) and exc.args[0] in (2006, 2013):
        django_db.reset_queries()
        django_db.close_old_connections()


def combine_images(image_fps: typing.List[str | io.BytesIO], gap: int = 10, quality: int = 85) -> io.BytesIO:
    images = [pil_image.open(path) for path in image_fps]
    widths, heights = zip(*(im.size for im in images))

    new_image = pil_image.new('RGBA', (sum(widths), max(heights)))
    offset = 0
    for image in images:
        new_image.paste(image, (offset, 0))
        offset += image.size[0] + gap

    image_bytes = io.BytesIO()
    new_image.save(image_bytes, format='PNG', quality=quality, optimize=True)
    image_bytes.seek(0)

    return image_bytes


def resize_image(buffer: io.BytesIO, factor: float = 0.75) -> io.BytesIO:
    if factor == 1.0:
        return buffer

    image = pil_image.open(buffer)
    width, height = image.size

    new_image = image.resize((int(width * factor), int(height * factor)), pil_image.Resampling.NEAREST)

    image_bytes = io.BytesIO()
    new_image.save(image_bytes, format='PNG', optimize=True)
    image_bytes.seek(0)

    return image_bytes


@contextmanager
def temp_open(path: str, mode: str = 'rb'):
    f = open(path, mode)  # pylint: disable=unspecified-encoding

    try:
        yield f
    finally:
        f.close()
        os.remove(path)
