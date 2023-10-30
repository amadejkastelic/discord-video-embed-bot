import io
import mimetypes
import re
import typing

import magic


def find_first_url(string: str) -> typing.Optional[str]:
    urls = re.findall(r'(https?://[^\s]+)', string)
    return urls[0] if urls else None


def guess_extension_from_buffer(buffer: io.BytesIO) -> str:
    extension = mimetypes.guess_extension(type=magic.from_buffer(buffer.read(2048), mime=True))
    buffer.seek(0)
    return extension or '.mp4'
