# TODO: Refactor
import datetime
import io
import typing
from dataclasses import dataclass

from bot import constants
from bot.common import utils
from bot.domain import post_format


DEFAULT_POST_FORMAT = post_format.DEFAULT_POST_FORMAT

DEFAULT_COMMENT_FORMAT = """🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👍🏻 Likes: {likes}
📕 Comment: {comment}\n
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
class Integration:
    uid: str
    integration: constants.Integration
    enabled: bool
    post_format: str = DEFAULT_POST_FORMAT

    def __str__(self) -> str:
        return INTEGRATION_INFO_FORMAT.format(
            name=self.integration.value.capitalize(),
            enabled='Enabled' if self.enabled else 'Disabled',
        )


@dataclass
class Server:
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
class Post:
    url: str
    author: typing.Optional[str] = None
    description: typing.Optional[str] = None
    views: typing.Optional[int] = None
    likes: typing.Optional[int] = None
    dislikes: typing.Optional[int] = None
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
            created=utils.date_to_human_format(self.created) if self.created else '❌',
            description=description if not self.spoiler else f'||{description}||',
            views=utils.number_to_human_format(self.views) if self.views is not None else '❌',
            likes=utils.number_to_human_format(self.likes) if self.likes is not None else '❌',
            dislikes=utils.number_to_human_format(self.dislikes) if self.dislikes is not None else '❌',
        )

    def set_format(self, fmt: typing.Optional[str]) -> None:
        self._format = fmt or DEFAULT_POST_FORMAT

    def read_buffer(self) -> typing.Optional[bytes]:
        if not self.buffer:
            return None

        self.buffer.seek(0)
        res = self.buffer.read()
        self.buffer.seek(0)
        return res


@dataclass
class Comment:
    author: typing.Optional[str] = None
    created: typing.Optional[datetime.datetime] = None
    likes: typing.Optional[int] = None
    comment: typing.Optional[str] = None
    spoiler: bool = False
    _format: str = DEFAULT_COMMENT_FORMAT

    def __str__(self) -> str:
        comment = self.comment or '❌'

        return self._format.format(
            author=self.author or '❌',
            created=utils.date_to_human_format(self.created) if self.created else '❌',
            likes=utils.number_to_human_format(self.likes) if self.likes else '❌',
            comment=comment if not self.spoiler else f'||{comment}||',
        )

    def set_format(self, fmt: typing.Optional[str]) -> None:
        self._format = fmt or DEFAULT_COMMENT_FORMAT


def comments_to_string(comments: typing.List[Comment]) -> str:
    return ''.join([str(comment) for comment in comments])
