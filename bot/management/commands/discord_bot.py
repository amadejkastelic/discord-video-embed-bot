import asyncio
import logging
import typing

from django import db
from django.core.management import base

from bot.common import utils
from bot.integrations.discord import bot


class Command(base.BaseCommand):
    help = 'Runs discord bot'

    def handle(self, *args: typing.Any, **options: typing.Any) -> typing.NoReturn:
        logging.info('Running discord bot command')

        while True:
            try:
                asyncio.run(bot.DiscordBot().run())
            except db.OperationalError as e:
                logging.warning(f'DB Connection expired, reconnecting... {str(e)}')
                utils.recover_from_db_error()
