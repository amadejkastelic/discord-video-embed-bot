# flake8: noqa
from conf.settings_base import *

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

OAUTH2_CONFIGURATION = {
    'discord': {
        'client_id': None,
        'client_secret': None,
        'redirect_uri': None,
        'api_token': BOT_CONFIGURATION['discord']['api_token'],
    },
}

LOGGING['loggers']['bot']['level'] = 'DEBUG'
