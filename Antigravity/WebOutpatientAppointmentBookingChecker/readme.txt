遠東聯合診所黃詩瑋醫師門診 - 自動監控與即時推播系統
============================================================

透過輕量 Python 爬蟲搭配免費的雲端排程平台（GitHub Actions），就能實現全自動 24 小時監控門診名額。一旦有名額釋出，立即發送 Telegram 訊息到您的手機，附帶一鍵掛號連結。

★ 為什麼改用 Telegram Bot？
LINE Notify 已於 2025 年 3 月底終止服務，目前個人即時推播最推薦改用 Telegram Bot：
- 完全免費、無廣告、推播零延遲。
- 支援富文本 HTML 格式與超連結，手機收到通知後一鍵直達掛號頁面。
- 設定只需 2 分鐘，電腦與手機皆可同步接收。

============================================================
【第一步：建立 Telegram 推播機器人（詳細步驟教學）】
============================================================

推播需要兩個關鍵憑證：
1. TELEGRAM_BOT_TOKEN：機器人的專屬身分識別碼
2. TELEGRAM_CHAT_ID  ：您個人帳號的數字 ID

請按照以下 4 個小步驟依序操作：

------------------------------------------------------------
步驟 1-1：向官方 BotFather 建立新機器人
------------------------------------------------------------
1. 打開手機或電腦上的 Telegram App。
2. 在上方搜尋欄輸入：@BotFather（請認明名稱旁邊有藍色勾勾的官方認證帳號）。
3. 進入與 BotFather 的對話室，點擊底部的「START」按鈕（或手動輸入發送 /start）。
4. 在對話框輸入指令：
   /newbot
5. BotFather 會詢問機器人的暱稱（Name，可自訂，支援中文）：
   例如輸入：遠東門診通知小幫手
6. BotFather 接著會詢問機器人的帳號（Username，全域唯一，必須以 bot 結尾，只能用英文/數字/底線）：
   例如輸入：fepc_reg_alert_bot
   （若提示 "Sorry, this username is already taken." 代表已被他人使用，請換一個名稱）
7. 建立完成後，BotFather 會回傳一段成功訊息，其中包含一串字：
   Use this token to access the HTTP API:
   後面接著類似：7123456789:AAFn_abc123xyz456...
   👉 這串長代碼就是您的【TELEGRAM_BOT_TOKEN】，請複製並妥善存好。

------------------------------------------------------------
步驟 1-2：取得您個人的使用者 ID（Chat ID）
------------------------------------------------------------
1. 在 Telegram 搜尋欄搜尋：@userinfobot
2. 進入對話室，點擊「START」（或隨意發送任何文字）。
3. @userinfobot 會立刻回傳您的個人資訊卡片：
   Id: 123456789
   First: 您的名字
   ...
   👉 其中「Id:」後面的純數字（通常為 9～10 位數）就是您的【TELEGRAM_CHAT_ID】，請複製記下。

------------------------------------------------------------
步驟 1-3：★ 至關重要的一步：啟動您的機器人！
------------------------------------------------------------
【請特別注意】：Telegram 官方為了防範騷擾垃圾訊息，規定「機器人無法主動發送訊息給陌生人」，除非您先點擊過機器人的 Start。
1. 在 Telegram 搜尋欄搜尋您在步驟 1-1 設定的機器人帳號（例如 @fepc_reg_alert_bot）。
2. 點進去聊天室，點擊畫面最下方的【START】按鈕（或發送 /start）。
3. 這樣就完成授權！機器人未來才能順利將推播發送到您的手機。

------------------------------------------------------------
步驟 1-4：本機快速測試推播
------------------------------------------------------------
本專案已支援自動讀取專案目錄下的【.env】設定檔，您也可以手動測試：

方法 A：使用 .env 檔案（最推薦，免每次輸入變數）
在專案根目錄建立 .env 檔案，內容填入：
TELEGRAM_BOT_TOKEN=您的Token
TELEGRAM_CHAT_ID=您的ChatID

接著直接執行：
python monitor.py

方法 B：在終端機手動設定暫時環境變數
- 若使用 PowerShell（藍底或 Windows Terminal）：
  $env:TELEGRAM_BOT_TOKEN="您的Token"
  $env:TELEGRAM_CHAT_ID="您的ChatID"
  python monitor.py

