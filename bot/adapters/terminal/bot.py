import json
import os
import sys
import typing
from io import BytesIO

from django.conf import settings

from bot import constants
from bot import logger
from bot import service
from bot.adapters import base
from bot.adapters import mixins
from bot.adapters.terminal import config
from bot.common import utils


class TerminalBot(base.BaseBot, mixins.BotMixin):
    _CONFIG_CLASS = config.TerminalConfig
    VENDOR = constants.ServerVendor.TERMINAL

    def __init__(self) -> None:
        super().__init__()
        self.config = self._load_config(settings.BOT_CONFIGURATION.get('terminal', {}))

    async def run(self) -> typing.NoReturn:
        """Main loop for terminal bot - reads URLs from stdin and outputs JSON."""
        logger.info('Terminal bot starting - reading URLs from stdin')

        while True:
            try:
                # Read URL from stdin
                url = input('Enter URL / command: ').strip()
                if not url:
                    continue

                if url.lower() == 'exit':
                    break

                # Process the URL
                result = await self._process_url(url)

                # Output JSON result
                print(json.dumps(result, indent=2))
                sys.stdout.flush()

            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_result = {'url': url if 'url' in locals() else None, 'success': False, 'error': str(e)}
                print(json.dumps(error_result, indent=2))
                sys.stdout.flush()

    async def _process_url(self, url: str) -> typing.Dict[str, typing.Any]:
        """Process a URL and return JSON-serializable result."""

        # Check if URL is supported
        if not service.should_handle_url(url):
            return {'url': url, 'success': False, 'error': 'URL not supported by any integration'}

        try:
            # Get post data
            post = await service.get_post(
                url=url,
                server_vendor=self.VENDOR,
                server_uid='terminal',  # Fixed server ID for terminal
                author_uid='terminal_user',  # Fixed user ID for terminal
            )

            if not post:
                return {'url': url, 'success': False, 'error': 'Failed to fetch post data'}

            # Save media file if present
            media_filename = None
            if post.buffer:
                media_filename = await self._save_media_file(post.buffer, url)

            # Convert post to JSON-serializable format
            result = {
                'url': url,
                'success': True,
                'data': {
                    'author': post.author,
                    'created': post.created.isoformat() if post.created else None,
                    'description': post.description,
                    'likes': post.likes,
                    'dislikes': post.dislikes,
                    'views': post.views,
                    'spoiler': post.spoiler,
                    'media_filename': media_filename,
                    'formatted_text': str(post),
                },
            }

            return result

        except Exception as e:
            logger.exception('Failed processing URL', url=url, error=str(e))
            return {'url': url, 'success': False, 'error': str(e)}

    async def _save_media_file(self, buffer: BytesIO, url: str) -> str:
        """Save media buffer to working directory and return filename."""

        # Generate filename
        extension = utils.guess_extension_from_buffer(buffer=buffer)

        # Create a safe filename based on URL
        url_hash = str(hash(url))[-8:]  # Last 8 chars of hash
        filename = f'media_{url_hash}{extension}'

        # Ensure we don't overwrite existing files
        counter = 1
        base_filename = filename
        while os.path.exists(filename):
            name, ext = os.path.splitext(base_filename)
            filename = f'{name}_{counter}{ext}'
            counter += 1

        # Write buffer to file
        buffer.seek(0)
        with open(filename, 'wb') as f:
            f.write(buffer.read())

        logger.info('Saved media file', filename=filename)
        return filename
