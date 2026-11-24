"""Shared YouTube helpers: access token from the private refresh token (client secret is injected by the proxy)."""
import json
import subprocess
from pathlib import Path

CANDIDATES = [Path("/home/user/sagar-private/secrets/youtube.json"), Path(__file__).resolve().parents[2] / ".." / "sagar-private" / "secrets" / "youtube.json"]


def load_cfg() -> dict:
    for p in CANDIDATES:
        if p.exists():
            return json.loads(p.read_text())
    raise SystemExit("youtube.json not found: is the private repo sagar-private attached to this session?")


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
