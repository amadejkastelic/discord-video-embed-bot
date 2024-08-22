import typing

import pydantic


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='ignore')


class User(BaseModel):
    profile_pic_url: typing.Optional[str]
    username: typing.Optional[str]
    pk: typing.Optional[str]
    is_verified: typing.Optional[bool]
    id: typing.Optional[str]
    text_post_app_is_private: typing.Optional[bool]


class Candidate(BaseModel):
    height: typing.Optional[int]
    url: typing.Optional[str]
    width: typing.Optional[int]


class ImageVersions2(BaseModel):
    candidates: typing.Optional[typing.List[Candidate]]


class VideoVersion(BaseModel):
    type: typing.Optional[int]
    url: typing.Optional[str]


class Caption(BaseModel):
    text: typing.Optional[str]


class Post(BaseModel):
    user: typing.Optional[User]
    accessibility_caption: typing.Optional[str]
    image_versions2: typing.Optional[ImageVersions2]
    original_width: typing.Optional[int]
    original_height: typing.Optional[int]
    code: typing.Optional[str]
    video_versions: typing.Optional[typing.List[VideoVersion]]
    carousel_media: typing.Optional[str]
    pk: typing.Optional[str]
    id: typing.Optional[str]
    media_type: typing.Optional[int]
    has_audio: typing.Optional[bool]
    audio: typing.Optional[str]
    taken_at: typing.Optional[int]
    caption: typing.Optional[Caption]
    like_count: typing.Optional[int]


class ThreadItem(BaseModel):
    post: typing.Optional[Post]
    line_type: typing.Optional[str]


class Node(BaseModel):
    thread_items: typing.Optional[typing.List[ThreadItem]]
    id: typing.Optional[str]


class Edge(BaseModel):
    node: typing.Optional[Node]
    cursor: typing.Optional[str]


class Data1(BaseModel):
    edges: typing.List[Edge]


class Data(BaseModel):
    data: Data1


class Thread(BaseModel):
    data: Data
