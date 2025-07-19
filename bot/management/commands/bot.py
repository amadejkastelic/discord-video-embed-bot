import asyncio
import typing

from django import db
from django.core.management import base

from bot import constants
from bot import logger
from bot.adapters.discord import bot as discord_bot
from bot.adapters.terminal import bot as terminal_bot
from bot.common import utils

BOT_ADAPTERS = {
    constants.ServerVendor.DISCORD: discord_bot.DiscordBot,
    constants.ServerVendor.TERMINAL: terminal_bot.TerminalBot,
}


class Command(base.BaseCommand):
    help = 'Runs bot with specified adapter (discord or terminal)'

    def add_arguments(self, parser):
        parser.add_argument(
            'type',
            type=str,
            choices=[vendor.value for vendor in constants.ServerVendor],
            help='Bot type to run (discord or terminal)',
        )

    def handle(self, *args: typing.Any, **options: typing.Any) -> typing.NoReturn:
        server_vendor = constants.ServerVendor(options['type'])
        logger.info('Running bot command', type=server_vendor.value)

        # Get the appropriate bot class from the mapping
        bot_class = BOT_ADAPTERS.get(server_vendor)
        if not bot_class:
            raise ValueError(f'Unsupported adapter type: {server_vendor}')

        bot_instance = bot_class()

        while True:
            try:
                asyncio.run(bot_instance.run())
            except db.OperationalError as e:
                logger.warning('DB Connection expired, reconnecting', error=str(e))
                utils.recover_from_db_error(e)
