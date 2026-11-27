"""Upload a Short to YouTube (@sagarkekrishna), optionally scheduled, with thumbnail.

Usage:
    python3 scripts/yt_upload.py --video Export/x.mp4 --meta meta.json [--thumb thumb.jpg]
                                 [--publish-at 2026-11-21T08:00:00Z] [--synthetic]
meta.json: {"title": "...", "description": "...", "tags": ["..."]}

The video is always uploaded as *private*. With --publish-at, YouTube is asked to publish it at that UTC time.
NOTE: while the Google API project is un-audited, YouTube may keep API uploads private even at publish time.
Prints the video id and what YouTube reports back, so the caller can check.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

from yt_common import access_token


def curl(*args):
    return subprocess.run(["curl", "-sS", *args], capture_output=True, text=True, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--thumb")
    ap.add_argument("--publish-at")
    ap.add_argument("--synthetic", action="store_true", help="mark as altered/synthetic content")
    ap.add_argument("--require-thumb", action="store_true", help="exit with an error if the thumbnail was not set (Uth Ja Sagar rule)")
    a = ap.parse_args()
    tok = access_token()
    m = json.loads(Path(a.meta).read_text())
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if a.publish_at:
        status["publishAt"] = a.publish_at
    if a.synthetic:
        status["containsSyntheticMedia"] = True
    body = {"snippet": {"title": m["title"][:100], "description": m["description"], "tags": m.get("tags", []),
                        "categoryId": m.get("categoryId", "23"), "defaultLanguage": "hi", "defaultAudioLanguage": "hi"},
            "status": status}
    size = os.path.getsize(a.video)
    hdr = curl("-D", "-", "-o", "/dev/null", "-X", "POST",
               "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
               "-H", f"Authorization: Bearer {tok}", "-H", "Content-Type: application/json; charset=UTF-8",
               "-H", "X-Upload-Content-Type: video/mp4", "-H", f"X-Upload-Content-Length: {size}", "-d", json.dumps(body)).stdout
    loc = next((l.split(" ", 1)[1].strip() for l in hdr.splitlines() if l.lower().startswith("location:")), None)
    if not loc:
        raise SystemExit("could not start upload:\n" + hdr[:500])
    res = json.loads(curl("-X", "PUT", loc, "-H", "Content-Type: video/mp4", "--data-binary", f"@{a.video}").stdout)
    if "id" not in res:
        raise SystemExit("upload failed: " + json.dumps(res)[:500])
    vid = res["id"]
    print("video id:", vid)
    print("status:", res.get("status", {}).get("privacyStatus"), res.get("status", {}).get("uploadStatus"),
          "publishAt:", res.get("status", {}).get("publishAt"))
    if a.thumb:
        t = json.loads(curl("-X", "POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                            "-H", f"Authorization: Bearer {tok}", "-H", "Content-Type: image/jpeg", "--data-binary", f"@{a.thumb}").stdout)
        print("thumbnail:", "ok" if "items" in t else json.dumps(t.get("error", t))[:300])
        if a.require_thumb and "items" not in t:
            raise SystemExit(f"THUMBNAIL NOT SET for {vid}: the video is uploaded but must not be left without a thumbnail. Fix and set it.")
    elif a.require_thumb:
        raise SystemExit("--require-thumb needs --thumb (checked before upload would be better: do not upload without a thumbnail)")
    print("link: https://www.youtube.com/shorts/" + vid)


if __name__ == "__main__":
    main()
