from django.core import cache

from bot import constants
from bot import repository
from bot import types


def get_server_config(vendor: constants.ServerVendor, vendor_uid: str) -> types.ServerConfig:
    model = repository.get_server(vendor=vendor, vendor_uid=vendor_uid, status=constants.ServerStatus.ACTIVE)

    return types.ServerConfig(
        tier=model.tier,
        tier_valid_until=model.tier_valid_until,
        prefix=model.prefix,
        post_format=model.post_format,
    )
