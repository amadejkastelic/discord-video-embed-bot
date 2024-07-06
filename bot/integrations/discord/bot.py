import logging
import typing

import discord
from django.conf import settings

from bot.integrations import base
from bot.integrations.discord import client


class DiscordBot(base.BaseBot):
    def __init__(self) -> None:
        super().__init__()

        self.config = self._load_config(settings.BOT_CONFIGURATION.get('discord', {}))

        intents = discord.Intents.default()
        intents.message_content = True

        self.client = client.DiscordClient(intents=intents)

    async def run(self) -> typing.NoReturn:
        if self.config.enabled and self.config.api_token:
            await self.client.start(token=self.config.api_token)
        else:
            logging.info('Discord bot not enabled or missing API token')
