"""Paths + persisted settings (stored per-user, e.g. %APPDATA%\\ClipPoster)."""
import os, sys, json
from pathlib import Path


def resource(rel: str) -> Path:
    """Locate bundled files both in dev and inside a PyInstaller exe."""
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).parent
    return Path(base) / rel


DATA_DIR = Path(os.getenv("APPDATA") or Path.home() / ".config") / "ClipPoster"
UPLOADS = DATA_DIR / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"
CLIENT_SECRET = DATA_DIR / "client_secret.json"
YT_TOKEN = DATA_DIR / "youtube_token.json"

KEYS = ["YOUTUBE_PRIVACY", "IG_USER_ID", "IG_ACCESS_TOKEN", "NGROK_AUTHTOKEN",
        "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN",
        "TIKTOK_REFRESH_TOKEN", "TIKTOK_PRIVACY"]
SECRET_KEYS = {"IG_ACCESS_TOKEN", "NGROK_AUTHTOKEN", "TIKTOK_CLIENT_SECRET",
               "TIKTOK_ACCESS_TOKEN", "TIKTOK_REFRESH_TOKEN"}
DEFAULTS = {"YOUTUBE_PRIVACY": "private", "TIKTOK_PRIVACY": "SELF_ONLY"}


def _read() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except Exception:
        return {}


def load() -> None:
    data = {**DEFAULTS, **_read()}
    for k in KEYS:
        if data.get(k):
            os.environ[k] = data[k]


def get() -> dict:
    return {k: os.getenv(k, DEFAULTS.get(k, "")) for k in KEYS}


def save(updates: dict) -> None:
    data = _read()
    data.update({k: v for k, v in updates.items() if k in KEYS})
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))
    load()
