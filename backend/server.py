# server.py
import os
import subprocess
import uuid
import json

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow all origins on /api/*
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
)

# --- Output folders inside docs ---
BASE_DIR   = os.path.dirname(__file__)
DOCS_ROOT  = os.path.abspath(os.path.join(BASE_DIR, "..", "docs"))
VIDEOS_DIR = os.path.join(DOCS_ROOT, "videos")
POSES_DIR  = os.path.join(DOCS_ROOT, "poses")
BVH_DIR    = os.path.join(DOCS_ROOT, "bvh")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(POSES_DIR,  exist_ok=True)
os.makedirs(BVH_DIR,    exist_ok=True)


def run_extractor(video_path, out_json_path):
    """
    Call your extract_pose.py on a downloaded/saved video.
    """
    extractor = os.path.join(BASE_DIR, "extract_pose.py")
    print(f"[run_extractor] python {extractor} --input {video_path} --output {out_json_path}")
    subprocess.check_call(
        ["python", extractor, "--input", video_path, "--output", out_json_path]
    )


@app.after_request
def add_cors_headers(response):
    """
    Extra safety: ensure CORS headers are always present.
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


# ---------------------------------------------------------
# /api/yt2json : download YouTube -> video + pose JSON
# ---------------------------------------------------------
@app.route("/api/yt2json", methods=["POST", "OPTIONS"])
def yt2json():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    url = (request.form.get("url") or "").strip()
    print(f"[yt2json] Incoming URL: {url}")
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    video_id  = str(uuid.uuid4())[:8]
    mp4_path  = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    json_path = os.path.join(POSES_DIR,  f"{video_id}_pose.json")

    try:
        # 1️⃣ Download video with yt-dlp
        print(f"[yt2json] Downloading to {mp4_path}")
        subprocess.check_call(["yt-dlp", "-f", "mp4", "-o", mp4_path, url])

        # 2️⃣ Run pose extractor
        print(f"[yt2json] Running extractor -> {json_path}")
        run_extractor(mp4_path, json_path)

        # 3️⃣ Return JSON file path (relative to docs/)
        rel_mp4  = os.path.relpath(mp4_path, DOCS_ROOT)
        rel_json = os.path.relpath(json_path, DOCS_ROOT)
        print(f"[yt2json] OK video={rel_mp4}, json={rel_json}")
        return jsonify({
            "status": "ok",
            "video_path": rel_mp4,
            "json_path":  rel_json
        })

    except subprocess.CalledProcessError as e:
        print(f"[yt2json] CalledProcessError: {e}")
        return jsonify({"error": f"Processing failed: {e}"}), 500
    except Exception as e:
        print(f"[yt2json] Exception: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# /api/video2json : upload MP4 -> video + pose JSON
# ---------------------------------------------------------
@app.route("/api/video2json", methods=["POST", "OPTIONS"])
def video2json():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    base     = os.path.splitext(file.filename)[0]
    video_id = str(uuid.uuid4())[:8]
    mp4_path  = os.path.join(VIDEOS_DIR, f"{base}_{video_id}.mp4")
    json_path = os.path.join(POSES_DIR,  f"{base}_{video_id}_pose.json")

    try:
        print(f"[video2json] Saving upload to {mp4_path}")
        file.save(mp4_path)
        print(f"[video2json] Running extractor -> {json_path}")
        run_extractor(mp4_path, json_path)
        rel_mp4  = os.path.relpath(mp4_path, DOCS_ROOT)
        rel_json = os.path.relpath(json_path, DOCS_ROOT)
        print(f"[video2json] OK video={rel_mp4}, json={rel_json}")
        return jsonify({
            "status": "ok",
            "video_path": rel_mp4,
            "json_path":  rel_json
        })
    except subprocess.CalledProcessError as e:
        print(f"[video2json] CalledProcessError: {e}")
        return jsonify({"error": f"Processing failed: {e}"}), 500
    except Exception as e:
        print(f"[video2json] Exception: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# /api/save_bvh : save BVH text into docs/bvh
# ---------------------------------------------------------
@app.route("/api/save_bvh", methods=["POST", "OPTIONS"])
def save_bvh():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400

    if not data or "content" not in data:
        return jsonify({"error": "Missing 'content' in JSON body"}), 400

    content  = data["content"]
    filename = (data.get("filename") or "").strip()

    # Generate a filename if not provided
    if not filename:
        filename = f"Mocap_bvh_{uuid.uuid4().hex[:8]}.bvh"

    # Sanitize filename a bit
    filename = filename.replace("/", "_").replace("\\", "_")

    out_path = os.path.join(BVH_DIR, filename)
    try:
        print(f"[save_bvh] Writing BVH to {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        rel_bvh = os.path.relpath(out_path, DOCS_ROOT)
        return jsonify({
            "status": "ok",
            "bvh_path": rel_bvh
        })
    except Exception as e:
        print(f"[save_bvh] Exception: {e}")
        return jsonify({"error": f"Failed to save BVH: {e}"}), 500


# ---------------------------------------------------------
# /api/save_webcam_pose : save webcam pose frames JSON
# ---------------------------------------------------------
@app.route("/api/save_webcam_pose", methods=["POST", "OPTIONS"])
def save_webcam_pose():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400

    if not data or "content" not in data:
        return jsonify({"error": "Missing 'content' in JSON body"}), 400

    frames   = data["content"]
    filename = (data.get("filename") or "").strip()

    if not filename:
        filename = f"webcam_pose_{uuid.uuid4().hex[:8]}.json"

    filename = filename.replace("/", "_").replace("\\", "_")

    out_path = os.path.join(POSES_DIR, filename)
    try:
        print(f"[save_webcam_pose] Writing pose JSON to {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(frames, f)

        rel_json = os.path.relpath(out_path, DOCS_ROOT)
        return jsonify({
            "status": "ok",
            "json_path": rel_json
        })
    except Exception as e:
        print(f"[save_webcam_pose] Exception: {e}")
        return jsonify({"error": f"Failed to save webcam pose JSON: {e}"}), 500


if __name__ == "__main__":
  print(">>> Flask server running on http://127.0.0.1:5000")
  app.run(host="127.0.0.1", port=5000, debug=True)
