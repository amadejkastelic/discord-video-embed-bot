import typing

from django.core.management import base

from bot import constants
from bot import service


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
            help='List of supported integrations',
        )

    def handle(self, *args: typing.Any, **options: typing.Any) -> None:
        server_vendor_uid = options.get('server_vendor_uid', '')
        server_vendor = options.get('server_vendor', constants.ServerVendor.DISCORD)
        integrations = self._parse_integrations(options.get('integrations', []))
        tier = options.get('server_tier', constants.ServerTier.FREE)

        service.provision_server(
            server_vendor=server_vendor,
            server_vendor_uid=server_vendor_uid,
            tier=tier,
            integrations=integrations,
        )

    @staticmethod
    def _parse_integrations(integrations: typing.List[str]) -> typing.List[constants.Integration]:
        if not integrations:
            return list(constants.Integration)

        return [constants.Integration(integration) for integration in integrations]
