## Django
- [x] Move to django
- [ ] Move discord bot entrypoint to a long running command

## Caching
Download all posts to fs and write path to cache
Cache:
- [x] Docker container
- [ ] Matches are made by vendor + vendor_id
- [ ] Serialized post with video path on fs
- [ ] TTL 1h (Clears fs and cache)

## Bot config
- [x] SQL Docker container
- [ ] Sql server with bot configs per guild
- [ ] FE page and django api that allows config management
- [ ] Monetization: Free (10 posts per day), Normal (5 posts per hour), Advanced (50 posts per hour)

## Server config
- [x] Prepare settings.py
- [ ] Move server config to settings.py
- [ ] Should contain all the secrets and should allow integration configuration and bot config:

```python
INTEGRATION_CONFIGURATION = {
    'tiktok': {
        'enabled': True,
    },
    'reddit': {
        'enabled': True,
        'API_KEY': 'reddit_api_key',
    },
}
BOT_CONFIGURATION = {
    'discord': {
        'enabled': True,
        'api_token': 'token',
    },
    'slack': {
        'enabled': True,
        'api_token': 'token',
    },
    'telegram': {
        'enabled': False,
    },
}
```
