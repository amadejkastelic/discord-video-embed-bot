import datetime
import io
import typing

from django.db import transaction

from bot import cache
from bot import constants
from bot import domain
from bot import exceptions
from bot import models


def create_server(
    vendor_uid: str,
    vendor: constants.ServerVendor,
    owner_id: typing.Optional[int] = None,
    tier: constants.ServerTier = constants.ServerTier.FREE,
    status: constants.ServerStatus = constants.ServerStatus.ACTIVE,
) -> domain.Server:
    with transaction.atomic():
        server = models.Server.objects.create(
            vendor_uid=vendor_uid,
            vendor=vendor,
            tier=tier,
            status=status,
            owner_id=owner_id,
        )
        # Add some default integrations to server
        integrations = models.ServerIntegration.objects.bulk_create(
            [
                models.ServerIntegration(
                    integration=constants.Integration.INSTAGRAM,
                    enabled=True,
                    server_id=server.pk,
                ),
                models.ServerIntegration(
                    integration=constants.Integration.TIKTOK,
                    enabled=True,
                    server_id=server.pk,
                ),
                models.ServerIntegration(
                    integration=constants.Integration.YOUTUBE,
                    enabled=True,
                    server_id=server.pk,
                ),
            ]
        )

    server = domain.Server(
        uid=server.uid,
        vendor_uid=server.vendor_uid,
        vendor=server.vendor,
        tier=server.tier,
        tier_valid_until=server.tier_valid_until,
        status=server.status,
        prefix=server.prefix,
        integrations={
            integration.integration: domain.Integration(
                uid=integration.uid,
                integration=integration.integration,
                enabled=integration.enabled,
            )
            for integration in integrations
        },
        _internal_id=server.pk,
    )
    cache.set(store=cache.Store.SERVER, key=f'{vendor.value}_{vendor_uid}', value=server)

    return server


def get_number_of_posts_in_server_from_datetime(
    server_id: int,
    from_datetime: datetime.datetime,
) -> int:
    post_cnt = cache.get(store=cache.Store.SERVER_POST_COUNT, key=str(server_id))
    if post_cnt != cache.NO_HIT:
        return post_cnt

    post_cnt = models.ServerPost.objects.filter(
        server_id=server_id,
        created__gt=from_datetime,
    ).count()
    cache.set(store=cache.Store.SERVER_POST_COUNT, key=str(server_id), value=post_cnt)

    return post_cnt


def update_post_format(
    vendor: constants.ServerVendor,
    vendor_uid: str,
    integration: constants.Integration,
    post_format: str,
) -> None:
    models.ServerIntegration.objects.filter(
        server__vendor=vendor,
        server__vendor_uid=vendor_uid,
        integration=integration,
    ).update(post_format=post_format)

    cache.delete(store=cache.Store.SERVER, key=f'{vendor.value}_{vendor_uid}')


def get_post_format(
    vendor: constants.ServerVendor,
    vendor_uid: str,
    integration: constants.Integration,
) -> str:
    cache_key = f'{vendor.value}_{vendor_uid}_{integration.value}'
    post_format = cache.get(
        store=cache.Store.SERVER_INTEGRATION_POST_FORMAT,
        key=cache_key,
    )
    if post_format != cache.NO_HIT:
        return post_format

    server_integration = (
        models.ServerIntegration.objects.filter(
            server__vendor=vendor,
            server__vendor_uid=vendor_uid,
            integration=integration,
        )
        .only('post_format')
        .first()
    )
    if server_integration is not None and server_integration.post_format is not None:
        post_format = server_integration.post_format
    else:
        post_format = domain.DEFAULT_POST_FORMAT

    cache.set(store=cache.Store.SERVER_INTEGRATION_POST_FORMAT, key=cache_key, value=post_format)

    return post_format


