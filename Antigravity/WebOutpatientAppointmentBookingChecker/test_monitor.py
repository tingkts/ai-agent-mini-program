import os
import unittest
from unittest.mock import patch, MagicMock
import monitor

# 模擬情況 1: 所有診次皆預掛額滿與當日不提供網路掛號
MOCK_HTML_ALL_FULL = """
<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=big5"></head>
<body>
<table>
  <tr><td>外層包裝</td></tr>
  <tr>
    <td>當日不提供網路掛號</td>
    <td>眼科</td>
    <td>115/10/27<br>星期二 下午診</td>
    <td>三樓十五診 (315)</td>
    <td>06023</td>
    <td>當日不提供網路掛號</td>
  </tr>
  <tr>
    <td>預掛額滿</td>
    <td>眼科</td>
    <td>115/10/28<br>星期三 上午診</td>
    <td>三樓十五診 (315)</td>
    <td>06023</td>
    <td>限40人 預掛額滿</td>
  </tr>
  <tr>
    <td>預掛額滿</td>
    <td>眼科</td>
    <td>115/10/30<br>星期五 下午診</td>
    <td>三樓十五診 (315)</td>
    <td>06023</td>
    <td>限40人 預掛額滿</td>
  </tr>
</table>
</body>
</html>
"""

# 模擬情況 2: 有名額釋出 (包含掛號連結與限額狀況)
MOCK_HTML_WITH_AVAILABLE_SLOTS = """
<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=big5"></head>
<body>
<table>
  <tr>
    <td><a href="https://reg.fepc.com.tw/NetReg/KReg/web_netregMakeSureReg1.aspx?doctor=F023&date=1151110&apn=2&div_no=1260&clino=315">&lt;掛號&gt;</a></td>
    <td>眼科</td>
    <td>115/11/10<br>星期二 下午診</td>
    <td>三樓十五診 (315)</td>
    <td>06023</td>
    <td><font color="#000080">限40人<br>已約29人</font></td>
  </tr>
  <tr>
    <td>預掛額滿</td>
    <td>眼科</td>
    <td>115/11/12<br>星期四 上午診</td>
    <td>三樓十五診 (315)</td>
    <td>06023</td>
    <td>限40人 預掛額滿</td>
  </tr>
</table>
</body>
</html>
"""


class TestSlotMonitor(unittest.TestCase):

    def setUp(self):
        # 確保 logger 已初始化
        monitor.setup_logger()

    def test_all_full_scenario(self):
        """測試情境：當所有診次額滿或當日不提供掛號時，應回傳空清單"""
        slots = monitor.parse_slots(MOCK_HTML_ALL_FULL)
        self.assertEqual(len(slots), 0, "額滿時不應識別出可預約名額")

    def test_available_slot_scenario(self):
        """測試情境：當有名額釋出時，應正確解析診次資訊與掛號連結"""
        slots = monitor.parse_slots(MOCK_HTML_WITH_AVAILABLE_SLOTS)
        self.assertEqual(len(slots), 1, "應正確識別出 1 個可預約名額")
        
        slot_text = slots[0]
        self.assertIn("115/11/10", slot_text)
        self.assertIn("星期二 下午診", slot_text)
        self.assertIn("限40人已約29人", slot_text.replace(" ", ""))
        self.assertIn("web_netregMakeSureReg1.aspx", slot_text)

    def test_check_slots_no_slots(self):
        """測試 check_slots 在額滿時正確回傳空清單"""
        result = monitor.check_slots(html_content=MOCK_HTML_ALL_FULL)
        self.assertEqual(len(result), 0)

    @patch("monitor.send_telegram")
    def test_check_slots_with_slots_triggers_telegram(self, mock_send_telegram):
        """測試 check_slots 在發現名額時會觸發 Telegram 推播函式"""
        result = monitor.check_slots(html_content=MOCK_HTML_WITH_AVAILABLE_SLOTS)
        self.assertEqual(len(result), 1)
        mock_send_telegram.assert_called_once()
        msg_arg = mock_send_telegram.call_args[0][0]
        self.assertIn("黃詩瑋醫師門診有名額釋出", msg_arg)
        self.assertIn("115/11/10", msg_arg)

    @patch("requests.post")
    def test_send_telegram_with_credentials(self, mock_post):
        """測試在有 Telegram Token 與 Chat ID 時正確呼叫 API"""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "mock_token_123", "TELEGRAM_CHAT_ID": "mock_chat_456"}):
            success = monitor.send_telegram("測試名額訊息")
            self.assertTrue(success)
            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            self.assertEqual(called_url, "https://api.telegram.org/botmock_token_123/sendMessage")
            called_data = mock_post.call_args[1]["data"]
            self.assertEqual(called_data["chat_id"], "mock_chat_456")
            self.assertEqual(called_data["text"], "測試名額訊息")

    def test_send_telegram_without_credentials_safe_fallback(self):
        """測試在未設定 Telegram 憑證時安全降級為 Console 輸出而不當機"""
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}, clear=True):
            with patch("monitor.TELEGRAM_TOKEN", None), patch("monitor.TELEGRAM_CHAT_ID", None):
                success = monitor.send_telegram("未設定憑證測試")
                self.assertFalse(success)

    @patch("monitor.send_telegram")
    @patch("requests.get")
    def test_start_monitoring_loop_and_deduplication(self, mock_get, mock_send_telegram):
        """測試自動循環監控機制，以及防止重複推播相同名額的功能"""
        mock_resp = MagicMock()
        mock_resp.encoding = "big5"
        mock_resp.text = MOCK_HTML_WITH_AVAILABLE_SLOTS
        mock_get.return_value = mock_resp

        # 執行 2 次循環，間隔 0 秒
        monitor.start_monitoring(interval_seconds=0, max_iterations=2)

        # 雖然檢查了 2 次，但因為名額內容完全相同，推播函式只會被觸發 1 次（去重複機制成功）
        self.assertEqual(mock_send_telegram.call_count, 1)

    def test_log_file_written(self):
        """測試 Log 檔案是否確實寫入磁碟且包含中文紀錄內容"""
        test_log = "test_run.log"
        if os.path.exists(test_log):
            os.remove(test_log)

        monitor.setup_logger(log_file=test_log)
        monitor.check_slots(html_content=MOCK_HTML_ALL_FULL)

        self.assertTrue(os.path.exists(test_log), "Log 檔案應被建立")
        with open(test_log, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("全數預掛額滿", content)

        # 關閉並移除測試 handler 以便在 Windows 上安全清理測試檔案
        for h in list(monitor.logger.handlers):
            if isinstance(h, monitor.RotatingFileHandler) and h.baseFilename == os.path.abspath(test_log):
                h.close()
                monitor.logger.removeHandler(h)

        if os.path.exists(test_log):
            os.remove(test_log)

    def test_live_website_fetch(self):
        """測試實際連線遠東聯合診所官網執行即時檢查"""
        slots = monitor.check_slots()
        self.assertIsInstance(slots, list)
        print(f"\n[實機連線測試成功] 目前官網回傳的名額數量: {len(slots)}")


if __name__ == "__main__":
    unittest.main()
