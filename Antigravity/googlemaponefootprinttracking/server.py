import os
import json
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from database import init_db, save_location, get_location_history, get_stats, clear_history

app = Flask(__name__, static_folder="static")

# 自動初始化資料庫（相容 Gunicorn 與 Render）
init_db()

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    cfg = {
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "alert_distance_km": 1.0,
        "server_port": 5000,
        "server_host": "0.0.0.0"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass

    # 優先讀取雲端環境變數 (Render / Docker)
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        cfg["telegram_bot_token"] = os.environ.get("TELEGRAM_BOT_TOKEN")
    if os.environ.get("TELEGRAM_CHAT_ID"):
        cfg["telegram_chat_id"] = os.environ.get("TELEGRAM_CHAT_ID")
    if os.environ.get("ALERT_DISTANCE_KM"):
        try:
            cfg["alert_distance_km"] = float(os.environ.get("ALERT_DISTANCE_KM"))
        except ValueError:
            pass
    if os.environ.get("PORT"):
        try:
            cfg["server_port"] = int(os.environ.get("PORT"))
        except ValueError:
            pass

    return cfg

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def send_telegram_alert(text):
    config = load_config()
    token = config.get("telegram_bot_token", "").strip()
    chat_id = config.get("telegram_chat_id", "").strip()

    if not token or not chat_id or "YOUR_TELEGRAM" in token:
        print("[Telegram] 未設定有效的 Bot Token 或 Chat ID，略過發送。")
        return False, "尚未設定有效的 Token 或 Chat ID"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("ok"):
            print("[Telegram] 警報訊息發送成功！")
            return True, "發送成功"
        else:
            print(f"[Telegram] 發送失敗: {data.get('description')}")
            return False, data.get("description", "Telegram API 回傳錯誤")
    except Exception as e:
        print(f"[Telegram] 呼叫例外錯誤: {e}")
        return False, str(e)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    if request.method == "POST":
        data = request.get_json() or {}
        cfg = load_config()
        if "telegram_bot_token" in data:
            cfg["telegram_bot_token"] = str(data["telegram_bot_token"]).strip()
        if "telegram_chat_id" in data:
            cfg["telegram_chat_id"] = str(data["telegram_chat_id"]).strip()
        if "alert_distance_km" in data:
            try:
                cfg["alert_distance_km"] = float(data["alert_distance_km"])
            except ValueError:
                pass
        save_config(cfg)
        return jsonify({"status": "ok", "config": cfg})
    else:
        cfg = load_config()
        # 遮蔽部分 token 保障隱私
        masked_cfg = dict(cfg)
        token = masked_cfg.get("telegram_bot_token", "")
        if len(token) > 10:
            masked_cfg["telegram_bot_token_masked"] = token[:6] + "..." + token[-4:]
        else:
            masked_cfg["telegram_bot_token_masked"] = token
        return jsonify(masked_cfg)

@app.route("/api/location", methods=["POST"])
@app.route("/pub", methods=["POST"])
def receive_location():
    """
    接收 OwnTracks (HTTP 模式) 回傳的座標
    """
    try:
        data = request.get_json(force=True, silent=True)
    except Exception:
        data = None

    if not data:
        return jsonify({"error": "No JSON payload received"}), 400

    msg_type = data.get("_type")
    # OwnTracks location message
    if msg_type == "location" or ("lat" in data and "lon" in data):
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
        tst = int(data.get("tst", time.time()))
        acc = data.get("acc")
        batt = data.get("batt")

        cfg = load_config()
        threshold = float(cfg.get("alert_distance_km", 1.0))

        is_alert, dist_from_alert, dist_from_last = save_location(
            lat=lat,
            lon=lon,
            timestamp=tst,
            accuracy=acc,
            battery=batt,
            raw_data=data,
            alert_threshold_km=threshold
        )

        if is_alert:
            # 組織 Telegram 訊息
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tst))
            battery_str = f"{batt}%" if batt is not None else "未知"
            gmap_link = f"https://www.google.com/maps?q={lat},{lon}"

            if dist_from_alert == 0.0:
                alert_text = (
                    f"🟢 <b>【Y 的足跡追蹤已啟動】</b>\n"
                    f"📍 起始座標: <code>{lat:.5f}, {lon:.5f}</code>\n"
                    f"🔋 電量: {battery_str}\n"
                    f"🕒 時間: {time_str}\n"
                    f"🗺️ <a href=\"{gmap_link}\">在 Google 地圖中查看</a>"
                )
            else:
                alert_text = (
                    f"🚨 <b>【Y 移動警報：位移超過 {threshold:.1f} km】</b>\n"
                    f"📏 距前次通知點已移動: <b>{dist_from_alert:.2f} km</b>\n"
                    f"📍 最新座標: <code>{lat:.5f}, {lon:.5f}</code>\n"
                    f"🔋 目前電量: {battery_str}\n"
                    f"🕒 時間: {time_str}\n"
                    f"🗺️ <a href=\"{gmap_link}\">在 Google 地圖中查看最新位置</a>"
                )

            send_telegram_alert(alert_text)

        # OwnTracks 規範：回傳 200 空列表表示成功接收
        return jsonify([])

    return jsonify([])

