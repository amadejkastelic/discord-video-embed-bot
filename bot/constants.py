import enum


class ServerVendor(enum.Enum):
    DISCORD = 'discord'


class ServerTier(enum.Enum):
    FREE = 1
    STANDARD = 2
    PREMIUM = 3
    ULTRA = 4

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def from_string(s: str) -> 'ServerTier':
        try:
            return ServerTier[s]
        except KeyError as e:
            raise ValueError() from e


class ServerStatus(enum.Enum):
    ACTIVE = 1
    INACTIVE = 2
    BLOCKED = 3


class Integration(enum.Enum):
    INSTAGRAM = 'instagram'
    FACEBOOK = 'facebook'
    TIKTOK = 'tiktok'
    REDDIT = 'reddit'
    THREADS = 'threads'
    TWITCH = 'twitch'
    TWITTER = 'twitter'
    YOUTUBE = 'youtube'
