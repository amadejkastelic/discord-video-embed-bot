import datetime
import logging
import time
import typing

from django import db
from django.core.management import base

from bot import models
from bot.common import utils


class Command(base.BaseCommand):
    help = 'Purges posts older than timestamp'

    def add_arguments(self, parser: base.CommandParser) -> None:
        parser.add_argument(
            '--older-than',
            default='1d',
            action='store',
            type=str,
            help='Age of records to delete',
        )
        parser.add_argument(
            '--batch-size',
            default=10,
            action='store',
            type=int,
            help='How many records to delete at once',
        )
        parser.add_argument(
            '--sleep',
            default=60 * 60 * 1,  # 1h
            action='store',
            type=float,
            help='How long to sleep after each batch',
        )

    def handle(self, *args: typing.Any, **options: typing.Any) -> typing.NoReturn:
        logging.info('Running purge posts command')

        older_than = self._parse_older_than(options.get('older_than', '1d'))
        batch_size = options.get('batch_size', 10)
        sleep = options.get('sleep', 60 * 60 * 1)

        while True:
            try:
                num_deleted, _ = models.Post.objects.filter(
                    pk__in=list(
                        models.Post.objects.filter(created__lt=older_than).values_list('pk', flat=True)[:batch_size]
                    )
                ).delete()
            except db.OperationalError as e:
                logging.warning(f'DB Connection expired, reconnecting... {str(e)}')
                utils.recover_from_db_error()
                time.sleep(1)
                continue

            logging.info(f'Deleted {num_deleted} expired posts')

            time.sleep(sleep)

    @staticmethod
    def _parse_older_than(older_than: str) -> typing.Optional[datetime.datetime]:
        now = datetime.datetime.now()

        num, unit = int(older_than[:-1]), older_than[-1]
        match (unit):
            case 'y':
                return now - datetime.timedelta(days=365 * num)
            case 'm':
                return now - datetime.timedelta(days=30 * num)
            case 'w':
                return now - datetime.timedelta(days=7 * num)
            case 'd':
                return now - datetime.timedelta(days=num)
            case 'h':
                return now - datetime.timedelta(hours=num)
            case 'M':
                return now - datetime.timedelta(minutes=num)
            case 's':
                return now - datetime.timedelta(seconds=num)

        return now - datetime.timedelta(days=1)
