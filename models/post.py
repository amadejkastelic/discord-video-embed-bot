import datetime
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
    created: typing.Optional[datetime.datetime] = None

    def __str__(self) -> str:
        return (
            '🔗 URL: {url}\n'
            '🧑🏻‍🎨 Author: {author}\n'
            '📅 Created: {created}\n'
            '👀 Views: {views}\n'
            '👍🏻 Likes: {likes}\n'
            '📕 Description: {description}\n'
        ).format(
            url=self.url,
            author=self.author or '❌',
            created=self._date_human_format(date=self.created) if self.created else '❌',
            description=self.description or '❌',
            views=self._number_human_format(num=self.views) if self.views else '❌',
            likes=self._number_human_format(num=self.likes) if self.likes else '❌',
        )

    def _number_human_format(self, num: int) -> str:
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

    def _date_human_format(self, date: datetime.datetime) -> str:
        if date.hour == 0 and date.minute == 0:
            return date.strftime('%b %-d, %Y')

        return date.strftime('%H:%M · %b %-d, %Y')
