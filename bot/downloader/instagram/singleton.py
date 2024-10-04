from django.conf import settings

from bot import logger
from bot.downloader import base
from bot.downloader.instagram import config
from bot.downloader.instagram.instaloader import client as instaloader_client


class InstagramClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['instagram.com', 'ddinstagram.com']
    _CONFIG_CLASS = config.InstagramConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.InstagramConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('instagram', {}))

        if not conf.enabled:
            logger.info('Instagram integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = instaloader_client.InstagramClient(
            username=conf.username,
            session_file_path=conf.session_file_path,
            user_agent=conf.user_agent,
        )
