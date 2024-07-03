import os
import typing

from bots.discord import bot


async def run_strategies() -> typing.NoReturn:
    """
    TODO: Add support for multiple strategies and move env vars to settings/config
    """
    discord_api_key = os.environ.get('DISCORD_API_TOKEN')
    if discord_api_key:
        await bot.DiscordBot(api_token=discord_api_key).run()
    else:
        raise RuntimeError('DISCORD_API_TOKEN environment variable not set, plesae set it to a valid value.')
