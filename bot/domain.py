import datetime
import io
import typing
from dataclasses import dataclass

from bot import constants


DEFAULT_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👀 Views: {views}
👍🏻 Likes: {likes}
📕 Description: {description}\n
"""

SERVER_INFO_FORMAT = """```yml
Tier: {tier}
Prefix: {prefix}
Integrations:
{integrations}
```
"""

INTEGRATION_INFO_FORMAT = """  - {name}: {enabled}"""


@dataclass
class Integration(object):
    uid: str
    integration: constants.Integration
    enabled: bool
    post_format: str = DEFAULT_POST_FORMAT

    def __str__(self) -> str:
        return INTEGRATION_INFO_FORMAT.format(
            name=self.integration.value.capitalize(),
            enabled=self.enabled,
        )


@dataclass
class Server(object):
    uid: str
    vendor_uid: str
    vendor: constants.ServerVendor
    tier: constants.ServerTier
    tier_valid_until: typing.Optional[datetime.datetime]
    status: constants.ServerStatus
    prefix: typing.Optional[str]
    integrations: typing.Dict[constants.Integration, Integration]
    _internal_id: typing.Optional[int]

    def __str__(self) -> str:
        return SERVER_INFO_FORMAT.format(
            tier=self.tier.name.capitalize(),
            prefix=self.prefix or 'No prefix',
            integrations='\n'.join([str(integration) for integration in self.integrations.values()]),
        )

    def can_post(self, num_posts_in_one_day: int, integration: constants.Integration) -> bool:
        if self.status != constants.ServerStatus.ACTIVE:
            return False

        if integration not in self.integrations or not self.integrations[integration].enabled:
            return False

        if self.tier_valid_until is not None and self.tier_valid_until < datetime.datetime.now():
            return num_posts_in_one_day < 3

        match (self.tier):
            case constants.ServerTier.FREE:
                return num_posts_in_one_day < 3
            case constants.ServerTier.STANDARD:
                return num_posts_in_one_day < 10
            case constants.ServerTier.PREMIUM:
                return num_posts_in_one_day < 25
            case constants.ServerTier.ULTRA:
                return True

        return False


@dataclass
class Post(object):
    url: str
    author: typing.Optional[str] = None
    description: typing.Optional[str] = None
    views: typing.Optional[int] = None
    likes: typing.Optional[int] = None
    buffer: typing.Optional[io.BytesIO] = None
    spoiler: bool = False
    created: typing.Optional[datetime.datetime] = None
    _internal_id: typing.Optional[int] = None
    _format: str = DEFAULT_POST_FORMAT

    def __str__(self) -> str:
        description = self.description or '❌'

        return self._format.format(
            url=self.url,
            author=self.author or '❌',
            created=self._date_human_format(date=self.created) if self.created else '❌',
            description=description if not self.spoiler else f'||{description}||',
            views=self._number_human_format(num=self.views) if self.views else '❌',
            likes=self._number_human_format(num=self.likes) if self.likes else '❌',
        )

    def set_format(self, format: typing.Optional[str]) -> None:
        self._format = format or DEFAULT_POST_FORMAT

    def read_buffer(self) -> typing.Optional[bytes]:
        if not self.buffer:
            return None

        self.buffer.seek(0)
        res = self.buffer.read()
        self.buffer.seek(0)
        return res

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
