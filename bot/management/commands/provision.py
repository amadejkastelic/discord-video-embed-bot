import typing

from django.core.management import base

from bot import constants
from bot import logger
from bot import models


class Command(base.BaseCommand):
    help = 'Provisions data for server'

    def add_arguments(self, parser: base.CommandParser) -> None:
        parser.add_argument(
            '--server-vendor-uid', required=True, action='store', type=str, help='Unique vendor ID of the server'
        )
        parser.add_argument(
            '--server-vendor',
            default=constants.ServerVendor.DISCORD,
            action='store',
            type=constants.ServerVendor,
            help='Vendor of server to provision',
        )
        parser.add_argument(
            '--server-tier',
            default=constants.ServerTier.FREE,
            choices=list(constants.ServerTier),
            action='store',
            type=constants.ServerTier.from_string,
            help='Desired server tier',
        )
        parser.add_argument(
            '--integrations',
            nargs='*',
            default=None,
            action='store',
            type=list,
            help='List of supported integrations',
        )

    def handle(self, *args: typing.Any, **options: typing.Any) -> typing.NoReturn:
        server_vendor_uid = options.get('server_vendor_uid')
        server_vendor = options.get('server_vendor', constants.ServerVendor.DISCORD)
        integrations = self._parse_integrations(options.get('integrations', []))
        tier = options.get('server_tier', constants.ServerTier.FREE)

        logger.info(
            'Provisioning integrations for server',
            integrations=[integration.value for integration in integrations] or 'all',
            server_vendor=server_vendor.value,
            server_vendor_uid=server_vendor_uid,
        )

        server = models.Server.objects.filter(
            vendor=server_vendor,
            vendor_uid=server_vendor_uid,
        ).first()
        if not server:
            server = models.Server.objects.create(
                vendor=server_vendor,
                vendor_uid=server_vendor_uid,
                tier=tier,
            )

        models.ServerIntegration.objects.bulk_create(
            [
                models.ServerIntegration(
                    integration=integration,
                    server=server,
                    enabled=True,
                )
                for integration in integrations
            ]
        )

        logger.info('Successfully created server with integrations')

    @staticmethod
    def _parse_integrations(integrations: typing.List[str]) -> typing.List[constants.Integration]:
        if not integrations:
            return list(constants.Integration)

        return [constants.Integration(integration) for integration in integrations]