def get_server(
    vendor: constants.ServerVendor,
    vendor_uid: str,
    status: constants.ServerStatus = constants.ServerStatus.ACTIVE,
) -> typing.Optional[domain.Server]:
    server = cache.get(store=cache.Store.SERVER, key=f'{vendor.value}_{vendor_uid}')
    if server != cache.NO_HIT:
        return server

    server = (
        models.Server.objects.filter(
            vendor=vendor,
            vendor_uid=vendor_uid,
            status=status,
        )
        .prefetch_related('integrations')
        .first()
    )

    if not server:
        return None

    server = domain.Server(
        uid=server.uid,
        vendor_uid=server.vendor_uid,
        vendor=server.vendor,
        tier=server.tier,
        tier_valid_until=server.tier_valid_until,
        status=server.status,
        prefix=server.prefix,
        integrations={
            integration.integration: domain.Integration(
                uid=integration.uid,
                integration=integration.integration,
                enabled=integration.enabled,
                post_format=integration.post_format,
            )
            for integration in server.integrations.all()
        },
        _internal_id=server.pk,
    )
    cache.set(store=cache.Store.SERVER, key=f'{vendor.value}_{vendor_uid}', value=server)

    return server


def get_post(
    url: str,
    integration: constants.Integration,
    integration_uid: str,
    integration_index: typing.Optional[int] = None,
) -> typing.Optional[domain.Post]:
    post = models.Post.objects.filter(
        integration=integration,
        integration_uid=integration_uid,
        integration_index=integration_index,
    ).first()

    if post is None:
        return None

    return domain.Post(
        url=url,
        author=post.author,
        description=post.description,
        views=post.views,
        likes=post.likes,
        buffer=io.BytesIO(post.blob) if post.blob else None,
        spoiler=post.spoiler,
        created=post.posted_at,
        _internal_id=post.pk,
    )


def save_post(
    post: domain.Post,
    integration: constants.Integration,
    integration_uid: str,
    integration_index: typing.Optional[int] = None,
) -> models.Post:
    return models.Post.objects.create(
        integration=integration,
        integration_uid=integration_uid,
        integration_index=integration_index,
        author=post.author,
        description=post.description,
        views=post.views,
        likes=post.likes,
        spoiler=post.spoiler,
        posted_at=post.created,
        blob=post.read_buffer(),
    )


def save_server_post(
    server_vendor: constants.ServerVendor,
    server_uid: str,
    author_uid: str,
    post: domain.Post,
    integration: constants.Integration,
    integration_uid: str,
    integration_index: typing.Optional[int] = None,
) -> None:
    server = models.Server.objects.filter(
        vendor=server_vendor,
        vendor_uid=server_uid,
    ).first()
    if not server:
        raise exceptions.RepositoryError('Server does not exist')

    if post._internal_id is not None:
        models.ServerPost.objects.create(
            author_uid=author_uid,
            url=post.url,
            server=server,
            post_id=post._internal_id,
        )
        cache.increment(store=cache.Store.SERVER_POST_COUNT, key=str(server.pk))
        return

    with transaction.atomic():
        post_model = save_post(
            post=post,
            integration=integration,
            integration_uid=integration_uid,
            integration_index=integration_index,
        )
        models.ServerPost.objects.create(
            author_uid=author_uid,
            url=post.url,
            server=server,
            post=post_model,
        )
        cache.increment(store=cache.Store.SERVER_POST_COUNT, key=str(server.pk))


def is_member_banned_from_server(
    server_vendor: constants.ServerVendor,
    server_uid: str,
    member_uid: str,
) -> bool:
    cache_key = f'{server_vendor.value}_{server_uid}_{member_uid}'
    banned = cache.get(store=cache.Store.SERVER_USER_BANNED, key=cache_key)
    if banned != cache.NO_HIT:
        return banned is True

    server_user = models.ServerMember.objects.filter(
        server__vendor=server_vendor,
        server__vendor_uid=server_uid,
        vendor_uid=member_uid,
    ).first()

    banned = server_user.banned if server_user else False
    cache.set(store=cache.Store.SERVER_USER_BANNED, key=cache_key, value=banned)

    return banned


def change_server_member_banned_status(
    server_vendor: constants.ServerVendor,
    server_uid: str,
    member_uid: str,
    banned: bool,
) -> None:
    updated = models.ServerMember.objects.filter(
        server__vendor=server_vendor,
        server__vendor_uid=server_uid,
        vendor_uid=member_uid,
    ).update(banned=banned)

    if updated == 0:
        models.ServerMember.objects.create(
            server=models.Server.objects.get(
                vendor=server_vendor,
                vendor_uid=server_uid,
            ),
            vendor_uid=member_uid,
            banned=banned,
        )

    cache.set(
        store=cache.Store.SERVER_USER_BANNED,
        key=f'{server_vendor.value}_{server_uid}_{member_uid}',
        value=banned,
    )
