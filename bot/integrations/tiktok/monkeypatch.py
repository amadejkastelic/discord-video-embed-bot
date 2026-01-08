import datetime
import io
import typing

from playwright.async_api import Page
from pydantic import ValidationError
from tiktokapipy.models.video import ImageData
from tiktokapipy.models.video import ImagePost
from tiktokapipy.models.video import ImageUrlList
from tiktokapipy.models.video import LightUser
from tiktokapipy.models.video import MusicData
from tiktokapipy.models.video import Video
from tiktokapipy.models.video import VideoData
from tiktokapipy.models.video import VideoStats

from bot import logger


class VideoPage(typing.TypedDict):
    itemInfo: dict
    itemStruct: dict


class UniversalData(typing.TypedDict):
    __DEFAULT_SCOPE__: dict


def _extract_video_url(video_data: dict) -> typing.Optional[str]:
    """Extract video URL from TikTok data."""
    play_addr = video_data.get('playAddr')
    if play_addr and isinstance(play_addr, str):
        return play_addr

    # Fallback to download_addr
    download_addr = video_data.get('downloadAddr')
    if download_addr and isinstance(download_addr, str):
        return download_addr
    return None


def _extract_author(author_data: dict) -> LightUser:
    """Extract author information."""
    unique_id = author_data.get('unique_id', '')
    display_name = author_data.get('nickname', unique_id)

    return LightUser(
        unique_id=unique_id,
        display_name=display_name,
    )


def _extract_music(music_data: dict) -> MusicData:
    """Extract music information."""
    # TikTok DOM uses camelCase
    return MusicData(
        id=music_data.get('id', 0),
        title=music_data.get('title', ''),
        play_url=music_data.get('playUrl'),
        author_name=music_data.get('authorName'),
        duration=music_data.get('duration'),
        original=music_data.get('original', False),
        album=music_data.get('album'),
        cover_large=music_data.get('coverLarge', ''),
        cover_medium=music_data.get('coverMedium', ''),
        cover_thumb=music_data.get('coverThumb', ''),
    )


def _extract_stats(stats_data: dict) -> VideoStats:
    """Extract video statistics."""
    # TikTok DOM uses camelCase: diggCount, playCount, etc.
    return VideoStats(
        digg_count=stats_data.get('diggCount', 0),
        share_count=stats_data.get('shareCount', 0),
        comment_count=stats_data.get('commentCount', 0),
        play_count=stats_data.get('playCount', 0),
        collect_count=0,
    )


def _extract_video_data(video_data: dict) -> VideoData:
    """Extract video data."""
    # TikTok DOM uses camelCase: originCover, dynamicCover, downloadAddr
    return VideoData(
        height=video_data.get('height', 0),
        width=video_data.get('width', 0),
        duration=video_data.get('duration', 0),
        ratio=video_data.get('ratio', ''),
        format=video_data.get('format'),
        bitrate=video_data.get('bitrate'),
        encoded_type=video_data.get('encodedType'),
        video_quality=video_data.get('videoQuality'),
        encode_user_tag=video_data.get('encodeUserTag'),
        codec_type=video_data.get('codecType'),
        definition=video_data.get('definition'),
        subtitle_infos=None,
        cover=video_data.get('cover', ''),
        origin_cover=video_data.get('originCover', ''),
        dynamic_cover=video_data.get('dynamicCover'),
        share_cover=None,
        reflow_cover=None,
        play_addr=_extract_video_url(video_data),
        download_addr=video_data.get('downloadAddr'),
    )


def _extract_image_post(image_post_data: dict) -> typing.Optional[ImagePost]:
    """Extract image post data (for slideshows)."""
    if not image_post_data:
        return None

    images = image_post_data.get('images', [])
    if not images:
        return None

    extracted_images = []
    for img_data in images:
        image_url_data = img_data.get('imageURL', {})
        url_list = image_url_data.get('url_list', [])

        extracted_images.append(
            ImageData(
                image_url=ImageUrlList(url_list=url_list),
                image_width=img_data.get('image_width', 0),
                image_height=img_data.get('image_height', 0),
            )
        )

    cover_data = image_post_data.get('cover', {})
    return ImagePost(
        images=extracted_images,
        cover=ImageData(
            image_url=ImageUrlList(url_list=[]),
            image_width=cover_data.get('image_width', 0),
            image_height=cover_data.get('image_height', 0),
        ),
        share_cover=None,
    )


