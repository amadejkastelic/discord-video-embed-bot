import io
import typing
from dataclasses import dataclass


@dataclass
class Post:
    url: str
    author: typing.Optional[str] = None
    description: typing.Optional[str] = None
    views: typing.Optional[int] = None
    likes: typing.Optional[int] = None
    buffer: typing.Optional[io.BytesIO] = None
    spoiler: bool = False

    def __str__(self) -> str:
        return (
            '🔗 URL: {url}\n'
            '🧑🏻‍🎨 Author: {author}\n'
            '📕 Description: {description}\n'
            '👀 Views: {views}\n'
            '👍🏻 Likes: {likes}\n'
        ).format(
            url=self.url,
            author=self.author or '❌',
            description=self.description or '❌',
            views=self._human_format(self.views) if self.views else '❌',
            likes=self._human_format(self.likes) if self.likes else '❌',
        )

    def _human_format(self, num: int) -> str:
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
