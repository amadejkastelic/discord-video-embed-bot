from TikTokApi import TikTokApi


with TikTokApi() as api:
    vid = api.video(url='https://www.tiktok.com/t/ZGJbYX8mC/')
    print(vid.info())
