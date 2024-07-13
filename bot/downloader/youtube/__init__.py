import re

from pytube import cipher
from pytube.innertube import _default_clients


# Age restriction bypass - https://stackoverflow.com/a/78267693/10428848
_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]


# https://github.com/pytube/pytube/issues/1954#issuecomment-2218287594
def patched_get_throttling_function_name(js: str) -> str:
    function_patterns = [
        # https://github.com/ytdl-org/youtube-dl/issues/29326#issuecomment-865985377
        # https://github.com/yt-dlp/yt-dlp/commit/48416bc4a8f1d5ff07d5977659cb8ece7640dcd8
        # var Bpa = [iha];
        # ...
        # a.C && (b = a.get("n")) && (b = Bpa[0](b), a.set("n", b),
        # Bpa.length || iha("")) }};
        # In the above case, `iha` is the relevant function name
        r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)',
        r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
        r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)',
    ]
    for pattern in function_patterns:
        regex = re.compile(pattern)
        function_match = regex.search(js)
        if function_match:
            if len(function_match.groups()) == 1:
                return function_match.group(1)
            idx = function_match.group(2)
            if idx:
                idx = idx.strip("[]")
                array = re.search(r'var {nfunc}\s*=\s*(\[.+?\]);'.format(nfunc=re.escape(function_match.group(1))), js)
                if array:
                    array = array.group(1).strip("[]").split(",")
                    array = [x.strip() for x in array]
                    return array[int(idx)]

    raise Exception("get_throttling_function_name")


cipher.get_throttling_function_name = patched_get_throttling_function_name
