import datetime
import time
import typing

from django import db
from django.core.management import base

from bot import logger
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
        older_than = self._parse_older_than(options.get('older_than', '1d'))
        batch_size = options.get('batch_size', 10)
        sleep = options.get('sleep', 60 * 60 * 1)

        logger.info(
            'Running purge posts command', older_than=older_than.isoformat(), batch_size=batch_size, sleep=sleep
        )

        while True:
            try:
                num_deleted, _ = models.Post.objects.filter(
                    pk__in=list(
                        models.Post.objects.filter(created__lt=older_than).values_list('pk', flat=True)[:batch_size]
                    )
                ).delete()
            except db.OperationalError as e:
                logger.warning('DB Connection expired, reconnecting', str(e))
                utils.recover_from_db_error(e)
                time.sleep(1)
                continue

            logger.info('Deleted expired posts', count=num_deleted)

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
