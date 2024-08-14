import asyncio
import typing

from django import db
from django.core.management import base

from bot import logger
from bot.common import utils
from bot.integrations.discord import bot


class Command(base.BaseCommand):
    help = 'Runs discord bot'

    def handle(self, *args: typing.Any, **options: typing.Any) -> typing.NoReturn:
        logger.info('Running discord bot command')

        while True:
            try:
                asyncio.run(bot.DiscordBot().run())
            except db.OperationalError as e:
                logger.warning('DB Connection expired, reconnecting', error=str(e))
                utils.recover_from_db_error(e)
