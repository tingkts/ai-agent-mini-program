import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import os
import sys
import threading
import time
import requests
import monitor

# 設定標準輸出編碼
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 鎖定台灣時間 (UTC+8 / Asia/Taipei)，解決 Render 等雲端主機預設 UTC 時間相差 8 小時問題
TZ_TAIPEI = datetime.timezone(datetime.timedelta(hours=8))


def get_taipei_now_str():
    return datetime.datetime.now(TZ_TAIPEI).strftime("%Y-%m-%d %H:%M:%S")


PORT = int(os.environ.get("PORT", 8080))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 300))

# 共享執行狀態
monitor_state = {
    "is_running": True,
    "last_check_time": "尚未檢查",
    "check_count": 0,
    "status": "初始化中...",
    "available_slots": [],
    "recent_logs": []
}
state_lock = threading.Lock()


def add_log(msg: str):
    timestamp = get_taipei_now_str()
    entry = f"[{timestamp}] {msg}"
    print(entry)
    with state_lock:
        monitor_state["recent_logs"].append(entry)
        if len(monitor_state["recent_logs"]) > 20:
            monitor_state["recent_logs"].pop(0)


def background_monitor_worker():
    """在背景執行緒中持續運行的監控迴圈"""
    add_log(f"背景門診監控服務已啟動，檢查間隔：{CHECK_INTERVAL} 秒")
    last_notified_slots = set()

    while monitor_state["is_running"]:
        now_str = get_taipei_now_str()
        with state_lock:
            monitor_state["last_check_time"] = now_str
            monitor_state["check_count"] += 1

        try:
            # 抓取遠東聯合診所網頁
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(monitor.URL, headers=headers, timeout=15)
            resp.encoding = "big5"
            current_slots = monitor.parse_slots(resp.text)

            with state_lock:
                monitor_state["available_slots"] = current_slots

            if current_slots:
                with state_lock:
                    monitor_state["status"] = f"🚨 發現 {len(current_slots)} 個有名額的診次！"

                current_slots_set = set(current_slots)
                # 去重複推播保護
                if current_slots_set != last_notified_slots:
                    add_log(f"發現名額釋出！共 {len(current_slots)} 個診次，發送 Telegram 推播通知")
                    msg = "🚨 <b>黃詩瑋醫師門診有名額釋出！</b>\n\n"
                    msg += "\n\n".join(current_slots)
                    msg += f"\n\n👉 立即前往門診查詢頁面：\n{monitor.URL}"
                    monitor.send_telegram(msg)
                    last_notified_slots = current_slots_set
                else:
                    add_log("名額依然存在（上一輪已推播，暫不重複發送）")
            else:
                with state_lock:
                    monitor_state["status"] = "目前全數預掛額滿，持續監控中..."
                add_log("第 " + str(monitor_state["check_count"]) + " 次檢查完成：目前全數預掛額滿")
                last_notified_slots.clear()

        except Exception as e:
            err_msg = f"檢查門診時發生異常: {e}"
            add_log(err_msg)
            with state_lock:
                monitor_state["status"] = f"發生錯誤: {e}"

        # 等候下一次檢查
        time.sleep(CHECK_INTERVAL)


class HealthAndDashboardHandler(BaseHTTPRequestHandler):
    """處理 Render 與 UptimeRobot 的 HTTP 請求並提供網頁儀表板"""

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            with state_lock:
                data = {
                    "status": "healthy",
                    "last_check_time": monitor_state["last_check_time"],
                    "check_count": monitor_state["check_count"],
                    "slots_count": len(monitor_state["available_slots"])
                }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 預設回傳繁體中文 HTML 監控儀表板
        with state_lock:
            last_time = monitor_state["last_check_time"]
            count = monitor_state["check_count"]
            status_text = monitor_state["status"]
            slots = list(monitor_state["available_slots"])
            logs = list(monitor_state["recent_logs"])

        slots_html = ""
        if slots:
            slots_html = '<div class="alert-box"><h3>🚨 發現有名額釋出！</h3><ul>'
            for s in slots:
                slots_html += f"<li>{s}</li>"
            slots_html += "</ul></div>"
        else:
            slots_html = '<p class="status-ok">✅ 目前全數預掛額滿（系統 24 小時持續守候中）</p>'

        logs_html = "".join([f"<div>{line}</div>" for line in reversed(logs)])

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>遠東聯合診所 - 黃詩瑋醫師門診監控儀表板</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .card {{ max-width: 700px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }}
        h1 {{ font-size: 20px; color: #38bdf8; margin-top: 0; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 13px; font-weight: bold; background: #22c55e; color: #fff; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0; background: #0f172a; padding: 16px; border-radius: 8px; }}
        .info-item {{ font-size: 14px; color: #94a3b8; }}
        .info-value {{ font-size: 16px; color: #f1f5f9; font-weight: bold; margin-top: 4px; }}
        .alert-box {{ background: #dc2626; color: white; padding: 16px; border-radius: 8px; margin: 15px 0; }}
        .status-ok {{ color: #4ade80; font-weight: 500; font-size: 15px; }}
        .log-box {{ background: #020617; color: #a3e635; padding: 12px; border-radius: 8px; font-family: Consolas, monospace; font-size: 12px; max-height: 220px; overflow-y: auto; line-height: 1.6; }}
        a.btn {{ display: inline-block; background: #0284c7; color: white; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-size: 14px; font-weight: bold; margin-top: 15px; }}
        a.btn:hover {{ background: #0369a1; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🩺 遠東聯合診所 - 黃詩瑋醫師門診監控</h1>
        <span class="badge">● 雲端常駐運作中</span>

        <div class="info-grid">
            <div class="info-item">上次檢查時間<div class="info-value">{last_time}</div></div>
            <div class="info-item">累計檢查次數<div class="info-value">{count} 次</div></div>
            <div class="info-item">檢查週期<div class="info-value">每 {CHECK_INTERVAL} 秒一次</div></div>
            <div class="info-item">即時狀態<div class="info-value">{status_text}</div></div>
        </div>

        {slots_html}

        <a class="btn" href="{monitor.URL}" target="_blank">👉 前往遠東聯合診所掛號官網</a>

        <h3 style="margin-top: 25px; font-size: 14px; color: #94a3b8;">📋 即時執行日誌 (最新在前)：</h3>
        <div class="log-box">{logs_html}</div>
    </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        # 覆蓋預設的日誌以減少控制台噪音
        return


def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthAndDashboardHandler)
    add_log(f"Web 伺服器啟動於 port {PORT}，可用於 Render 與 UptimeRobot Ping")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    # 啟動背景門診監控執行緒 (Daemon Thread)
    t = threading.Thread(target=background_monitor_worker, daemon=True)
    t.start()

    # 啟動 Web 伺服器 (保持進程存活用於 Render 與 Ping)
    run_web_server()
