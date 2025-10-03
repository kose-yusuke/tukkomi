from flask import Flask, request, jsonify
import requests
import os
import time
import subprocess 

ESP32_IP    = os.getenv("ESP32_IP", "157.82.205.12")
ESP32_TOKEN = os.getenv("ESP32_TOKEN", "mysecret")
PORT        = int(os.getenv("PORT", "8000"))

SOUND_PATH  = "/Users/koseki.yusuke/work/Lab/tsukkomi.mp3"

ALLOWED_ORIGINS = {
    "https://tsukkomi.ohararyo.com",
    "https://tsukkomi.ohararyo.com/master",
    "https://tsukkomi.ohararyo.com/endpoint",
}

app = Flask(__name__)
last_fire_ts = 0.0
MIN_INTERVAL = 0.25  # 連打制限

def cors_origin():
    origin = request.headers.get("Origin", "")
    return origin if origin in ALLOWED_ORIGINS else ""

@app.after_request
def add_cors(resp):
    origin = cors_origin()
    if origin:
        resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return resp

def play_sound():
    """Macでmp3を非同期再生（afplay使用）"""
    if not os.path.exists(SOUND_PATH):
        print("[AUDIO][ERR] not found:", SOUND_PATH)
        return
    try:
        subprocess.Popen(["afplay", SOUND_PATH],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        print("[AUDIO] playing:", SOUND_PATH)
    except Exception as e:
        print("[AUDIO][ERR]", e)

@app.route("/ping", methods=["GET", "OPTIONS"])
def ping():
    if request.method == "OPTIONS":
        return ("", 204)
    try:
        r = requests.get(f"http://{ESP32_IP}/ping", timeout=2.0)
        return jsonify({"ok": True, "esp32": r.text.strip()}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 502

@app.route("/sound", methods=["POST", "GET", "OPTIONS"])
def sound():
    if request.method == "OPTIONS":
        return ("", 204)
    play_sound()
    return jsonify({"ok": True}), 200

@app.route("/trigger", methods=["GET", "POST", "OPTIONS"])  # ← GET/POST 両対応
def trigger():
    if request.method == "OPTIONS":
        return ("", 204)

    global last_fire_ts
    now = time.time()
    if now - last_fire_ts < MIN_INTERVAL:
        return jsonify({"ok": False, "error": "rate_limited"}), 429
    
    play_sound()

    try:
        r = requests.get(
            f"http://{ESP32_IP}/trigger",
            params={"token": ESP32_TOKEN},
            timeout=(5.0, 5.0)
        )
        last_fire_ts = now
        return jsonify({"ok": True, "esp32": r.text.strip()}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 502

if __name__ == "__main__":
    print(f"Proxy starting on 0.0.0.0:{PORT} → ESP32 {ESP32_IP}")
    app.run(host="0.0.0.0", port=PORT)
