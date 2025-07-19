import json
import re
import typing
from urllib.parse import urlparse

from django.conf import settings

from bot import constants
from bot import domain
from bot import logger
from bot.integrations import base
from bot.integrations.ninegag import config


class NineGagClientSingleton(base.BaseClientSingleton):
    DOMAINS = {'9gag.com'}
    _CONFIG_CLASS = config.NineGagConfig

    @classmethod
    def _create_instance(cls) -> None:
        conf: config.NineGagConfig = cls._load_config(conf=settings.INTEGRATION_CONFIGURATION.get('9gag', {}))

        if not conf.enabled:
            logger.info('9GAG integration not enabled')
            cls._INSTANCE = base.MISSING
            return

        cls._INSTANCE = NineGagClient(post_format=conf.post_format)


class NineGagClient(base.BaseClient):
    INTEGRATION = constants.Integration.NINEGAG

    def __init__(self, post_format: typing.Optional[str] = None):
        super().__init__(post_format)

    async def get_integration_data(self, url: str) -> typing.Tuple[constants.Integration, str, typing.Optional[int]]:
        post_id = self._extract_post_id(url)
        return self.INTEGRATION, post_id, None

    async def get_post(self, url: str) -> domain.Post:
        post_id = self._extract_post_id(url)

        # Try multiple approaches to get post data
        post_data = None

        # Approach 1: Try 9gag API endpoints
        api_urls = [
            f'https://9gag.com/v1/post?id={post_id}',
            f'https://9gag.com/v1/group-posts/group/default/type/hot?after={post_id}&c=1',
            f'https://comment-cdn.9gag.com/v2/post/{post_id}',
        ]

        api_headers = {
            'User-Agent': 'Mediapartners-Google',
            'Accept': 'application/json',
            'Referer': 'https://9gag.com/',
        }

        for api_url in api_urls:
            try:
                logger.info(f'Trying API endpoint: {api_url}')
                content = await self._fetch_content(api_url, headers=api_headers)
                data = json.loads(content)
                if 'data' in data:
                    if 'post' in data['data']:
                        post_data = data['data']['post']
                        logger.info('Got post data from API endpoint')
                        break
                    elif 'posts' in data['data'] and data['data']['posts']:
                        # Find our specific post
                        for post in data['data']['posts']:
                            if post.get('id') == post_id:
                                post_data = post
                                logger.info('Found post in posts array from API')
                                break
                        if post_data:
                            break
            except Exception as e:
                logger.debug(f'API endpoint failed: {e}')
                continue

        # Approach 2: Try scraping the page if API failed
        if not post_data:
            logger.info('API approaches failed, trying page scraping')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }

            page_content = await self._fetch_content(url, headers=headers)
            post_data = self._extract_post_data_from_page(page_content, post_id)

        if not post_data:
            raise ValueError(f'Could not extract post data for {url}')

        # Debug: Log the post data structure
        logger.info(f'9gag post data keys: {list(post_data.keys())}')
        if 'images' in post_data:
            logger.info(f'9gag image keys: {list(post_data["images"].keys())}')
            # Log all URLs found in images
            for key, value in post_data['images'].items():
                if isinstance(value, dict) and 'url' in value:
                    logger.info(f'9gag {key}: {value["url"]}')
        logger.info(f'9gag post type: {post_data.get("type")}')

        # Log creator info
        if 'creator' in post_data:
            logger.info(f'9gag creator keys: {list(post_data["creator"].keys())}')
            logger.info(f'9gag creator data: {post_data["creator"]}')

        # Log time fields
        time_fields = ['creationTs', 'created', 'timestamp', 'publishedAt', 'date']
        for field in time_fields:
            if field in post_data:
                logger.info(f'9gag {field}: {post_data[field]}')

        # Log view fields
        view_fields = ['views', 'viewCount', 'totalViewCount', 'impressions']
        for field in view_fields:
            if field in post_data:
                logger.info(f'9gag {field}: {post_data[field]}')

        # Log the entire post data structure (truncated for safety)
        logger.info(f'9gag full post data: {json.dumps(post_data, indent=2)[:2000]}...')

        # Extract author with fallbacks
        author = 'Unknown'
        creator = post_data.get('creator', {})
        if creator:
            author = creator.get('displayName') or creator.get('username') or creator.get('fullName') or 'Unknown'

        # Extract creation date
        created = None
        created_time = post_data.get('creationTs') or post_data.get('created') or post_data.get('timestamp')
        if created_time:
            if isinstance(created_time, (int, float)):
                # Convert timestamp to datetime
                import datetime

                created = datetime.datetime.fromtimestamp(created_time)
            elif isinstance(created_time, str):
                # Try to parse ISO date string
                try:
                    import datetime

                    created = datetime.datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                except ValueError:
                    pass

        # Extract views with fallbacks
        views = post_data.get('views') or post_data.get('viewCount') or post_data.get('totalViewCount')

        post = domain.Post(
            url=url,
            author=author,
            description=post_data.get('title', ''),
            views=views,
            likes=post_data.get('upVoteCount', 0),
            created=created,
        )

        # Get media URL and download content
        media_url = self._get_media_url(post_data)
        logger.info(f'9gag selected media URL: {media_url}')
        if media_url:
            # Use appropriate headers for downloading
            download_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://9gag.com/',
            }
            post.buffer = await self._download(media_url, headers=download_headers)

        return post

    def _extract_post_id(self, url: str) -> str:
        """Extract post ID from 9gag URL"""
        # 9gag URLs typically look like:
        # https://9gag.com/gag/aY701r0
        # https://9gag.com/gag/aY701r0/title-slug
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) >= 2 and path_parts[0] == 'gag':
            return path_parts[1]

        # Fallback: extract alphanumeric post ID from URL
        match = re.search(r'/gag/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)

        raise ValueError(f'Could not extract post ID from URL: {url}')

    def _extract_post_data_from_page(self, html_content: str, post_id: str) -> typing.Optional[dict]:
        """Extract post data from the HTML page"""
        # Look for JSON data in script tags
        patterns = [
            r'<script id="__NEXT_DATA__" type="application/json">({.+?})</script>',
            r'window\._config\s*=\s*JSON\.parse\("([^"]+)"\)',
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'__NEXT_DATA__["\']>\s*({.+?})\s*</script>',
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                logger.info(f'Found JSON data with pattern {i}')
                try:
                    json_str = match.group(1)
                    # Unescape JSON string if needed
                    if i == 1:  # window._config pattern
                        json_str = json_str.encode().decode('unicode_escape')

                    data = json.loads(json_str)
                    logger.info(
                        f'Parsed JSON successfully, top level keys: {list(data.keys()) if isinstance(data, dict) else "not a dict"}'
                    )

                    # Navigate through the data structure to find the post
                    post_data = self._find_post_in_data(data, post_id)
                    if post_data:
                        logger.info('Found post data via recursive search')
                        return post_data

                    # For Next.js, also check pageProps
                    if i == 0 and 'props' in data and 'pageProps' in data['props']:
                        logger.info('Checking Next.js pageProps')
                        props_data = self._find_post_in_data(data['props']['pageProps'], post_id)
                        if props_data:
                            return props_data

                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f'Failed to parse JSON from pattern {i}', error=str(e))
                    continue

        # Try a basic fallback approach
        return self._create_basic_post_data(html_content, post_id)

    def _find_post_in_data(self, data: dict, post_id: str) -> typing.Optional[dict]:
        """Recursively search for post data in the JSON structure"""
        if isinstance(data, dict):
            # Check if this is the post we're looking for
            if data.get('id') == post_id:
                return data

            # Recursively search in nested structures
            for value in data.values():
                result = self._find_post_in_data(value, post_id)
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = self._find_post_in_data(item, post_id)
                if result:
                    return result

        return None

    def _get_media_url(self, post_data: dict) -> typing.Optional[str]:
        """Extract media URL from post data, prioritizing videos over images"""
        images = post_data.get('images', {})
        logger.debug(f'Available image keys: {list(images.keys()) if images else "No images"}')

        # Priority 1: Video URLs (for animated posts/videos)
        video_keys = [
            'image460sv',  # Standard video format
            'image700v',  # High quality video
            'image460svwm',  # Video with watermark
            'video',  # Direct video field
        ]

        for video_key in video_keys:
            if images.get(video_key, {}).get('url'):
                logger.info(f'Found video URL with key {video_key}: {images[video_key]["url"]}')
                return images[video_key]['url']

        # Priority 2: Check if this is an animated post and look for .mp4 URLs
        if post_data.get('type') in ['Animated', 'Video']:
            # Look for any URL ending with video extensions
            for key, value in images.items():
                if isinstance(value, dict) and value.get('url'):
                    url = value['url']
                    if any(url.endswith(ext) for ext in ['.mp4', '.webm', '.mov']):
                        return url

        # Priority 3: High quality images
        image_priority = ['image700', 'imageFbThumbnail', 'image460', 'image220']
        for size in image_priority:
            if images.get(size, {}).get('url'):
                return images[size]['url']

        # Priority 4: Check for direct video/media URLs in post data
        direct_video_fields = ['videoUrl', 'video_url', 'mediaUrl', 'media_url']
        for field in direct_video_fields:
            if post_data.get(field):
                return post_data[field]

        # Fallback: any available URL (but still prefer videos)
        video_urls = []
        image_urls = []

        for key, value in images.items():
            if isinstance(value, dict) and value.get('url'):
                url = value['url']
                if any(url.endswith(ext) for ext in ['.mp4', '.webm', '.mov']):
                    video_urls.append(url)
                else:
                    image_urls.append(url)

        # Return video if available, otherwise image
        if video_urls:
            return video_urls[0]
        elif image_urls:
            return image_urls[0]

        return None

    def _create_basic_post_data(self, html_content: str, post_id: str) -> typing.Optional[dict]:
        """Create basic post data from HTML meta tags and content"""
        try:
            # Extract title from meta tags or title tag
            title_patterns = [
                r'<meta property="og:title" content="([^"]+)"',
                r'<title>([^<]+)</title>',
                r'<meta name="title" content="([^"]+)"',
            ]

            title = 'Unknown'
            for pattern in title_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    break

            # Try to extract video URL from meta tags first
            video_patterns = [
                r'<meta property="og:video:url" content="([^"]+)"',
                r'<meta property="og:video" content="([^"]+)"',
                r'<meta name="twitter:player:stream" content="([^"]+)"',
                r'<meta name="twitter:video:src" content="([^"]+)"',
            ]

            media_url = None
            for pattern in video_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    media_url = match.group(1)
                    break

            # Fallback to image if no video found
            if not media_url:
                image_patterns = [
                    r'<meta property="og:image" content="([^"]+)"',
                    r'<meta name="twitter:image" content="([^"]+)"',
                    r'<link rel="image_src" href="([^"]+)"',
                ]

                for pattern in image_patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        media_url = match.group(1)
                        break

            # Create basic post data structure
            post_data = {
                'id': post_id,
                'title': title,
                'creator': {'displayName': '9GAG User'},
                'upVoteCount': 0,
                'views': 0,
                'images': {},
            }

            if media_url:
                # Determine if it's a video or image based on URL
                if any(media_url.endswith(ext) for ext in ['.mp4', '.webm', '.mov']):
                    post_data['images']['image460sv'] = {'url': media_url}
                else:
                    post_data['images']['image700'] = {'url': media_url}

            return post_data

        except Exception as e:
            logger.error(f'Failed to create basic post data: {e}')
            return None

    async def get_comments(self, url: str, n: int = 5) -> typing.List[domain.Comment]:
        # 9gag comments would require additional API calls
        # For now, return empty list
        # TODO: Implement comment fetching
        _ = url, n  # Suppress unused parameter warnings
        return []
