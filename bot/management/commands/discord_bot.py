import asyncio
import logging
import typing

from django.core.management import base

from bot.integrations.discord import bot


class Command(base.BaseCommand):
    help = 'Runs discord bot'

    def add_arguments(self, parser: base.CommandParser) -> None:
        return super().add_arguments(parser)

    def handle(self, *args: typing.Any, **options: typing.Any) -> None:
        logging.info('Running discord bot command')

        asyncio.run(bot.DiscordBot().run())
