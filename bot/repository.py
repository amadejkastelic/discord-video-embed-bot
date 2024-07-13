import datetime
import io
import typing

from django.db import transaction

from bot import constants
from bot import domain
from bot import models


def create_server(
    uid: str,
    bot_type: constants.ServerVendor,
    admin_id: str,
    tier: constants.ServerTier = constants.ServerTier.FREE,
    tier_valid_until: typing.Optional[datetime.datetime] = None,
    prefix: typing.Optional[str] = None,
    post_format: typing.Optional[str] = None,
) -> str:
    return models.Server.objects.create(
        uid=uid,
        bot_type=bot_type,
        admin_id=admin_id,
        tier=tier,
        tier_valid_until=tier_valid_until,
        status=constants.ServerStatus.ACTIVE,
        prefix=prefix,
        post_format=post_format,
    ).uid


def update_server(
    uid: str,
    status: constants.ServerStatus = constants.ServerStatus.ACTIVE,
    tier: constants.ServerTier = constants.ServerTier.FREE,
    tier_valid_until: typing.Optional[datetime.datetime] = None,
    prefix: typing.Optional[str] = None,
    post_format: typing.Optional[str] = None,
) -> None:
    models.Server.objects.filter(uid=uid).update(
        status=status,
        tier=tier,
        tier_valid_until=tier_valid_until,
        prefix=prefix,
        post_format=post_format,
    )


def get_server(
    vendor: constants.ServerVendor,
    vendor_uid: str,
    status: constants.ServerStatus = constants.ServerStatus.ACTIVE,
) -> typing.Optional[models.Server]:
    models.Server.objects.filter(
        vendor=vendor,
        vendor_uid=vendor_uid,
        status=status,
    ).first()


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
        raise Exception('Server does not exist?!')

    if post._internal_id is not None:
        models.ServerPost.objects.create(
            author_uid=author_uid,
            url=post.url,
            server=server,
            post_id=post._internal_id,
        )
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
