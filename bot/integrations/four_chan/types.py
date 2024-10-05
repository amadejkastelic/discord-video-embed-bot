import typing

import pydantic


class Post(pydantic.BaseModel):
    no: typing.Optional[int] = None
    sticky: typing.Optional[int] = None
    closed: typing.Optional[int] = None
    now: typing.Optional[str] = None
    name: typing.Optional[str] = None
    sub: typing.Optional[str] = None
    com: typing.Optional[str] = None
    filename: typing.Optional[str] = None
    ext: typing.Optional[str] = None
    w: typing.Optional[int] = None
    h: typing.Optional[int] = None
    tn_w: typing.Optional[int] = None
    tn_h: typing.Optional[int] = None
    tim: typing.Optional[int] = None
    time: typing.Optional[int] = None
    md5: typing.Optional[str] = None
    fsize: typing.Optional[int] = None
    resto: typing.Optional[int] = None
    capcode: typing.Optional[str] = None
    semantic_url: typing.Optional[str] = None
    replies: typing.Optional[int] = None
    images: typing.Optional[int] = None
    spoiler: typing.Optional[int] = None


class Posts(pydantic.BaseModel):
    posts: typing.List[Post] = []
