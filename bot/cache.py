import enum
import typing

from django.core import cache


class CacheKey(enum.Enum):
    SERVER = 'server'
    SERVER_POST_COUNT = 'server_post_count'


NO_HIT = -1
DEFAULT_TTL = 60 * 60 * 2  # 2 hours
KEY_FORMAT = 'bot_{key}'


def set(key: CacheKey, value: typing.Any, override_timeout: typing.Optional[int] = None) -> None:
    cache.cache.set(key=KEY_FORMAT.format(key=key.value), value=value, timeout=override_timeout or DEFAULT_TTL)


def get(key: CacheKey) -> typing.Any:
    return cache.cache.get(key=KEY_FORMAT.format(key=key.value), default=NO_HIT)


def delete(key: CacheKey) -> None:
    cache.cache.delete(key=KEY_FORMAT.format(key=key.value))


def increment(key: CacheKey, delta: int = 1) -> None:
    if cache.cache.has_key(key):
        cache.cache.incr(key, delta=delta)
    else:
        cache.cache.set(key=key, value=delta)
