import os, time
import httpx
import media_server

GRAPH = "https://graph.facebook.com/v21.0"


def post(filename: str, caption: str) -> str:
    ig_id, token = os.getenv("IG_USER_ID"), os.getenv("IG_ACCESS_TOKEN")
    if not (ig_id and token):
        raise RuntimeError("Add your Instagram user ID and access token in Settings.")
    base = media_server.public_base_url()

    with httpx.Client(timeout=60) as c:
        r = c.post(f"{GRAPH}/{ig_id}/media", data={
            "media_type": "REELS", "video_url": f"{base}/{filename}",
            "caption": caption, "access_token": token})
        if r.status_code != 200:
            raise RuntimeError(f"Instagram: {r.text[:300]}")
        container = r.json()["id"]

        for _ in range(60):
            s = c.get(f"{GRAPH}/{container}", params={
                "fields": "status_code,status", "access_token": token}).json()
            if s.get("status_code") == "FINISHED":
                break
            if s.get("status_code") in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Instagram processing failed: {s}")
            time.sleep(5)
        else:
            raise RuntimeError("Instagram processing timed out")

        r = c.post(f"{GRAPH}/{ig_id}/media_publish",
                   data={"creation_id": container, "access_token": token})
        if r.status_code != 200:
            raise RuntimeError(f"Instagram: {r.text[:300]}")
        return "published"
