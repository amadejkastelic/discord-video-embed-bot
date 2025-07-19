import typing

from django.core.management import base
from django.core.management import call_command


class Command(base.BaseCommand):
    help = 'Runs Discord bot (backwards compatibility - use "python manage.py bot discord" instead)'

    def handle(self, *_args: typing.Any, **_options: typing.Any) -> typing.NoReturn:
        call_command('bot', 'discord')
