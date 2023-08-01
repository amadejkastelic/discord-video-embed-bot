# discord-video-embed-bot
A Discord bot that automatically embeds messages containing a video link of a supported platform.

![image](https://github.com/amadejkastelic/discord-video-embed-bot/assets/26391003/bada7a36-db0d-44ba-89ee-afe4f79ad7d3)


## Supported platforms
- Instagram ✅
- Facebook ✅
- Tiktok ✅

## How to run
- Build the docker image: `docker build . -t video-embed-bot`
- Run it with your discord api key: `docker run -e DISCORD_API_KEY=<api_key> video-embed-bot`
- Facebook requires you to provide cookies. Download them in your browser using [an extension](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) while you're logged in and place them to the root of this project as `cookies.txt`.
