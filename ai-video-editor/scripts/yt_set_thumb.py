"""Set (or retry) the custom thumbnail of an already uploaded video.

Usage: python3 scripts/yt_set_thumb.py --channel uth-ja-sagar <videoId> <thumb.jpg>
Exit code 0 = ok. 429 "uploaded too many thumbnails recently" = YouTube's thumbnail rate limit: wait and retry later
(do not re-upload test thumbnails many times in one day). Costs 50 quota units per call.
"""
import json
import subprocess
import sys

from yt_common import access_token

a = [x for x in sys.argv[1:]]
if len(a) < 2:
    sys.exit(__doc__)
vid, img = a[0], a[1]
r = json.loads(subprocess.run(["curl", "-sS", "-X", "POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                               "-H", "Authorization: Bearer " + access_token(), "-H", "Content-Type: image/jpeg", "--data-binary", f"@{img}"],
                              capture_output=True, text=True).stdout)
if "items" in r:
    print(vid, "thumbnail ok", "(shorts version: yes)" if "shortsAspectRatio" in r["items"][0] else "")
else:
    print(vid, "thumbnail FAILED", json.dumps(r.get("error", r))[:200])
    sys.exit(1)
