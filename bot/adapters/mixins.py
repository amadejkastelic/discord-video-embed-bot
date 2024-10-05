import typing

from bot import constants
from bot import models


class BotMixin:
    VENDOR: constants.ServerVendor

    def clear_cache(self, server_vendor_uid: str, integration: typing.Optional[constants.Integration] = None) -> int:
        kwargs = {
            'serverpost__server__vendor_uid': server_vendor_uid,
            'serverpost__server__vendor': self.VENDOR,
        }
        if integration:
            kwargs['integration'] = integration

        num_deleted, _ = models.Post.objects.filter(**kwargs).delete()

        return num_deleted
