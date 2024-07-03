import typing

import discord

from bots import base
from bots.discord import client


class DiscordBot(base.BaseBot):
    def __init__(self, api_token: str) -> None:
        super().__init__(api_token)

        intents = discord.Intents.default()
        intents.message_content = True

        self.client = client.DiscordClient(intents=intents)

    async def run(self) -> typing.NoReturn:
        await self.client.start(token=self.api_token)
