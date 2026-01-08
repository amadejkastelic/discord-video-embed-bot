# pylint: disable=unused-argument
import typing

from bot import constants
from bot import domain
from bot import exceptions
from bot import logger
from bot.domain import post_format
from bot.integrations import registry


class Service:
    def should_handle_url(self, url: str) -> bool:
        return registry.should_handle(url)

    def get_server_info(
        self,
        server_vendor: constants.ServerVendor,
        server_uid: str,
    ) -> typing.Optional[str]:
        raise NotImplementedError()

    def change_server_member_banned_status(
        self,
        server_vendor: constants.ServerVendor,
        server_uid: str,
        member_uid: str,
        banned: bool,
    ) -> None:
        raise NotImplementedError()

    def get_post_format(
        self,
        server_vendor: constants.ServerVendor,
        server_uid: str,
        integration: constants.Integration,
    ) -> str:
        raise NotImplementedError()

    async def get_post(
        self,
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

        try:
            post = await client.get_post(url)
        except Exception:
            logger.exception('Error getting post', url=url)
            return None

        post.set_format(
            post_format.get_or_default(
                integration=client.INTEGRATION,
                override=client.post_format,
            )
        )

        return post

    async def get_comments(
        self,
        url: str,
        n: int,
        server_vendor: constants.ServerVendor,
        server_uid: str,
        author_uid: str,
    ) -> typing.List[domain.Comment]:
        if n > 15:
            raise exceptions.NotAllowedError("Can't fetch more than 15 comments")

        try:
            client = registry.get_instance(url)
        except ValueError as e:
            logger.warning('No strategy for url', url=url, error=str(e))
            return None

        if not client:
            logger.warning('Integration for url not enabled or client init failure', url=url)
            return None

        try:
            return await client.get_comments(url=url, n=n)
        except Exception as e:
            logger.error('Failed downloading', url=url, num_comments=n, error=str(e))
            raise e

    def provision_server(
        self,
        server_vendor: constants.ServerVendor,
        server_vendor_uid: str,
        tier: constants.ServerTier,
        integrations: typing.List[constants.Integration],
    ) -> None:
        raise NotImplementedError()
