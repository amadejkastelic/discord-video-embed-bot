import typing

from bot import constants

DEFAULT_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👀 Views: {views}
👍🏻 Likes: {likes} 👎🏻 Dislikes: {dislikes}
📕 Description: {description}\n
"""

BLUESKY_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👍🏻 Likes: {likes}
📕 Description: {description}\n
"""

FACEBOOK_POST_FORMAT = '🔗 URL: {url}\n'

FOUR_CHAN_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
📕 Description: {description}\n
"""

INSTAGRAM_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👍🏻 Likes: {likes}\n
"""

LINKEDIN_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👍🏻 Likes: {likes}
📕 Description: {description}\n
"""

REDDIT_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👍🏻 Likes: {likes} 👎🏻 Dislikes: {dislikes}
📕 Description: {description}\n
"""

THREADS_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👍🏻 Likes: {likes}
📕 Description: {description}\n
"""

TIKTOK_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👀 Views: {views}
👍🏻 Likes: {likes}\n
"""

TRUTH_SOCIAL_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👍🏻 Likes: {likes}
📕 Description: {description}\n
"""

TWENTY4_UR_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
📕 Description: {description}\n
"""

TWITCH_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👀 Views: {views}
📕 Description: {description}\n
"""

TWITTER_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👀 Views: {views}
👍🏻 Likes: {likes}
📕 Description: {description}\n
"""

YOUTUBE_POST_FORMAT = """🔗 URL: {url}
🧑🏻‍🎨 Author: {author}
📅 Created: {created}
👀 Views: {views}
👍🏻 Likes: {likes} 👎🏻 Dislikes: {dislikes}\n
"""


DEFAULT_INTEGRATION_POST_FMT_MAPPING = {
    constants.Integration.BLUESKY: BLUESKY_POST_FORMAT,
    constants.Integration.FACEBOOK: FACEBOOK_POST_FORMAT,
    constants.Integration.FOUR_CHAN: FOUR_CHAN_POST_FORMAT,
    constants.Integration.INSTAGRAM: INSTAGRAM_POST_FORMAT,
    constants.Integration.LINKEDIN: LINKEDIN_POST_FORMAT,
    constants.Integration.REDDIT: REDDIT_POST_FORMAT,
    constants.Integration.THREADS: THREADS_POST_FORMAT,
    constants.Integration.TIKTOK: TIKTOK_POST_FORMAT,
    constants.Integration.TRUTH_SOCIAL: TRUTH_SOCIAL_POST_FORMAT,
    constants.Integration.TWENTY4_UR: TWENTY4_UR_POST_FORMAT,
    constants.Integration.TWITCH: TWITCH_POST_FORMAT,
    constants.Integration.TWITTER: TWITTER_POST_FORMAT,
    constants.Integration.YOUTUBE: YOUTUBE_POST_FORMAT,
}


def get_or_default(
    integration: constants.Integration,
    default: typing.Optional[str] = None,
    override: typing.Optional[str] = None,
) -> str:
    """
    Get the post format for the given integration. If no post format is found, return the default post format.
    If an override is provided, return that instead.
    """
    return (
        override
        if override is not None
        else DEFAULT_INTEGRATION_POST_FMT_MAPPING.get(
            integration,
            default if default is not None else DEFAULT_POST_FORMAT,
        )
    )
