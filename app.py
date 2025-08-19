from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)


@app.get("/")
def home():
    return "YouTube Downloader API is running!"


def pick_mp4_stream(formats):
    """
    Choose the best MP4 stream, preferring progressive (audio+video) and highest height.
    Falls back to any mp4 if progressive is not available.
    """
    if not formats:
        return None

    # progressive: both audio and video in one file
    progressive = [
        f for f in formats
        if (f.get("ext") == "mp4"
            and f.get("vcodec") and f["vcodec"] != "none"
            and f.get("acodec") and f["acodec"] != "none"
            and f.get("url"))
    ]
    if progressive:
        return sorted(progressive, key=lambda f: f.get("height") or 0, reverse=True)[0]

    # fallback: any mp4 with a URL
    any_mp4 = [f for f in formats if f.get("ext") == "mp4" and f.get("url")]
    if any_mp4:
        return sorted(any_mp4, key=lambda f: f.get("height") or 0, reverse=True)[0]

    return None


@app.post("/download-info")
def download_info():
    # 1) Read input
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"ok": False, "error": "No 'url' provided"}), 400

    # 2) yt-dlp options
    # Put a valid cookies.txt (exported from your browser) next to app.py
    ydl_opts = {
        "cookiefile": "cookies.txt",  # <-- include this file in your repo (keep private!)
        "format": "best[ext=mp4]/best",  # direct-stream selection when possible
        "noplaylist": True,             # treat playlists as a single video unless we handle entries
        "quiet": True,
        "nocheckcertificate": True,     # helps in some containerized envs
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # 3) If it’s a playlist, take the first entry
        if info.get("_type") == "playlist":
            entries = info.get("entries") or []
            if not entries:
                return jsonify({"ok": False, "error": "Empty playlist"}), 400
            info = entries[0] or {}

        title = info.get("title")
        duration = info.get("duration")  # seconds

        # If yt-dlp honored `format`, we usually get a direct URL at top-level
        mp4_url = info.get("url")

        # If no direct URL at top-level, pick from formats
        if not mp4_url:
            mp4_fmt = pick_mp4_stream(info.get("formats") or [])
            if mp4_fmt:
                mp4_url = mp4_fmt.get("url")

        if not mp4_url:
            return jsonify({"ok": False, "error": "No suitable MP4 stream found"}), 400

        return jsonify({
            "ok": True,
            "title": title,
            "duration": duration,
            "mp4_url": mp4_url,
        })

    except Exception as e:
        # yt-dlp surfaces a lot of provider errors here (age-gated, region, private, etc.)
        return jsonify({"ok": False, "error": f"yt-dlp failed: {e}"}), 400


if __name__ == "__main__":
    # For local testing; Render will use gunicorn via your start command.
    app.run(host="0.0.0.0", port=5000)
