import json
import sys

from bot.integrations.threads import client

c = client.ThreadsClientSingleton.get_instance()

if len(sys.argv) == 1:
    print('Please specify thread url and optionally a file name')
    exit(1)
elif len(sys.argv) == 2:
    url = sys.argv[1]
    out_file = 'thread.json'
else:
    url = sys.argv[1]
    out_file = sys.argv[2]

with open(out_file, '+w') as f:
    url_id = url.strip('/').split('?')[0].split('/')[-1]
    f.write(json.dumps(c._get_thread_raw(url_id=url_id, api_token=c._get_threads_api_token()), indent=2))
