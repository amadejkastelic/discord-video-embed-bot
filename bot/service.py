import datetime
import typing

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot import repository
from bot.downloader import registry


def should_handle_url(url: str) -> bool:
    return registry.should_handle(url)


def get_server_info(
    server_vendor: constants.ServerVendor,
    server_uid: str,
) -> typing.Optional[str]:
    server = repository.get_server(vendor=server_vendor, vendor_uid=server_uid)
    return str(server) if server else None


def change_server_member_banned_status(
    server_vendor: constants.ServerVendor,
    server_uid: str,
    member_uid: str,
    banned: bool,
) -> None:
    repository.change_server_member_banned_status(
        server_vendor=server_vendor,
        server_uid=server_uid,
        member_uid=member_uid,
        banned=banned,
    )


def get_post_format(
    server_vendor: constants.ServerVendor,
    server_uid: str,
    integration: constants.Integration,
) -> str:
    return repository.get_post_format(
        vendor=server_vendor,
        vendor_uid=server_uid,
        integration=integration,
    )


async def get_post(  # noqa: C901
    url: str,
    server_vendor: constants.ServerVendor,
    server_uid: str,
    author_uid: str,
) -> typing.Optional[domain.Post]:
    try:
        client = registry.get_instance(url)
    except ValueError as e:
        logger.warning('No strategy for url', url=url, error=str(e))
        return None

    if not client:
        logger.warning('Integration for url not enabled or client init failure', url=url)
        return None

    integration, integration_uid, integration_index = await client.get_integration_data(url=url)

    # Check if server is throttled and allowed to post
    server = repository.get_server(
        vendor=server_vendor,
        vendor_uid=server_uid,
    )
    if not server:
        logger.info(
            'Server not configured, creating a default config',
            server_vendor_uid=server_uid,
            server_vendor=server_vendor.value,
        )
        server = repository.create_server(vendor=server_vendor, vendor_uid=server_uid)

    if not server._internal_id:
        logger.error('Internal id for server not set')
        raise exceptions.BotError('Internal server error')

    num_posts_in_server = repository.get_number_of_posts_in_server_from_datetime(
        server_id=server._internal_id,
        from_datetime=datetime.datetime.now() - datetime.timedelta(days=1),
    )

    if not server.can_post(num_posts_in_one_day=num_posts_in_server, integration=integration):
        logger.warning(
            'Server is not allowed to post',
            server_vendor=server_vendor.value,
            server_vendor_uid=server_uid,
            server_tier=server.tier.name,
        )
        raise exceptions.NotAllowedError('Upgrade your tier')

    # Check if user is banned
    if repository.is_member_banned_from_server(
        server_vendor=server_vendor,
        server_uid=server_uid,
        member_uid=author_uid,
    ):
        logger.warning(
            'User banned from server',
            user=author_uid,
            server_vendor=server_vendor.value,
            server_vendor_uid=server_uid,
        )
        raise exceptions.NotAllowedError('User banned')

    # Check if post stored in DB already
    post = repository.get_post(
        url=url,
        integration=integration,
        integration_uid=integration_uid,
        integration_index=integration_index,
    )
    # Else fetch it from 3rd party
    if not post:
        try:
            post = await client.get_post(url)
        except Exception as e:
            logger.error('Failed downloading', url=url, error=str(e))
            raise e
    else:
        logger.debug('Post already in DB, not downloading again...', url=url)

    # Set formatting
    post.set_format(server.integrations[integration].post_format)

    repository.save_server_post(
        server_vendor=server_vendor,
        server_uid=server_uid,
        author_uid=author_uid,
        post=post,
        integration=integration,
        integration_uid=integration_uid,
        integration_index=integration_index,
    )

    return post
