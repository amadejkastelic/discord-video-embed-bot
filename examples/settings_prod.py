# flake8: noqa
from conf.settings_base import *

DEBUG = False

LOGGING['handlers'].update(
    {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/app.log',
            'formatter': 'simple',
        }
    }
)
