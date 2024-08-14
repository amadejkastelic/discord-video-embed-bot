import typing

import pydantic


class User(pydantic.BaseModel):
    id: str
    username: str


class Server(pydantic.BaseModel):
    id: str = None
    name: str = None
    owner: bool = False


class Identity(pydantic.BaseModel):
    user: User
    servers: typing.List[Server]
