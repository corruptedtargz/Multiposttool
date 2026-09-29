import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def connect() -> None:
    """Opens the browser for Google login and stores the token."""
    if not config.CLIENT_SECRET.exists():
        raise RuntimeError("Upload your client_secret.json first.")
    flow = InstalledAppFlow.from_client_secrets_file(str(config.CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0)
    config.YT_TOKEN.write_text(creds.to_json())


def post(path: str, title: str, caption: str) -> str:
    if not config.YT_TOKEN.exists():
        raise RuntimeError("YouTube isn't connected. Open Settings → Connect YouTube.")
    creds = Credentials.from_authorized_user_file(str(config.YT_TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        config.YT_TOKEN.write_text(creds.to_json())

    yt = build("youtube", "v3", credentials=creds)
    description = caption if "#shorts" in caption.lower() else f"{caption}\n\n#Shorts"
    body = {
        "snippet": {"title": title[:100], "description": description, "categoryId": "22"},
        "status": {"privacyStatus": os.getenv("YOUTUBE_PRIVACY", "private"),
                   "selfDeclaredMadeForKids": False},
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return f"https://youtube.com/shorts/{resp['id']}"
