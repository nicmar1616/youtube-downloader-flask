from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "YouTube Downloader API is running!"})

@app.route('/download-info', methods=['POST'])
def download_info():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"ok": False, "error": "No URL provided"}), 400

    # yt-dlp options
    ydl_opts = {
        "cookiefile": "cookies.txt",   # since cookies.txt is at root
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return jsonify({
                "ok": True,
                "title": info.get("title"),
                "duration": info.get("duration"),
                "mp4_url": info.get("url")
            })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
