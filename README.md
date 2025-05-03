# discord-video-embed-bot
A Discord bot that automatically embeds media and metadata of messages containing a link of a supported platform.

![image](https://github.com/amadejkastelic/discord-video-embed-bot/assets/26391003/bada7a36-db0d-44ba-89ee-afe4f79ad7d3)


## Supported platforms
- Instagram ✅
- Facebook ⚠️ - flaky
- Tiktok ✅
- Reddit ✅
- Twitter ✅
- Youtube Shorts ✅
- Twitch Clips ✅
- Threads ✅
- 24ur.com ✅
- 4chan ✅
- Linkedin ⚠️ - flaky
- Bluesky ✅
- Truth Social ✅

## Configuration

You first need to configure settings. There are two possible ways of running this app:
- [Standalone mode](conf/settings_base_standalone.py) - no database and cache
- [Database mode](conf/settings_base.py)

You need to create your own settings by in the project root by running:
```bash
# Standalone mode
make init-standalone
# with DB
make init
```

Now you can edit the settings.py in project root. Each of the currently supported integration can be configured independently. All possible options are listed in [_settings_app.py](conf/_settings_app.py).

## Building

You can build and load the docker image by running:
```bash
nix build .#docker
docker load < result
```

## Running

### Nix

```bash
nix develop
python manage.py discord_bot
```

### Without Nix

```bash
uv sync
python manage.py discord_bot
```

### Docker

If you don't want to build the image yourself, you can pull a pre-built image (available versions are listed [here](https://github.com/amadejkastelic/discord-video-embed-bot/pkgs/container/discord-video-embed-bot)):
```bash
docker pull ghcr.io/amadejkastelic/discord-video-embed-bot:latest
```

You can run the container with the following command (make sure to mount settings):
```bash
docker run --network=host --rm -v $(pwd)/settings.py:/app/settings.py discord-video-embed-bot discord_bot
```

Example docker compose files are available under [examples](examples).
