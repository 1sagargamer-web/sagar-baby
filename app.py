"""
Video Downloader - link daalo, video download karo.

Run:
    pip install -r requirements.txt
    python app.py
Phir browser me kholo: http://127.0.0.1:5000
"""

import os
import shutil
import threading
import uuid

from flask import Flask, jsonify, render_template, request, send_file, abort
import yt_dlp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HAS_FFMPEG = shutil.which("ffmpeg") is not None

app = Flask(__name__)

# job_id -> {status, percent, speed, eta, filename, filepath, error, title}
jobs = {}
jobs_lock = threading.Lock()


def format_selector(quality: str) -> str:
    """User ki choice ko yt-dlp format string me badlo."""
    if quality == "audio":
        return "bestaudio/best"
    if not HAS_FFMPEG:
        # ffmpeg ke bina video+audio merge nahi ho sakta, isliye single file wala format lo
        if quality == "best":
            return "best[ext=mp4]/best"
        return f"best[height<={quality}][ext=mp4]/best[height<={quality}]/best"
    if quality == "best":
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
    return (
        f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
    )


def update_job(job_id, **fields):
    with jobs_lock:
        jobs[job_id].update(fields)


def run_download(job_id: str, url: str, quality: str):
    job_dir = os.path.join(DOWNLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            percent = round(done * 100 / total, 1) if total else 0
            update_job(
                job_id,
                status="downloading",
                percent=percent,
                speed=d.get("_speed_str", "").strip(),
                eta=d.get("_eta_str", "").strip(),
            )
        elif d["status"] == "finished":
            update_job(job_id, status="processing", percent=100)

    opts = {
        "format": format_selector(quality),
        "outtmpl": os.path.join(job_dir, "%(title).150B.%(ext)s"),
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": False,
    }
    if quality == "audio" and HAS_FFMPEG:
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    elif HAS_FFMPEG:
        opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            update_job(job_id, title=info.get("title", ""))

        files = [f for f in os.listdir(job_dir) if not f.endswith((".part", ".ytdl"))]
        if not files:
            raise RuntimeError("Download hua par file nahi mili.")
        # sabse badi file hi final output hai
        files.sort(key=lambda f: os.path.getsize(os.path.join(job_dir, f)), reverse=True)
        final = files[0]
        update_job(
            job_id,
            status="done",
            percent=100,
            filename=final,
            filepath=os.path.join(job_dir, final),
        )
    except Exception as e:  # noqa: BLE001
        msg = str(e).replace("ERROR: ", "")
        update_job(job_id, status="error", error=msg)


@app.route("/")
def index():
    return render_template("index.html", has_ffmpeg=HAS_FFMPEG)


@app.post("/api/info")
def api_info():
    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify(error="Pehle video ka link daalo."), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=str(e).replace("ERROR: ", "")), 400

    heights = sorted(
        {f.get("height") for f in info.get("formats") or [] if f.get("height")},
        reverse=True,
    )
    return jsonify(
        title=info.get("title"),
        thumbnail=info.get("thumbnail"),
        duration=info.get("duration_string") or "",
        uploader=info.get("uploader") or info.get("channel") or "",
        site=info.get("extractor_key", ""),
        heights=heights,
    )


@app.post("/api/download")
def api_download():
    data = request.json or {}
    url = data.get("url", "").strip()
    quality = str(data.get("quality", "best"))
    if not url:
        return jsonify(error="Pehle video ka link daalo."), 400
    if quality not in ("best", "audio") and not quality.isdigit():
        return jsonify(error="Galat quality."), 400

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {"status": "starting", "percent": 0, "speed": "", "eta": ""}
    threading.Thread(target=run_download, args=(job_id, url, quality), daemon=True).start()
    return jsonify(job_id=job_id)


@app.get("/api/progress/<job_id>")
def api_progress(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify(error="Job nahi mila."), 404
        return jsonify({k: v for k, v in job.items() if k != "filepath"})


@app.get("/api/file/<job_id>")
def api_file(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        abort(404)
    return send_file(job["filepath"], as_attachment=True, download_name=job["filename"])


if __name__ == "__main__":
    if not HAS_FFMPEG:
        print("NOTE: ffmpeg nahi mila - HD quality aur MP3 ke liye ffmpeg install karo.")
    print("App chal raha hai: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