@app.route("/api/history", methods=["GET"])
def get_history():
    limit = request.args.get("limit", default=1000, type=int)
    history = get_location_history(limit=limit)
    return jsonify(history)

@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(get_stats())

@app.route("/api/history", methods=["DELETE"])
def reset_history():
    clear_history()
    return jsonify({"status": "ok", "message": "歷史紀錄已清除"})

@app.route("/api/test-telegram", methods=["POST"])
def test_telegram():
    ok, msg = send_telegram_alert(
        "🔔 <b>【OwnTracks 追蹤系統測試】</b>\n"
        "這是一則測試訊息，代表您的 Telegram Bot 連線設定正確無誤！"
    )
    return jsonify({"ok": ok, "message": msg})

@app.route("/api/simulate", methods=["POST"])
def simulate_point():
    """
    供使用者在網頁上自訂座標或模擬位移（方便室內測試）
    """
    body = request.get_json() or {}
    lat = float(body.get("lat", 25.03396))
    lon = float(body.get("lon", 121.56447))
    batt = int(body.get("batt", 88))
    acc = int(body.get("acc", 10))
    tst = int(time.time())

    cfg = load_config()
    threshold = float(cfg.get("alert_distance_km", 1.0))

    is_alert, dist_from_alert, dist_from_last = save_location(
        lat=lat,
        lon=lon,
        timestamp=tst,
        accuracy=acc,
        battery=batt,
        raw_data={"simulate": True, "lat": lat, "lon": lon},
        alert_threshold_km=threshold
    )

    if is_alert:
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tst))
        gmap_link = f"https://www.google.com/maps?q={lat},{lon}"
        alert_text = (
            f"🚨 <b>【Y 模擬移動警報】</b>\n"
            f"📏 位移: <b>{dist_from_alert:.2f} km</b>\n"
            f"📍 座標: <code>{lat:.5f}, {lon:.5f}</code>\n"
            f"🔋 電量: {batt}%\n"
            f"🕒 時間: {time_str}\n"
            f"🗺️ <a href=\"{gmap_link}\">點擊開啟 Google 地圖</a>"
        )
        send_telegram_alert(alert_text)

    return jsonify({
        "status": "ok",
        "is_alert": is_alert,
        "dist_from_alert_km": round(dist_from_alert, 3),
        "dist_from_last_km": round(dist_from_last, 3)
    })

if __name__ == "__main__":
    init_db()
    config = load_config()
    port = int(config.get("server_port", 5000))
    host = config.get("server_host", "0.0.0.0")
    print(f"🚀 伺服器啟動於 http://localhost:{port}")
    print(f"📡 OwnTracks 請設定 HTTP 回傳網址: http://<你的IP或網址>:{port}/api/location")
    app.run(host=host, port=port, debug=False)