- 若使用傳統命令提示字元 CMD（黑底白字 cmd.exe）：
  set TELEGRAM_BOT_TOKEN=您的Token
  set TELEGRAM_CHAT_ID=您的ChatID
  python monitor.py

若看到手機 Telegram 彈出通知，即代表設定完全成功！

============================================================
【第二步：Python 監控腳本說明（monitor.py）】
============================================================

本專案已實作完整的 monitor.py 腳本，具備以下特性：
- 自動解析遠東聯合診所黃詩瑋醫師門診網頁（採 Big5 編碼與容錯解析）。
- 精準擷取門診日期、時段、診間、預約限額，並附帶一鍵直達的線上掛號網址。
- 排除「當日不提供網路掛號」與「預掛額滿」診次，不誤發假警報。
- 支援本機 Log 紀錄檔（monitor.log），完整記錄每次檢查結果。

【本機執行方式】：
1. 單次檢查（檢查一次後退出）：
   python monitor.py

2. 常駐自動監控迴圈（每 5 分鐘自動巡檢一次，按 Ctrl+C 可停止）：
   python monitor.py --loop

3. 自訂巡檢間隔時間（例如每 60 秒檢查一次）：
   python monitor.py --loop --interval 60

============================================================
【第三步：建立 GitHub Actions 自動排程（詳細步驟教學）】
============================================================

使用 GitHub Actions 可以讓程式 24 小時在 GitHub 雲端伺服器每 10 分鐘自動幫您檢查門診，電腦不需要開機，完全免費且安全。

常見問答：它一定要是獨立的 GitHub 專案嗎？
👉 【完全不用！】它可以直接放在您現有 GitHub 專案的任一子目錄下（例如 WebOutpatientAppointmentBookingChecker/）。
只要留意 GitHub Actions 的設定檔必須放在整個專案的最頂層目錄【.github/workflows/monitor.yml】，並在設定中指定子目錄路徑即可。

以下為兩種部署方式的說明：

------------------------------------------------------------
方式 A：放在現有 GitHub 專案的「子目錄」中（目前已為您配置完成）
------------------------------------------------------------
您的專案結構為：
ai-agent-mini-program/  (GitHub 專案根目錄)
├── .github/
│   └── workflows/
│       └── monitor.yml  <-- 排程設定檔（已放置在此頂層目錄）
└── Antigravity/
    └── WebOutpatientAppointmentBookingChecker/  <-- 本門診監控子目錄
        ├── monitor.py
        ├── requirements.txt
        └── .env (敏感憑證，已加入 .gitignore 不會被上傳)

monitor.yml 已為您設定好 working-directory，內容如下：

name: Hospital Slot Monitor

on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  check-slots:
    runs-on: ubuntu-latest
    defaults:
      run:
        # 已設定指向本門診監控子目錄路徑
        working-directory: ./Antigravity/WebOutpatientAppointmentBookingChecker
    steps:
      - name: 下載專案程式碼
        uses: actions/checkout@v4

      - name: 設定 Python 環境
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 安裝相依套件
        run: pip install -r requirements.txt

      - name: 執行門診監控腳本
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python monitor.py

------------------------------------------------------------
方式 B：建立獨立的 GitHub 專案
------------------------------------------------------------
若要單獨建立專案，請按照以下 4 個小步驟：

步驟 3-1：在 GitHub 建立儲存庫（Repository）
1. 前往 GitHub 官網（https://github.com）並登入帳號。
2. 點擊首頁右上角的「+」號圖示，選擇【New repository】。
3. 設定儲存庫資訊：
   - Repository name：例如輸入 fepc-appointment-monitor
   - 設定為【Public】（推薦：公開專案享有完全無上限的免費 Actions 執行時間；敏感 Token 會存放在加密保險箱，不會公開）。
4. 點擊最下方的綠色按鈕【Create repository】。

步驟 3-2：上傳專案程式碼到 GitHub
將本機專案中的檔案推播或上傳至該儲存庫，核心檔案包含：
- monitor.py （主監控程式）
- requirements.txt （相依套件清單）
- .github/workflows/monitor.yml （自動排程設定檔）

