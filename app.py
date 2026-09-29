import json, uuid, threading
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import config
from platforms import youtube, instagram, tiktok

MAX_BYTES = 500 * 1024 * 1024
ALLOWED = {".mp4", ".mov", ".m4v"}
jobs: dict[str, dict] = {}
lock = threading.Lock()
app = FastAPI(title="Clip Poster")


def set_status(job_id, platform, state, detail=""):
    with lock:
        jobs[job_id]["platforms"][platform] = {"state": state, "detail": detail}


def run_platform(job_id, platform, fn):
    set_status(job_id, platform, "running")
    try:
        set_status(job_id, platform, "done", fn())
    except Exception as e:
        set_status(job_id, platform, "error", str(e)[:500])


def publish(job_id, filename, title, caption, targets):
    path = str(config.UPLOADS / filename)
    fns = {"youtube": lambda: youtube.post(path, title, caption),
           "instagram": lambda: instagram.post(filename, caption),
           "tiktok": lambda: tiktok.post(path, caption)}
    threads = [threading.Thread(target=run_platform, args=(job_id, p, fns[p])) for p in targets]
    [t.start() for t in threads]
    [t.join() for t in threads]
    (config.UPLOADS / filename).unlink(missing_ok=True)  # don't leave clips on disk


@app.get("/")
def index():
    return FileResponse(config.resource("static/index.html"))


@app.post("/api/post")
async def create_post(background: BackgroundTasks, video: UploadFile = File(...),
                      title: str = Form(""), caption: str = Form(""),
                      platforms: str = Form("youtube,instagram,tiktok")):
    ext = Path(video.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Use one of: {', '.join(sorted(ALLOWED))}")
    targets = [p for p in platforms.split(",") if p in ("youtube", "instagram", "tiktok")]
    if not targets:
        raise HTTPException(400, "Pick at least one platform")

    job_id = uuid.uuid4().hex[:12]
    filename = f"{job_id}{ext}"
    size = 0
    with open(config.UPLOADS / filename, "wb") as out:
        while chunk := await video.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                out.close()
                (config.UPLOADS / filename).unlink(missing_ok=True)
                raise HTTPException(413, "File too large (500 MB max)")
            out.write(chunk)

    jobs[job_id] = {"platforms": {p: {"state": "queued", "detail": ""} for p in targets}}
    background.add_task(publish, job_id, filename, title or caption[:90] or "New clip", caption, targets)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404)
    return JSONResponse(jobs[job_id])


# ---------- settings ----------
@app.get("/api/settings")
def get_settings():
    vals = config.get()
    return {"values": {k: ("" if k in config.SECRET_KEYS else v) for k, v in vals.items()},
            "secrets_set": {k: bool(vals[k]) for k in config.SECRET_KEYS},
            "youtube": {"has_client_secret": config.CLIENT_SECRET.exists(),
                        "connected": config.YT_TOKEN.exists()}}


@app.post("/api/settings")
async def save_settings(payload: dict):
    # blank values mean "leave unchanged" so saved secrets are never wiped by accident
    config.save({k: str(v).strip() for k, v in payload.items() if str(v).strip()})
    return {"ok": True}


@app.post("/api/youtube/secret")
async def youtube_secret(file: UploadFile = File(...)):
    data = await file.read()
    try:
        parsed = json.loads(data)
        assert "installed" in parsed or "web" in parsed
    except Exception:
        raise HTTPException(400, "That doesn't look like a Google client_secret.json")
    config.CLIENT_SECRET.write_bytes(data)
    return {"ok": True}


@app.post("/api/youtube/connect")
def youtube_connect():
    try:
        youtube.connect()
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"ok": True}
