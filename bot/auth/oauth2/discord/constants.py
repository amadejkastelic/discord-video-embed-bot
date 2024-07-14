import enum


class UserFlag(enum.Enum):
    STAFF = 0
    PARTNER = 1
    HYPESQUAD = 2
    BUG_HUNTER_LEVEL_1 = 3
    HYPESQUAD_ONLINE_HOUSE_1 = 6
    HYPESQUAD_ONLINE_HOUSE_2 = 7
    HYPESQUAD_ONLINE_HOUSE_3 = 8
    PREMIUM_EARLY_SUPPORTER = 9
    TEAM_PSEUDO_USER = 10
    BUG_HUNTER_LEVEL_2 = 14
    VERIFIED_BOT = 16
    VERIFIED_DEVELOPER = 17
    CERTIFIED_MODERATOR = 18
    BOT_HTTP_INTERACTIONS = 19
    ACTIVE_DEVELOPER = 22

    def value(self):
        return 1 << self._value_  # pylint: disable=no-member


class UserPremiumType(enum.Enum):
    NONE = 0
    NITRO_CLASSIC = 1
    NITRO = 2
    NITRO_BASIC = 3


class VerificationLevel(enum.Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


class GuildNsfwLevel(enum.Enum):
    DEFAULT = 0
    EXPLICIT = 1
    SAFE = 2
    AGE_RESTRICTED = 3


class ExplicitContentFilterLevel(enum.Enum):
    DISABLED = 0
    MEMBERS_WITHOUT_ROLES = 1
    ALL_MEMBERS = 2
