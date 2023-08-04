# discord-video-embed-bot
A Discord bot that automatically embeds messages containing a video link of a supported platform.

![image](https://github.com/amadejkastelic/discord-video-embed-bot/assets/26391003/bada7a36-db0d-44ba-89ee-afe4f79ad7d3)


## Supported platforms
- Instagram ✅
- Facebook ✅
- Tiktok ✅
- Reddit ✅
- Twitter ✅

## How to run
- Build the docker image: `docker build . -t video-embed-bot` or simply pull it from ghcr:
```bash
docker pull ghcr.io/amadejkastelic/discord-video-embed-bot:0.1.0
```
- Run it with your discord api key: `docker run -e DISCORD_API_KEY=<api_key> video-embed-bot`
- Facebook requires you to provide cookies. Download them in your browser using [an extension](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) while you're logged in and mount them to the container).
- For extended reddit support you need to create an app on reddit and add the following environment variables:
˙˙˙bash
REDDIT_API_TOKEN=<your_reddit_api_token>
REDDIT_API_SECRET=<your_reddit_api_secret>
REDDIT_USER_AGENT=<name_version_and_your_username>
```
