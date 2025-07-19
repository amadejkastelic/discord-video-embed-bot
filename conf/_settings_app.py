BOT_CONFIGURATION = {
    'discord': {
        'api_token': None,
    },
    'terminal': {},
}

"""
Each integration has its own configuration.
All of them are disabled by default and need to be enabled.
You can enable them by setting the 'enabled' key to True.
You can also set a custom post_format for each integration.
"""
INTEGRATION_CONFIGURATION = {
    'tiktok': {
        'enabled': False,
    },
    'instagram': {
        'enabled': False,
        'session_file_path': None,
        'username': None,
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0',
        'password': None,
    },
    'facebook': {
        'enabled': False,
        'cookies_file_path': None,
    },
    'reddit': {
        'enabled': False,
        'client_id': None,
        'client_secret': None,
        'user_agent': None,
    },
    'youtube': {
        'enabled': False,
        'external_likes_api': False,  # Use return youtube dislikes API
    },
    'threads': {
        'enable': False,
    },
    '24ur': {
        'enable': False,
    },
    'twitter': {
        'enabled': False,
        'username': None,
        'email': None,
        'password': None,
    },
    'twitch': {
        'enabled': False,
    },
    '4chan': {
        'enabled': False,
    },
    'bluesky': {
        'enabled': False,
        'base_url': None,  # If you want some other instance
        'username': None,
        'password': None,
    },
    '9gag': {
        'enabled': False,
    },
}
