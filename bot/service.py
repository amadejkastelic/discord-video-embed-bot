import datetime
import logging
import typing

from bot import constants
from bot import domain
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


async def get_post(
    url: str,
    server_vendor: constants.ServerVendor,
    server_uid: str,
    author_uid: str,
) -> typing.Optional[domain.Post]:
    try:
        client = registry.get_instance(url)
    except Exception as e:
        logging.warning(f'No strategy for url {url}. Error: {str(e)}')
        return None

    if not client:
        logging.warning(f'Integration for url {url} not enabled or client init failure')
        return

    integration, integration_uid, integration_index = await client.get_integration_data(url=url)

    # Check if server is throttled and allowed to post
    server = repository.get_server(
        vendor=server_vendor,
        vendor_uid=server_uid,
    )
    if not server:
        logging.info(f'Server {server_uid} not configured, creating a default config')
        repository.create_server(vendor=server_vendor, vendor_uid=server_uid)

    num_posts_in_server = repository.get_number_of_posts_in_server_from_datetime(
        server_id=server._internal_id,
        from_datetime=datetime.datetime.now() - datetime.timedelta(days=1),
    )

    if not server.can_post(num_posts_in_one_day=num_posts_in_server, integration=integration):
        logging.warning(f'Server {server.uid} is not allowed to post')
        raise Exception('Not allowed to post. Upgrade your tier.')

    # Check if user is banned
    if repository.is_member_banned_from_server(server_vendor=server_vendor, server_uid=server_uid, user_uid=author_uid):
        logging.warning(f'User {author_uid} banned from server [{server_vendor.value} - {server_uid}]')
        raise Exception('Not allowed to post, you were banned')

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
            logging.error(f'Failed downloading {url}: {str(e)}')
            raise e
    else:
        logging.debug(f'Post {url} already in DB, not downloading again...')

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
