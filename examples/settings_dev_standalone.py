# flake8: noqa
from conf.settings_base_standalone import *

# Define your settings here
INTEGRATION_CONFIGURATION.update(
    {
        'tiktok': {
            'enabled': True,
        },
    }
)

BOT_CONFIGURATION = {
    'discord': {
        'enabled': False,
        'api_token': '',
    },
}

LOGGING['loggers']['bot']['level'] = 'DEBUG'
