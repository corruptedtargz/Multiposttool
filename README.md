# Clip Poster (Windows desktop app)

Drop in a clip → posts to YouTube Shorts, Instagram Reels and TikTok.

## Get the .exe
**Option A – on your PC (needs Python 3.10+):** double-click `build.bat` → `dist\ClipPoster.exe`.
**Option B – no Python:** push this folder to a GitHub repo; the included Actions workflow
builds `ClipPoster.exe` and attaches it as a downloadable artifact.

Dev run: `pip install -r requirements.txt && python main.py`

## First-time setup (all inside the app's ⚙ Settings)
- **YouTube:** Google Cloud → enable YouTube Data API v3 → OAuth client type *Desktop app* → download JSON →
  *Upload client_secret.json* → *Connect YouTube*. Unverified projects upload as private until audited.
- **Instagram:** Professional account linked to a Facebook Page + Meta app with `instagram_content_publish`;
  paste user ID + token. Add a free ngrok authtoken: the app briefly serves just the clip through a tunnel
  so Instagram can download it (nothing else is exposed).
- **TikTok:** developers.tiktok.com → Content Posting API (`video.publish`); paste keys/tokens.
  Unaudited apps can only post as SELF_ONLY (private).

Settings are stored in `%APPDATA%\ClipPoster\settings.json` (plain text). Clips are deleted after posting.
