import fake_useragent
from django.conf import settings

from bot import logger
from bot.integrations import base
from bot.integrations.instagram import config
from bot.integrations.instagram.aiograpi import client as aiograpi_client
from bot.integrations.instagram.instaloader import client as instaloader_client


class InstagramClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'instagram.com', 'ddinstagram.com'}
    _CONFIG_CLASS = config.InstagramConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.InstagramConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('instagram', {}))

        if not conf.enabled:
            logger.info('Instagram integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        if conf.version == 1:
            klass = instaloader_client.InstagramClient
        else:
            klass = aiograpi_client.InstagramClient

        cls._INSTANCE = klass(
            username=conf.username,
            password=conf.password,
            session_file_path=conf.session_file_path,
            user_agent=conf.user_agent or fake_useragent.UserAgent().random,
            post_format=conf.post_format,
        )
