import typing

import constants


class BaseBot(object):
    TYPE: constants.BotType

    def __init__(self, api_token: str) -> None:
        self.api_token = api_token

    async def run(self) -> typing.NoReturn:
        raise NotImplementedError()
