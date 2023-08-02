import aiohttp
import io
import os
import urllib

import asyncio
import praw

from downloader import base
from models import post


class RedditClient(base.BaseClient):
    DOMAINS = ['reddit.com', 'redd.it']

    def __init__(self, url: str):
        super(RedditClient, self).__init__(url=url)

        self.client = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USERAGENT'),
            check_for_async=False,
        )

    async def download(self) -> post.Post:
        submission: praw.models.Submission = self.client.submission(url=self.url)

        p = post.Post(
            url=self.url,
            author=submission.author,
            description=submission.title,
            likes=submission.score,
            spoiler=submission.spoiler or submission.over_18,
        )

        print(submission.url)

        if submission.is_self:
            return p
        elif submission.url.startswith('https://i.reddit'):
            async with aiohttp.ClientSession() as session:
                async with session.get(submission.url) as resp:
                    p.buffer = io.BytesIO(await resp.read())
                    return p

        video_url = submission.media['reddit_video']['fallback_url']
        audio_url = f'{submission.url}/DASH_audio.mp4'
        print(audio_url)

        video_filename = f'temp_{submission.id}_video.mp4'
        audio_filename = f'temp_{submission.id}_audio.mp4'
        filename = f'temp_{submission.id}.mp4'

        directory = '/tmp'

        urllib.request.urlretrieve(video_url, os.path.join(directory, video_filename))
        urllib.request.urlretrieve(audio_url, os.path.join(directory, audio_filename))

        command = [
            'ffmpeg',
            f'-i {directory}/{video_filename}',
            f'-i {directory}/{audio_filename}',
            '-c:v copy',
            '-c:a copy',
            f'{directory}/{filename}',
        ]
        ffmpeg_proc = await asyncio.create_subprocess_shell(
            ' '.join(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await ffmpeg_proc.communicate()

        with open(os.path.join(directory, filename), 'rb') as f:
            p.buffer = io.BytesIO(f.read())

        for file in [audio_filename, video_filename, filename]:
            os.remove(f'{directory}/{file}')

        return p
