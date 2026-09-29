import os, time
import httpx
import config

API = "https://open.tiktokapis.com/v2"


def _refresh() -> str:
    r = httpx.post(f"{API}/oauth/token/", data={
        "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
        "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
        "grant_type": "refresh_token",
        "refresh_token": os.getenv("TIKTOK_REFRESH_TOKEN")})
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"TikTok token refresh failed: {data}")
    upd = {"TIKTOK_ACCESS_TOKEN": data["access_token"]}
    if data.get("refresh_token"):
        upd["TIKTOK_REFRESH_TOKEN"] = data["refresh_token"]
    config.save(upd)  # persist rotated tokens
    return data["access_token"]


def post(path: str, caption: str) -> str:
    token = os.getenv("TIKTOK_ACCESS_TOKEN")
    if os.getenv("TIKTOK_REFRESH_TOKEN") and os.getenv("TIKTOK_CLIENT_KEY"):
        token = _refresh()  # access tokens only last ~24h
    if not token:
        raise RuntimeError("Add your TikTok credentials in Settings.")

    size = os.path.getsize(path)
    chunk = min(size, 64 * 1024 * 1024)
    total = (size + chunk - 1) // chunk
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}

    with httpx.Client(timeout=300) as c:
        body = c.post(f"{API}/post/publish/video/init/", headers=headers, json={
            "post_info": {"title": caption[:2200],
                          "privacy_level": os.getenv("TIKTOK_PRIVACY", "SELF_ONLY"),
                          "disable_duet": False, "disable_comment": False, "disable_stitch": False},
            "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                            "chunk_size": chunk, "total_chunk_count": total},
        }).json()
        if body.get("error", {}).get("code") != "ok":
            raise RuntimeError(f"TikTok: {body.get('error', body)}")
        upload_url, publish_id = body["data"]["upload_url"], body["data"]["publish_id"]

        with open(path, "rb") as f:
            for i in range(total):
                start, data = i * chunk, f.read(chunk)
                c.put(upload_url, content=data, headers={
                    "Content-Type": "video/mp4", "Content-Length": str(len(data)),
                    "Content-Range": f"bytes {start}-{start + len(data) - 1}/{size}"}
                ).raise_for_status()

        for _ in range(60):
            st = c.post(f"{API}/post/publish/status/fetch/", headers=headers,
                        json={"publish_id": publish_id}).json()
            status = st.get("data", {}).get("status")
            if status == "PUBLISH_COMPLETE":
                return "published"
            if status == "FAILED":
                raise RuntimeError(f"TikTok failed: {st['data'].get('fail_reason')}")
            time.sleep(5)
        raise RuntimeError("TikTok processing timed out")
