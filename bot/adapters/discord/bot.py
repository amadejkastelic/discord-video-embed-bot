import typing

import discord
from django.conf import settings

from bot import exceptions
from bot.adapters import base
from bot.adapters.discord import client


class DiscordBot(base.BaseBot):
    def __init__(self) -> None:
        super().__init__()

        self.config = self._load_config(settings.BOT_CONFIGURATION.get('discord', {}))

        intents = discord.Intents.default()
        intents.message_content = True

        self.client = client.DiscordClient(intents=intents)

    async def run(self) -> typing.NoReturn:
        if not self.config.api_token:
            raise exceptions.ConfigurationError('Discord bot missing API token')

        await self.client.start(token=self.config.api_token)
