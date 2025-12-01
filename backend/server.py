# server.py
import os, subprocess, uuid, shutil
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Output folders inside docs ---
DOCS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
VIDEOS_DIR = os.path.join(DOCS_ROOT, "videos")
POSES_DIR  = os.path.join(DOCS_ROOT, "poses")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(POSES_DIR,  exist_ok=True)

def run_extractor(video_path, out_json_path):
    extractor = os.path.join(os.path.dirname(__file__), "extract_pose.py")
    subprocess.check_call(["python", extractor, "--input", video_path, "--output", out_json_path])

@app.route("/api/yt2json", methods=["POST"])
def yt2json():
    url = (request.form.get("url") or "").strip()
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    video_id = str(uuid.uuid4())[:8]
    mp4_path  = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    json_path = os.path.join(POSES_DIR,  f"{video_id}_pose.json")

    try:
        # 1️⃣ Download video with yt-dlp
        subprocess.check_call(["yt-dlp", "-f", "mp4", "-o", mp4_path, url])
        # bypass certificate check
        # Added --no-check-certificate to bypass the SSL error
        # subprocess.check_call(["yt-dlp", "--no-check-certificate", "-f", "mp4", "-o", mp4_path, url])

        # 2️⃣ Run pose extractor
        run_extractor(mp4_path, json_path)

        # 3️⃣ Return JSON file path
        rel_mp4  = os.path.relpath(mp4_path, DOCS_ROOT)
        rel_json = os.path.relpath(json_path, DOCS_ROOT)
        return jsonify({
            "status": "ok",
            "video_path": rel_mp4,
            "json_path":  rel_json
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Processing failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/video2json", methods=["POST"])
def video2json():
    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    base = os.path.splitext(file.filename)[0]
    video_id = str(uuid.uuid4())[:8]
    mp4_path  = os.path.join(VIDEOS_DIR, f"{base}_{video_id}.mp4")
    json_path = os.path.join(POSES_DIR,  f"{base}_{video_id}_pose.json")

    try:
        file.save(mp4_path)
        run_extractor(mp4_path, json_path)
        rel_mp4  = os.path.relpath(mp4_path, DOCS_ROOT)
        rel_json = os.path.relpath(json_path, DOCS_ROOT)
        return jsonify({
            "status": "ok",
            "video_path": rel_mp4,
            "json_path":  rel_json
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Processing failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
