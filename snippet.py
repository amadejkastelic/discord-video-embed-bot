import json

from bot.downloader.threads import client

c = client.ThreadsClientSingleton.get_instance()

print(c._get_thread('C-9VjLyu2Sy'))
