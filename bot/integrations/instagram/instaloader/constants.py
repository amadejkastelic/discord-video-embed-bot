import enum
import typing


class LinkType(enum.Enum):
    MEDIA = 1
    PROFILE = 2
    STORY = 3

    @classmethod
    def from_url(cls, url: str) -> typing.Self:
        if '/p/' in url or '/reel/' in url:
            return cls.MEDIA
        if '/stories/' in url or '/story/' in url:
            return cls.STORY
        return cls.PROFILE
