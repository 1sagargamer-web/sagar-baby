"""Daily title research: what titles do the most-viewed recent Shorts in India use for a topic?

Usage: python3 scripts/yt_title_research.py "krishna comedy shorts hindi" "gta 6 funny hindi" [--days 90]
Prints stats (visible-title length, emoji, hashtags) and the top titles, so the day's titles are chosen from data.
"""
import argparse, json, re, statistics as st, subprocess, urllib.parse
from datetime import datetime, timedelta, timezone

from yt_common import access_token

clean = lambda t: re.split(r"\s*#", t)[0].strip()
emo = lambda t: len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", t))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--days", type=int, default=90)
    a = ap.parse_args()
    tok = access_token()
    api = lambda p: json.loads(subprocess.run(["curl", "-sS", "https://www.googleapis.com/youtube/v3/" + p, "-H", "Authorization: Bearer " + tok], capture_output=True, text=True).stdout)
    since = (datetime.now(timezone.utc) - timedelta(days=a.days)).strftime("%Y-%m-%dT00:00:00Z")
    ids = []
    for q in a.queries:
        d = api("search?part=id&type=video&videoDuration=short&regionCode=IN&relevanceLanguage=hi&order=viewCount&maxResults=25&publishedAfter=" + since + "&q=" + urllib.parse.quote(q))
        ids += [i["id"]["videoId"] for i in d.get("items", [])]
    ids = list(dict.fromkeys(ids))[:50]
    rows = []
    for v in api("videos?part=snippet,statistics&id=" + ",".join(ids)).get("items", []):
        rows.append((int(v["statistics"].get("viewCount", 0)), v["snippet"]["title"]))
    rows.sort(reverse=True)
    if not rows:
        raise SystemExit("no results")
    top = rows[:20]
    L = [len(clean(t)) for _, t in top]; W = [len(clean(t).split()) for _, t in top]
    print(f"{len(rows)} videos | top-20 visible title: median {st.median(L):.0f} chars / {st.median(W):.0f} words | "
          f"hashtags median {st.median(t.count('#') for _, t in top):.0f} | emoji median {st.median(emo(t) for _, t in top):.0f}")
    for v, t in rows[:15]:
        print(f"{v/1e6:7.1f}M | {len(clean(t)):>2} ch | {clean(t)[:70]} | {' '.join(re.findall(r'#\w+', t)[:4])}")


if __name__ == "__main__":
    main()
