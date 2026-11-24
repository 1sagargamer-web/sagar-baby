"""Shared YouTube helpers: access token from the private refresh token (client secret is injected by the proxy)."""
import json
import os
import subprocess
import sys
from pathlib import Path

# Which channel's login to use: `--channel <name>` on any yt_*.py command, or the env var YT_CHANNEL.
# No flag = the first channel (secrets/youtube.json, unchanged). `--channel uth-ja-sagar` = secrets/youtube-uth-ja-sagar.json.
CHANNEL = os.environ.get("YT_CHANNEL", "")
if "--channel" in sys.argv:  # strip it here so the scripts' own argparse never sees it
    _i = sys.argv.index("--channel")
    CHANNEL = sys.argv[_i + 1]
    del sys.argv[_i:_i + 2]
_FILE = f"youtube-{CHANNEL}.json" if CHANNEL else "youtube.json"
CANDIDATES = [Path("/home/user/sagar-private/secrets") / _FILE, Path(__file__).resolve().parents[2] / ".." / "sagar-private" / "secrets" / _FILE]


def load_cfg() -> dict:
    for p in CANDIDATES:
        if p.exists():
            return json.loads(p.read_text())
    raise SystemExit(f"{_FILE} not found: is the private repo sagar-private attached to this session (and has this channel been logged in)?")


def access_token() -> str:
    cfg = load_cfg()
    out = subprocess.run(
        ["curl", "-sS", "-X", "POST", "https://oauth2.googleapis.com/token", "-d", "client_id=" + cfg["client_id"],
         "-d", "refresh_token=" + cfg["refresh_token"], "-d", "grant_type=refresh_token"],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    if "access_token" not in d:
        raise SystemExit(f"token refresh failed: {d.get('error')} {d.get('error_description', '')}")
    return d["access_token"]
