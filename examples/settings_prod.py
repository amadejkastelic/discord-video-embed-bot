# flake8: noqa
from conf.settings_base import *

DEBUG = False
ALLOWED_HOSTS = ['*']

LOGGING['handlers'].update(
    {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/embed_bot.log',
            'formatter': 'simple',
        }
    }
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'embed_bot',
        'USER': 'bot',
        'PASSWORD': 'bot',
        'HOST': 'db',
        'PORT': 5432,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': [
            'cache:11211',
        ],
    }
}
