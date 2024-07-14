import typing
from dataclasses import dataclass


@dataclass
class User:
    id: str
    username: str


@dataclass
class Server:
    id: str = None
    name: str = None
    owner: bool = False


@dataclass
class Identity:
    user: User
    servers: typing.List[Server]