若使用網頁上傳：
在專案首頁點擊「uploading an existing file」，將上述檔案拖曳上傳並點擊「Commit changes」。
（注意：.github/workflows/monitor.yml 為隱藏資料夾結構，若手動新增可透過 Add file -> Create new file 輸入 .github/workflows/monitor.yml 並貼入 yml 內容）。

------------------------------------------------------------
步驟 3-3：設定加密秘密變數（GitHub Secrets）
------------------------------------------------------------
無論您使用【方式 A (子目錄)】或【方式 B (獨立專案)】，都必須在 GitHub 儲存庫設定金鑰：
1. 進入該 GitHub 專案頁面。
2. 點擊上方導覽列最右邊的【Settings】（設定）。
3. 在左側功能選單中找到【Secrets and variables】，點擊展開後點選【Actions】。
4. 點擊右上角綠色按鈕【New repository secret】：
   - 新增第一個 Secret：
     Name 欄位輸入：TELEGRAM_BOT_TOKEN
     Secret 欄位貼上：步驟 1-1 取得的 Token
     點擊「Add secret」確認儲存。
   - 新增第二個 Secret：
     再次點擊「New repository secret」
     Name 欄位輸入：TELEGRAM_CHAT_ID
     Secret 欄位貼上：步驟 1-2 取得的純數字 ID
     點擊「Add secret」確認儲存。

------------------------------------------------------------
步驟 3-4：手動觸發測試與確認排程運行
------------------------------------------------------------
1. 點擊專案上方導覽列的【Actions】頁籤。
2. 若畫面上出現提示，請點擊綠色按鈕啟用 Workflows（I understand my workflows, go ahead and enable them）。
3. 在左側選單點擊【Hospital Slot Monitor】。
4. 在右側會看到一個【Run workflow】的按鈕，點擊它並按下綠色的【Run workflow】。
5. 稍等約 30 秒，重新整理頁面，會看到一筆記錄並帶有綠色勾勾（Success）✅。
6. 點擊進去可展開「執行門診監控腳本」查看實際執行日誌！
7. 測試成功後即大功告成！之後 GitHub 會自動依照排程（每 10 分鐘）自動在背景檢測，一旦門診名額釋出，手機 Telegram 就會第一時間收到掛號警報！

============================================================
【常見問題：如何暫停、撤回或取消 GitHub Action 排程？】
============================================================

當您掛號成功或暫時不需要門診監控時，有以下兩種方式可以取消：

方法一：暫時停用（最推薦，保留程式碼，隨時可一鍵恢復）
不需刪除任何檔案，只需在 GitHub 網頁上按一個按鈕即可暫停：
1. 前往 GitHub 專案頁面，點選【Actions】頁籤。
2. 在左側清單點選【Hospital Slot Monitor】。
3. 點選右上角的【...】（三個點圖示）。
4. 點選【Disable workflow】。
👉 如此一來排程就會立即停止，GitHub 不會再定時執行；日後若還需要，只需點選「Enable workflow」即可一鍵恢復！

方法二：永久刪除（徹底移除排程）
如果您以後完全不再需要這個自動排程：
- 直接將專案中的【.github/workflows/monitor.yml】刪除並 push 到 GitHub：
  git rm .github/workflows/monitor.yml
  git commit -m "remove: 刪除門診監控 Actions 排程"
  git push
- 或直接在 GitHub 網頁上點進該檔案，點擊右上角垃圾桶圖示刪除並 Commit。
👉 刪除該 yml 檔案後，GitHub Actions 就會徹底移除此排程任務。












＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
Telegram



Done! Congratulations on your new bot. You will find it at t.me/fepc_06023_checker_bot. You can now add a description,
about section and profile picture for your bot, see /help for a list of commands.
By the way, when you've finished creating your cool bot,
ping our Bot Support if you want a better username for it. Just make sure the bot is fully operational before you do this.

Use this token to access the HTTP API:


Keep your token secure and store it safely, it can be used by anyone to control your bot.

For a description of the Bot API, see this page: https://core.telegram.org/bots/api




Id:


First: ting
Lang: zh-hans
Registered: Check Date

🧠 Explanations and answers
Free AI → DeepSeek & ChatGPT

🖼 Visualize your ideas
Make Image → NanoBanana

＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
