import datetime
import typing

from bot import constants
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
