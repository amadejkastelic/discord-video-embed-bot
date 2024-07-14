import enum
import typing

from django.core import cache


class Store(enum.Enum):
    SERVER = 'server'
    SERVER_POST_COUNT = 'server_post_count'
    SERVER_USER_BANNED = 'server_user_banned'
    SERVER_INTEGRATION_POST_FORMAT = 'srv_int_post_fmt'


NO_HIT = -1

_DEFAULT_TTL = 60 * 60 * 2  # 2 hours
_KEY_FORMAT = '{store}_{key}'


def _build_key(store: Store, key: str) -> str:
    return _KEY_FORMAT.format(store=store.value, key=key)


def set(  # pylint: disable=redefined-builtin
    store: Store,
    key: str,
    value: typing.Any,
    override_timeout: typing.Optional[int] = None,
) -> None:
    cache.cache.set(key=_build_key(store=store, key=key), value=value, timeout=override_timeout or _DEFAULT_TTL)


def get(store: Store, key: str) -> typing.Any:
    return cache.cache.get(
        key=_build_key(store=store, key=key),
        default=NO_HIT,
    )


def delete(store: Store, key: str) -> None:
    cache.cache.delete(key=_build_key(store=store, key=key))


def increment(store: Store, key: str, delta: int = 1) -> None:
    k = _build_key(store=store, key=key)
    if cache.cache.has_key(k):
        cache.cache.incr(key=k, delta=delta)
    else:
        cache.cache.set(key=k, value=delta)
