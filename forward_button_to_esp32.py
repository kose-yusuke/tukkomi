import serial
import requests
import time
import subprocess
import os

# ====== 設定 ======
SERIAL_PORT = "/dev/cu.usbserial-110"   # Leonardo のポート
BAUD        = 9600
ESP32_IP    = "157.82.205.12"
TOKEN       = "mysecret"
TIMEOUT_S   = 1.0                      # 少し余裕を持たせる
DEBOUNCE_S  = 0.3

SOUND_PATH  = "/Users/koseki.yusuke/work/Lab/tsukkomi.mp3"
SOUND_MAP = {
    1: SOUND_PATH,
    2: SOUND_PATH,
    3: SOUND_PATH,
}
TRIGGER_VALUES = set(SOUND_MAP.keys())
# ===================

def play_sound_for(val: int):
    """ボタン値 val に対応するサウンドを非同期再生"""
    path = SOUND_MAP.get(val, SOUND_PATH)  # 未定義ボタンはデフォルト
    if not os.path.exists(path):
        print(f"[AUDIO][ERR] file not found: {path}")
        return
    try:
        subprocess.Popen(["afplay", path],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        print(f"[AUDIO] playing (val={val})")
    except FileNotFoundError:
        try:
            import playsound  # pip install playsound==1.2.2
            playsound.playsound(path, block=False)
            print(f"[AUDIO] playing via playsound (val={val})")
        except Exception as e:
            print("[AUDIO][ERR]", e)

def send_trigger():
    """ESP32へHTTPトリガ送信"""
    try:
        r = requests.get(f"http://{ESP32_IP}/trigger",
                         params={"token": TOKEN},
                         timeout=TIMEOUT_S)
        print("[HTTP]", r.status_code, r.text.strip())
    except Exception as e:
        print("[HTTP][ERR]", e)

def main():
    print("[SERIAL] opening:", SERIAL_PORT, BAUD)
    with serial.Serial(SERIAL_PORT, BAUD, timeout=0.1) as ser:
        last_in_trigger = False   # 前回がトリガ値内だったかどうか
        last_fire = 0.0
        buf = b""

        while True:
            try:
                data = ser.read(64)
                if not data:
                    continue
                buf += data

                # \r\n/\n/\r 区切りで1行ずつ処理
                while b"\n" in buf or b"\r" in buf:
                    for sep in (b"\r\n", b"\n", b"\r"):
                        if sep in buf:
                            line, _, rest = buf.partition(sep)
                            buf = rest
                            break
                    s = line.decode(errors="ignore").strip()
                    if not s:
                        continue

                    # 受信値のパース
                    try:
                        val = int(s)
                    except ValueError:
                        print("[SERIAL] non-int:", s)
                        continue

                    in_trigger = (val in TRIGGER_VALUES)

                    # デバッグ：値が来ていることだけ確認したい時は下を有効化
                    # print(f"[SERIAL] val={val}, in_trigger={in_trigger}")

                    # 立ち上がり検出：非トリガ -> トリガ
                    if in_trigger and not last_in_trigger:
                        now = time.time()
                        if now - last_fire > DEBOUNCE_S:
                            print(f"[SERIAL] TRIGGER (val={val})")
                            play_sound_for(val)
                            send_trigger()
                            last_fire = now

                    # 状態更新
                    last_in_trigger = in_trigger

            except KeyboardInterrupt:
                break
            except Exception as e:
                print("[SERIAL][ERR]", e)
                time.sleep(0.2)

if __name__ == "__main__":
    main()
