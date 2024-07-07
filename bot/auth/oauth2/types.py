import typing
from dataclasses import dataclass


@dataclass
class User(object):
    id: str
    username: str


@dataclass
class Server(object):
    id: str = None
    name: str = None
    owner: bool = False


@dataclass
class Identity(object):
    user: User
    servers: typing.List[Server]
