import argparse
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

# 設定標準輸出編碼以避免 Windows 控制台亂碼
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_dotenv(dotenv_path=".env"):
    """若存在 .env 檔案則自動載入環境變數（不需額外安裝第三方套件）。"""
    if os.path.exists(dotenv_path):
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val


load_dotenv()

URL = "https://www.fepc.com.tw/web_netreg2/web_netreg_Netreg_doc_Query.asp?doctor_no=F023"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DEFAULT_LOG_FILE = "monitor.log"

logger = logging.getLogger("slot_monitor")


TZ_TAIPEI = datetime.timezone(datetime.timedelta(hours=8))


def taipei_time_converter(*args):
    """將日誌時間強制轉為台灣時間 (UTC+8)"""
    return datetime.datetime.now(TZ_TAIPEI).timetuple()


def setup_logger(log_file: str = DEFAULT_LOG_FILE, level=logging.INFO):
    """設定 Logger 同步輸出至螢幕終端機與 Log 檔案。"""
    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    formatter.converter = taipei_time_converter

    # 確保有終端機輸出 (StreamHandler)
    has_stream = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
        for h in logger.handlers
    )
    if not has_stream:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # 檢查是否已存在目標檔案的 FileHandler
    abs_target = os.path.abspath(log_file)
    existing_file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
    file_handler_exists = any(
        getattr(h, "baseFilename", None) == abs_target for h in existing_file_handlers
    )

    if not file_handler_exists:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def send_telegram(message: str) -> bool:
    """發送 Telegram 訊息。若未設定 Token 或 Chat ID 則輸出至終端機作為測試。"""
    token = os.getenv("TELEGRAM_BOT_TOKEN") or TELEGRAM_TOKEN
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.warning(f"未設定 Telegram 憑證，輸出測試訊息：\n{message}")
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(api_url, data=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Telegram 推播發送成功！")
        return True
    except requests.RequestException as e:
        logger.error(f"Telegram 推播發送失敗: {e}")
        return False


def parse_slots(html_content: str) -> list:
    """解析遠東聯合診所門診查詢網頁 HTML，回傳有名額的診次清單。"""
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.find_all("tr")

    available_slots = []

    for row in rows:
        # 排除包含其他 tr 的最外層容器 tr
        if row.find("tr"):
            continue

        text = row.get_text()
        # 篩選門診時間列
        if "星期" in text and "診" in text:
            # 尋找直接掛號連結 (例如 web_netregMakeSureReg1.aspx)
            reg_link = row.find("a", href=re.compile(r"web_netregMakeSureReg", re.I))

            # 判斷是否有名額：有掛號連結，或包含「<掛號>」、「可掛號」
            is_available = bool(reg_link) or ("<掛號>" in text or "可掛號" in text)

            # 排除「當日不提供網路掛號」或無掛號連結的「預掛額滿」
            if "當日不提供網路掛號" in text:
                is_available = False
            if "預掛額滿" in text and not reg_link:
                is_available = False

            if is_available:
                # 擷取日期與時段（例如：115/11/10 星期二 下午診）
                m_date = re.search(r"(\d+/\d+/\d+\s*星期[一二三四五六日]\s*[上下晚]午診)", text)
                date_str = re.sub(r"\s+", " ", m_date.group(1)).strip() if m_date else ""

                # 擷取科別
                dept_str = "眼科" if "眼科" in text else ""

                # 擷取診間（例如：三樓十五診 (315)）
                m_room = re.search(r"([^\s]+樓[^\s]+診(?:\s*\([^)]+\))?)", text)
                room_str = re.sub(r"\s+", " ", m_room.group(1)).strip() if m_room else ""

                # 擷取預約限額狀況（例如：限40人 已約29人）
                m_status = re.search(r"(限\d+人\s*(?:已約\d+人)?)", text)
                status_str = re.sub(r"\s+", " ", m_status.group(1)).strip() if m_status else "尚有名額"

                slot_desc = f"{date_str} | {dept_str} | {room_str} | {status_str}".replace(" |  | ", " | ").strip(" |")

                # 若有直接掛號連結，一併附上
                if reg_link and reg_link.get("href"):
                    slot_desc += f"\n   🔗 掛號連結：{reg_link.get('href')}"

                available_slots.append(slot_desc)

    return available_slots


def check_slots(html_content: str = None) -> list:
    """檢查黃詩瑋醫師門診名額。若傳入 html_content 則解析該內容，否則從遠東聯合診所網站抓取。"""
    setup_logger()

    if html_content is None:
        logger.info(f"正在連線門診查詢頁面：{URL}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 遠東聯合診所網頁採 Big5 編碼
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.encoding = "big5"
        html_content = resp.text

    available_slots = parse_slots(html_content)

    if available_slots:
        logger.info(f"發現名額釋出！共 {len(available_slots)} 個診次可預約。")
        msg = "🚨 <b>黃詩瑋醫師門診有名額釋出！</b>\n\n"
        msg += "\n\n".join(available_slots)
        msg += f"\n\n👉 立即前往門診查詢頁面：\n{URL}"
        send_telegram(msg)
    else:
        logger.info("檢查完成：目前全數預掛額滿，持續監控中...")

    return available_slots


def start_monitoring(interval_seconds: int = 300, max_iterations: int = None, log_file: str = DEFAULT_LOG_FILE):
    """
    常駐自動監控迴圈：
    :param interval_seconds: 每次檢查間隔秒數（預設 300 秒 = 5 分鐘）
    :param max_iterations: 最大檢查次數（預設 None 為無限循環，可用於測試）
    :param log_file: Log 檔案路徑（預設 monitor.log）
    """
    setup_logger(log_file=log_file)
    logger.info("啟動黃詩瑋醫師門診自動監控模式...")
    logger.info(f"檢查頻率：每 {interval_seconds} 秒檢查一次（按 Ctrl+C 可停止監控）")
    logger.info(f"紀錄檔存放路徑：{os.path.abspath(log_file)}")

    iteration = 0
    last_notified_slots = set()

    try:
        while True:
            iteration += 1
            logger.info(f"--- [第 {iteration} 次檢查開始] ---")

            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                resp = requests.get(URL, headers=headers, timeout=15)
                resp.encoding = "big5"
                current_slots = parse_slots(resp.text)

                if current_slots:
                    current_slots_set = set(current_slots)
                    # 避免重複轟炸：僅在有新釋出名額或狀態異動時推播
                    if current_slots_set != last_notified_slots:
                        logger.info(f"發現名額釋出！共 {len(current_slots)} 個診次：\n" + "\n".join(current_slots))
                        msg = "🚨 <b>黃詩瑋醫師門診有名額釋出！</b>\n\n"
                        msg += "\n\n".join(current_slots)
                        msg += f"\n\n👉 立即前往門診查詢頁面：\n{URL}"
                        send_telegram(msg)
                        last_notified_slots = current_slots_set
                    else:
                        logger.info("名額依然存在（已於上一輪推播過，暫不重複發送推播通知）。")
                else:
                    logger.info("檢查完成：目前全數預掛額滿。")
                    last_notified_slots.clear()

            except Exception as e:
                logger.error(f"檢查時發生異常: {e}", exc_info=True)

            if max_iterations is not None and iteration >= max_iterations:
                logger.info(f"已達指定檢查次數 ({max_iterations})，停止監控。")
                break

            logger.info(f"等待 {interval_seconds} 秒後進行下一次檢查...\n")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        logger.info("收到中斷信號 (Ctrl+C)，已安全停止自動監控。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="遠東聯合診所黃詩瑋醫師門診名額監控")
    parser.add_argument(
        "--loop", "-l",
        action="store_true",
        help="啟動常駐自動監控迴圈（按 Ctrl+C 結束）"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=300,
        help="自動監控時的檢查間隔秒數（預設 300 秒 = 5 分鐘）"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=DEFAULT_LOG_FILE,
        help=f"紀錄檔輸出路徑（預設: {DEFAULT_LOG_FILE}）"
    )
    args = parser.parse_args()

    setup_logger(log_file=args.log_file)

    if args.loop:
        start_monitoring(interval_seconds=args.interval, log_file=args.log_file)
    else:
        check_slots()