async def _scrape_video_from_dom(page: Page, url: str, timeout: int = 60000) -> Video:
    """Scrape video data from TikTok page DOM."""
    logger.debug('Scraping video from DOM', url=url)

    try:
        await page.goto(url, timeout=timeout, wait_until='networkidle')
    except Exception as e:
        logger.error('Failed to load TikTok page', url=url, error=str(e))
        raise

    # Wait for data element to appear
    try:
        await page.wait_for_selector('#__UNIVERSAL_DATA_FOR_REHYDRATION__', state='attached', timeout=timeout)
    except Exception as e:
        logger.error('Data element not found', url=url, error=str(e))
        raise

    # Wait for video element to load
    try:
        await page.wait_for_selector('video', state='attached', timeout=timeout)
    except Exception as e:
        logger.error('Video element not found', url=url, error=str(e))
        raise

    # Extract JSON from script tag
    try:
        raw_data = await page.evaluate(
            '() => JSON.parse(document.querySelector("#__UNIVERSAL_DATA_FOR_REHYDRATION__").textContent)'
        )
    except Exception as e:
        logger.error('Failed to parse data from DOM', url=url, error=str(e))
        raise

    # Navigate TikTok's new DOM structure
    try:
        universal_data = typing.cast(UniversalData, raw_data)
        video_page = typing.cast(VideoPage, universal_data['__DEFAULT_SCOPE__']['webapp.video-detail'])
        item_struct = video_page['itemInfo']['itemStruct']
    except KeyError as e:
        logger.error('Failed to navigate TikTok DOM structure', url=url, error=str(e))
        raise

    logger.debug('Extracted TikTok data', video_id=item_struct.get('id'))

    # Extract all fields needed for Video object
    # TikTok DOM uses camelCase: createTime
    create_time = item_struct.get('createTime')
    if create_time:
        create_time_dt = datetime.datetime.fromtimestamp(int(create_time))
    else:
        create_time_dt = datetime.datetime.now()

    # Build Video object
    try:
        video = Video(
            id=item_struct.get('id', 0),
            desc=item_struct.get('desc', ''),
            author=_extract_author(item_struct.get('author', {})),
            stats=_extract_stats(item_struct.get('stats', {})),
            video=_extract_video_data(item_struct.get('video', {})),
            music=_extract_music(item_struct.get('music', {})),
            image_post=_extract_image_post(item_struct.get('image_post')),
            digged=item_struct.get('digged', False),
            item_comment_status=item_struct.get('item_comment_status', 0),
            diversification_labels=item_struct.get('diversification_labels'),
            challenges=None,
            create_time=create_time_dt,
        )
    except (ValidationError, KeyError) as e:
        logger.error('Failed to construct Video object', url=url, error=str(e))
        raise

    # Download video bytes while page is still open (using fetch API to share browser session)
    if not video.image_post and video.video.play_addr:
        try:
            logger.debug('Downloading video via fetch API')
            result = await page.evaluate(f'''
                async () => {{
                    try {{
                        const response = await fetch("{video.video.play_addr}");
                        if (!response.ok) {{
                            return {{ success: false, status: response.status, statusText: response.statusText }};
                        }}
                        const blob = await response.blob();
                        const arrayBuffer = await blob.arrayBuffer();
                        const uint8Array = new Uint8Array(arrayBuffer);
                        return {{ success: true, data: Array.from(uint8Array), size: blob.size }};
                    }} catch (e) {{
                        return {{ success: false, error: e.message }};
                    }}
                }}
            ''')

            if result.get('success'):
                setattr(video, '_video_buffer', io.BytesIO(bytes(result['data'])))
                logger.debug('Successfully downloaded video bytes', size=len(result['data']))
            else:
                logger.warning(
                    'Failed to download video bytes', error=result.get('error', f'Status: {result.get("status")}')
                )
                setattr(video, '_video_buffer', None)
        except Exception as e:
            logger.warning('Exception downloading video bytes', error=str(e))
            setattr(video, '_video_buffer', None)
    else:
        setattr(video, '_video_buffer', None)

    logger.debug('Successfully constructed Video object', video_id=video.id)
    return video


def monkeypatch_tiktok_video() -> None:
    """Monkeypatch AsyncTikTokAPI.video() to use DOM scraping."""
    from tiktokapipy import async_api

    async def patched_video(self, link_or_id: typing.Union[int, str]) -> Video:
        """Patched video method that scrapes DOM instead of using API."""
        # Convert to URL if it's just an ID
        if isinstance(link_or_id, str) and link_or_id.isdigit():
            url = f'https://www.tiktok.com/video/{link_or_id}'
        elif isinstance(link_or_id, int):
            url = f'https://www.tiktok.com/video/{link_or_id}'
        else:
            url = str(link_or_id)

        logger.debug('Using DOM scraping for TikTok video', url=url)

        # Use existing playwright context
        context = self.context

        # Create a new page and scrape
        page = await context.new_page()
        try:
            video = await _scrape_video_from_dom(page, url)
        finally:
            await page.close()

        return video

    # Apply the monkeypatch
    async_api.AsyncTikTokAPI.video = patched_video

    logger.info('Monkeypatch applied to AsyncTikTokAPI.video()')


__all__ = ['monkeypatch_tiktok_video']
