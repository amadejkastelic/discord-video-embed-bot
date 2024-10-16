import datetime
import enum
import io
import json
import re
import typing

import pydantic
import requests

import models
import utils
from downloader import base


HEADERS = {
    'Authority': 'www.threads.net',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.threads.net',
    'Pragma': 'no-cache',
    'Sec-Fetch-Site': 'same-origin',
    'X-ASBD-ID': '129477',
    'X-IG-App-ID': '238260118697367',
    'X-FB-Friendly-Name': 'BarcelonaPostPageQuery',
}


class ThreadsClient(base.BaseClient):
    DOMAINS = ['threads.net']

    def __init__(self, url: str):
        super().__init__(url)
        self.url_id = url.strip('/').split('?')[0].split('/')[-1]

    async def get_post(self) -> models.Post:
        api_token = self._get_thread_id(self.url_id)

        thread = self._get_thread(url_id=self.url_id, api_token=api_token)
        if len(thread.data.data.edges) == 0 or len(thread.data.data.edges[0].node.thread_items) == 0:
            raise Exception('No threads found')

        thread = thread.data.data.edges[0].node.thread_items[0].post

        post = models.Post(
            url=self.url,
            author=thread.user.username,
            description=thread.caption.text,
            likes=thread.like_count,
            created=datetime.datetime.fromtimestamp(thread.taken_at),
        )

        headers = HEADERS | {'X-FB-LSD': api_token}

        media_url = None
        match thread.media_type:
            case MediaType.IMAGE:
                media_url = self._find_suitable_image_url(thread.image_versions2.candidates)
            case MediaType.VIDEO:
                media_url = thread.video_versions[0].url
            case MediaType.CAROUSEL:
                post.buffer = utils.combine_images(
                    [
                        await self._download(img.image_versions2.candidates[0].url, headers=headers)
                        for img in thread.carousel_media
                    ]
                )

        if media_url:
            with requests.get(url=media_url, timeout=(5.0, 5.0)) as resp:
                post.buffer = io.BytesIO(resp.content)

        return post

    def _get_thread_id(self, url_id: str) -> str:
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'

        thread_id = 0

        for letter in url_id:
            thread_id = (thread_id * 64) + alphabet.index(letter)

        return str(thread_id)

    def _get_thread_raw(self, url_id: str, api_token: str) -> dict:
        return requests.post(
            url='https://www.threads.net/api/graphql',
            timeout=(5.0, 5.0),
            headers=HEADERS | {'X-FB-LSD': api_token},
            data={
                'lsd': api_token,
                'variables': json.dumps(
                    {
                        'postID': self._get_thread_id(url_id),
                    },
                ),
                'doc_id': '25460088156920903',
            },
        ).json()

    def _get_thread(self, url_id: str, api_token: str) -> 'Thread':
        return Thread.model_validate(self._get_thread_raw(url_id=url_id, api_token=api_token))

    def _get_threads_api_token(self) -> str:
        response = requests.get(
            url='https://www.instagram.com/instagram',
            timeout=(5.0, 5.0),
            headers=HEADERS,
        )

        token_key_value = re.search('LSD",\\[\\],{"token":"(.*?)"},\\d+\\]', response.text).group()
        token_key_value = token_key_value.replace('LSD",[],{"token":"', '')
        token = token_key_value.split('"')[0]

        return token

    @staticmethod
    def _find_suitable_image_url(candidates: typing.List['Candidate'], max_quality: int = 1440) -> str:
        """
        Returns image url with highest quality that is below max quality
        """
        return sorted(
            list(filter(lambda candidate: candidate.width <= max_quality, candidates)),
            key=lambda candidate: candidate.width,
            reverse=True,
        )[0].url


class MediaType(enum.IntEnum):
    IMAGE = 1
    VIDEO = 2
    CAROUSEL = 8
    COMMENT = 19


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
    height: typing.Optional[int] = None
    url: typing.Optional[str]
    width: typing.Optional[int] = None


class ImageVersions2(BaseModel):
    candidates: typing.Optional[typing.List[Candidate]]


class VideoVersion(BaseModel):
    type: typing.Optional[int]
    url: typing.Optional[str]


class Caption(BaseModel):
    text: typing.Optional[str]


class CarouselMedia(BaseModel):
    image_versions2: typing.Optional[ImageVersions2]
    video_versions: typing.Optional[typing.List[VideoVersion]]
    accessibility_caption: typing.Optional[str]
    has_audio: typing.Optional[bool]
    original_height: typing.Optional[int]
    original_width: typing.Optional[int]
    pk: typing.Optional[str]
    id: typing.Optional[str]


class Post(BaseModel):
    user: typing.Optional[User]
    accessibility_caption: typing.Optional[str]
    image_versions2: typing.Optional[ImageVersions2]
    original_width: typing.Optional[int]
    original_height: typing.Optional[int]
    code: typing.Optional[str]
    video_versions: typing.Optional[typing.List[VideoVersion]]
    carousel_media: typing.Optional[typing.List[CarouselMedia]]
    pk: typing.Optional[str]
    id: typing.Optional[str]
    media_type: typing.Optional[typing.Union[MediaType, int]]
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
