import datetime
import typing

from django.conf import settings
from playwright.async_api import async_playwright

from bot import constants
from bot import domain
from bot import logger
from bot.common import utils
from bot.integrations import base
from bot.integrations.linkedin import config


class LinkedinClientSingleton(base.BaseClientSingleton):
    DOMAINS = ['linkedin.com/posts', 'linkedin.com/feed']
    _CONFIG_SCHEMA = config.LinkedinConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.LinkedinConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('linkedin', {}))

        if not conf.enabled:
            logger.info('Linkedin integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = LinkedinClient()


class LinkedinClient(base.BaseClient):
    INTEGRATION = constants.Integration.LINKEDIN

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        id_part = url.strip('/').split('?')[0].split('/')[-1]
        if ':' in id_part:
            return self.INTEGRATION, id_part.split(':')[-1], None
        return self.INTEGRATION, id_part.split('-')[-2], None

    async def get_post(self, url: str) -> domain.Post:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            page = await context.new_page()
            await page.goto(url)

            author = await page.locator('[data-tracking-control-name="public_post_feed-actor-name"]').first.inner_text()
            description = await page.locator('[data-test-id="main-feed-activity-card__commentary"]').first.inner_text()
            likes_text = await page.locator('[data-test-id="social-actions__reaction-count"]').first.inner_text()
            likes = int(likes_text.replace(',', '').replace('.', '') or 0)
            relative_time = (await page.locator('time').first.inner_text()).split()[0]
            author_pfp = await page.locator(
                '[data-tracking-control-name="public_post_feed-actor-image"] img'
            ).first.get_attribute('src')

            post = domain.Post(
                url=url,
                author=author.strip(),
                description=description.strip(),
                likes=likes,
                created=datetime.datetime.now() - utils.parse_relative_time(relative_time),
            )

            video_locator = page.locator('meta[property="og:video"]')
            video_count = await video_locator.count()
            media_url = await video_locator.get_attribute('content') if video_count > 0 else None
            if not media_url:
                image_locator = page.locator('meta[property="og:image"]')
                image_count = await image_locator.count()
                media_url = await image_locator.get_attribute('content') if image_count > 0 else None

            if media_url and 'static' not in media_url:
                post.buffer = await self._download(media_url)
            elif author_pfp:
                post.buffer = await self._download(author_pfp)

            await browser.close()
            return post
