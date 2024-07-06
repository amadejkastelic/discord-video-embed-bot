import datetime
import typing
from dataclasses import dataclass

from bot import constants


@dataclass
class ServerConfig(object):
    tier: constants.ServerTier
    tier_valid_until: typing.Optional[datetime.datetime]
    prefix: typing.Optional[str]
    post_format: typing.Optional[str]
