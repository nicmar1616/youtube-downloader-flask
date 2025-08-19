from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route("/")
def home():
    return "YouTube Downloader API is running!"

def pick_mp4_format(formats):
    """
    Prefer progressive MP4 (video+audio) up to 1080p; fall back to best MP4 with video+audio.
    """
    candidates = []
    for f in formats:
        # need both audio and video, extension mp4, and a URL present
        if f.get("ext") == "mp4" and f.get("acodec") != "none" and f.get("vcodec") != "none" and f.get("url"):
            height = f.get("height") or 0
            candidates.append((height, f["url"]))
    if not candidates:
        return None
    # sort by height descending and return the best
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

@app.route("/download-info", methods=["POST"])
def download_info():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"ok": False, "error": "Missing 'url'"}), 400

    # OPTIONAL: simple API key check to prevent abuse
    # api_key = request.headers.get("X-API-Key")
    # if api_key != "YOUR_SECRET_KEY":
    #     return jsonify({"ok": False, "error": "Unauthorized"}), 401

    ydl_opts = {"quiet": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        return jsonify({"ok": False, "error": f"yt-dlp failed: {e}"}), 400

    # YouTube can be playlists; if so, take the first entry
    if info.get("_type") == "playlist":
        entries = info.get("entries") or []
        if not entries:
            return jsonify({"ok": False, "error": "Empty playlist"}), 400
        info = entries[0]

    mp4_url = pick_mp4_format(info.get("formats", []))
    if not mp4_url:
        return jsonify({"ok": False, "error": "No suitable MP4 found"}), 400

    return jsonify({
        "ok": True,
        "title": info.get("title"),
        "duration": info.get("duration"),  # seconds
        "mp4_url": mp4_url
    })
