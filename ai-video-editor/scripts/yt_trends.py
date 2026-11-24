"""India's trending YouTube videos right now (real data from the YouTube Data API).

Usage: python3 scripts/yt_trends.py [--category 23] [--n 25]
Categories: 0/none = all, 23 = Comedy, 24 = Entertainment, 22 = People & Blogs, 10 = Music, 20 = Gaming.
"""
import argparse
import json
import subprocess

from yt_common import access_token


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category")
    ap.add_argument("--n", type=int, default=25)
    a = ap.parse_args()
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=IN&maxResults={a.n}"
    if a.category:
        url += f"&videoCategoryId={a.category}"
    out = subprocess.run(["curl", "-sS", url, "-H", "Authorization: Bearer " + access_token()], capture_output=True, text=True).stdout
    d = json.loads(out)
    if "items" not in d:
        raise SystemExit(json.dumps(d.get("error", d))[:300])
    for i in d["items"]:
        s = i["snippet"]
        print(f"{s['title'][:80]} | {s['channelTitle'][:25]} | views {i['statistics'].get('viewCount')} | tags {', '.join(s.get('tags', [])[:4])}")


if __name__ == "__main__":
    main()
