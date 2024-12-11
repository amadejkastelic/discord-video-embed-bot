# discord-video-embed-bot

A Discord bot that automatically embeds media and metadata of messages containing a link of a supported platform.

![image](https://github.com/amadejkastelic/discord-video-embed-bot/assets/26391003/bada7a36-db0d-44ba-89ee-afe4f79ad7d3)

## Supported platforms

- Instagram ✅
- Facebook ✅
- Tiktok ✅
- Reddit ✅
- Twitter ✅
- Youtube Shorts ✅
- Threads ✅

## How to run

Build the docker image: `docker build . -t video-embed-bot` or simply pull it from ghcr:

```bash
docker pull ghcr.io/amadejkastelic/discord-video-embed-bot:<latest|tag>
```

Run it with your discord api key: `docker run -e DISCORD_API_TOKEN=<api_token> video-embed-bot`

### Facebook

Facebook requires you to provide cookies. Download them in your browser using [an extension](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) while you're logged in and mount them to the container).

### Reddit

For extended reddit support you need to [create an app on reddit](https://www.reddit.com/prefs/apps) and add the following environment variables:

```bash
REDDIT_CLIENT_ID=<your_reddit_api_token>
REDDIT_CLIENT_SECRET=<your_reddit_api_secret>
REDDIT_USER_AGENT=<name_version_and_your_username>
```

### Twitter

For better twitter support you need to add credentials:

```bash
TWITTER_USERNAME=<your_twitter_username>
TWITTER_EMAIL=<your_twitter_email>
TWITTER_PASSWORD=<your_twitter_password>
```

### Instagram

For better instagram integration that allows to view items that require login, you need to provide the instagram.sess file and instagram username environemnt variable:

```bash
INSTAGRAM_USERNAME=<your_instagram_username>
```

`instagram.sess` file should be in the working directory of your instance

You can obtain the session file by logging into Instagram in Firefox and running:

```bash
python bin/fetch_instagram_session.py
```

### Additional Options

| Env Var        | Default Value | Description                                                                                                              |
|----------------|---------------|--------------------------------------------------------------------------------------------------------------------------|
| `COMPACT_POST` | false         | If set to true, only the url and video will post instead of additional details such as description, author, created, etc |
|                |               |                                                                                                                          |
