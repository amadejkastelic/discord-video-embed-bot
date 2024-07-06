import enum


class ServerVendor(enum.Enum):
    DISCORD = 'discord'


class ServerTier(enum.Enum):
    FREE = 1
    STANDARD = 2
    PREMIUM = 3
    ULTRA = 4


class ServerStatus(enum.Enum):
    ACTIVE = 1
    INACTIVE = 2
    BLOCKED = 3


class Integration(enum.Enum):
    INSTAGRAM = 'instagram'
    FACEBOOK = 'facebook'
    TIKTOK = 'tiktok'
    REDDIT = 'reddit'
    TWITTER = 'twitter'
    YOUTUBE = 'youtube'
