import enum


class ServerVendor(enum.Enum):
    DISCORD = 'discord'
    TERMINAL = 'terminal'


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
    BLUESKY = 'bluesky'
    INSTAGRAM = 'instagram'
    FACEBOOK = 'facebook'
    LINKEDIN = 'linkedin'
    TIKTOK = 'tiktok'
    REDDIT = 'reddit'
    THREADS = 'threads'
    TRUTH_SOCIAL = 't_social'
    TWENTY4_UR = '24ur'
    TWITCH = 'twitch'
    TWITTER = 'twitter'
    YOUTUBE = 'youtube'
    FOUR_CHAN = '4chan'
