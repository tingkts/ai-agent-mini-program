# 遠東聯合診所黃詩瑋醫師門診自動監控系統 - 完整對話與實作歷程紀錄

本文件完整記錄自對話開始至功能完全實現的全部歷程、問題排查、程式碼設計與部署教學。

---

## 目錄
1. [第一階段：Python 監控腳本初版實作與功能驗證](#一第一階段python-監控腳本初版實作與功能驗證)
2. [第二階段：實作 Python 本機自動持續監控（--loop）](#二第二階段實作-python-本機自動持續監控--loop)
3. [第三階段：加入日誌紀錄（Logging / monitor.log）](#三第三階段加入日誌紀錄logging--monitorlog)
4. [第四階段：Telegram 機器人設定教學與 CMD 語法問題排查](#四第四階段telegram-機器人設定教學與-cmd-語法問題排查)
5. [第五階段：GitHub Actions 雲端排程與多層子目錄架構調整](#五第五階段github-actions-雲端排程與多層子目錄架構調整)
6. [第六階段：GitHub Actions 取消/撤回、驗證方式與推播觸發條件說明](#六第六階段github-actions-取消撤回驗證方式與推播觸發條件說明)
7. [第七階段：GitHub Actions 延遲排查與 Render 免費雲端常駐方案](#七第七階段github-actions-延遲排查與-render-免費雲端常駐方案)
8. [第八階段：Render 專屬 Web 服務與狀態儀表板實作（web_app.py）](#八第八階段render-專屬-web-服務與狀態儀表板實作web_apppy)
9. [第九階段：Render 雲端主機 8 小時時差排查與台灣時區鎖定修復](#九第九階段render-雲端主機-8-小時時差排查與台灣時區鎖定修復)
10. [第十階段：Telegram Bot Token 安全性分析與 10 秒撤銷重置教學](#十第十階段telegram-bot-token-安全性分析與-10-秒撤銷重置教學)
11. [第十一階段：Git 查看 Remote Branch 建立與更新時間排序指令](#十一第十一階段git-查看-remote-branch-建立與更新時間排序指令)
12. [第十二階段：Render 額度機制全方位解析（750小時、每月重置、15分鐘 Spin Down）](#十二第十二階段render-額度機制全方位解析750小時每月重置15分鐘-spin-down)

---

## 一、第一階段：Python 監控腳本初版實作與功能驗證

### 1. 使用者需求
> 「請問能幫忙看一下 readme.txt 先實作出 python 腳本的部分，然後實作完成後證明一下腳本的功能符合需求。」

### 2. 分析與痛點排除
檢視 `readme.txt` 原設計，目標為抓取遠東聯合診所黃詩瑋醫師網頁（`web_netreg_Netreg_doc_Query.asp?doctor_no=F023`）。實地測試官網 HTML 時發現以下關鍵細節：
- **編碼問題**：該院 ASP 網頁使用 Big5 編碼，需明確設定 `resp.encoding = 'big5'` 避免中文亂碼。
- **HTML 語法未閉合問題**：ASP 產生的原始碼中 `<td>` 標籤並未正常閉合（例如 `<td><font>...<td>...`），使用 BeautifulSoup 預設解析會造成儲存格嚴重嵌套，導致文字重複抓取。
- **特殊狀態過濾**：
  - 診所包含「當日不提供網路掛號」，此時並非有名額，需排除。
  - 「預掛額滿」需排除。
  - 真正有名額時，按鈕文字為 `<掛號>`，並附帶 `web_netregMakeSureReg1.aspx?...` 的直接掛號連結。

### 3. 實作產出
- 建立 `monitor.py`：實現容錯解析、資訊擷取（日期/時段/診間/限額狀況/掛號連結）及 Telegram 推播。
- 建立 `requirements.txt`：`requests>=2.28.0`、`beautifulsoup4>=4.11.0`。
- 建立 `test_monitor.py`：撰寫 7 項單元測試，包含全滿模擬、有名額模擬、官網連線整合測試等，全數通過。

---

## 二、第二階段：實作 Python 本機自動持續監控（--loop）

### 1. 使用者需求
> 「請問這個 python 腳本是會自己去監看門診網頁嗎？還是需要手動下 python monitor.py 才會觸發一次檢查？請問能做到讓 python 腳本自己監控門診網頁嗎？」

### 2. 說明與升級
- **原設計說明**：原先腳本為單次執行模式，原規劃是透過 GitHub Actions 雲端排程定時跑，因此本機執行一次即結束。
- **功能擴充**：為 `monitor.py` 加入常駐循環監控函式 `start_monitoring()`：
  1. 支援 `--loop`（或 `-l`）啟動持續監控。
  2. 支援 `--interval`（或 `-i`）自訂檢查間隔秒數（預設 300 秒 / 5 分鐘）。
  3. **去重複防洗版推播保護**：若同一個名額在上一輪已推播過，下一輪檢查不重複發送 Telegram，僅在發現新釋出名額或狀態改變時才推播。
  4. 支援 `Ctrl + C` 優雅中斷退出。

---

## 三、第三階段：加入日誌紀錄（Logging / monitor.log）

### 1. 使用者需求
> 「請問能再加入寫下 log 的功能嗎？每次監控都留下記錄」

### 2. 功能實作
在 `monitor.py` 整合 Python 標準庫 `logging`：
- **同步輸出**：終端機螢幕與實體紀錄檔（`monitor.log`）同步寫入。
- **格式規範**：`[YYYY-MM-DD HH:MM:SS] [INFO/WARNING/ERROR] 訊息內容`。
- **防爆機制**：採用 `RotatingFileHandler`（上限 5MB，保留 3 份歷史備份，UTF-8 編碼確保中文不亂碼）。
- **指令彈性**：支援 `--log-file` 指定日誌檔名。

---

## 四、第四階段：Telegram 機器人設定教學與 CMD 語法問題排查

### 1. 使用者需求
> 「請問 readme.txt 中的 第一步：建立 Telegram 推播機器人（1 分鐘） 沒有說得很清楚，請問你能詳細描述，一步一步的教該怎麼做嗎？然後可以幫忙也同步更新 readme.txt 嗎？」
> 後續執行指令時反饋：
> 「在您的本機 PowerShell 終端機執行：
> $env:TELEGRAM_BOT_TOKEN=""
> $env:TELEGRAM_CHAT_ID=""
> 這一個步驟顯示 檔案名稱、目錄名稱或磁碟區標籤語法錯誤。」

### 2. 問題診斷
使用者開啟的是傳統 Windows 命令提示字元（CMD，`cmd.exe`），而非 PowerShell：
- CMD 不支援 `$env:VAR="VAL"` 語法。CMD 看到冒號 `:` 會誤以為是磁碟代號（如 `C:`），因而回報「檔案名稱、目錄名稱或磁碟區標籤語法錯誤」。
- CMD 的正確語法為 `set VAR=VAL`。

### 3. 最優解法與實機驗證
1. **即時推播測試**：使用使用者提供的 Token 與 Chat ID 進行連線測試，成功將測試訊息推送到 Telegram 機器人（`@fepc_06023_checker_bot`）與使用者（`ting`）。
2. **自動載入 `.env`**：在 `monitor.py` 實作自動讀取本機 `.env` 機制，並在本機建立 `.env` 儲存憑證。使用者今後在任何命令提示字元或 PowerShell 下，只需直接輸入 `python monitor.py`，不需手動下任何變數指令。

---

## 五、第五階段：GitHub Actions 雲端排程與多層子目錄架構調整

### 1. 使用者需求
> 「請問步驟三，它一定要作為一個 github 的專案嗎？它可以是 github 下的既有的專案的子目錄嗎？」
> 「呈上一則交談，Github 根目錄在上兩層位置 cd ../../，絕對目錄為 C:\Users\tingsung\Desktop\trash\ai-agent-mini-program，你可以直接幫我做對應的修改嗎?」

### 2. GitHub Actions 規則與調整
GitHub Actions 規定：**排程 yml 檔必須置於整個 Git 專案最頂層的 `.github/workflows/` 下**。
- **專案結構梳理**：
  ```text
  ai-agent-mini-program/                                (Git 儲存庫根目錄)
  ├── .github/
  │   └── workflows/
  │       └── monitor.yml                               (雲端定時排程)
  ├── .gitignore                                        (全域忽略規則)
  └── Antigravity/
      └── WebOutpatientAppointmentBookingChecker/       (門診爬蟲子目錄)
          ├── monitor.py
          ├── requirements.txt
          ├── monitor.log
          ├── .env                                      (金鑰憑證，不進入 Git)
          └── readme.txt
  ```
- **配置內容**：在 `ai-agent-mini-program/.github/workflows/monitor.yml` 中設定 `working-directory: ./Antigravity/WebOutpatientAppointmentBookingChecker`，使雲端執行時自動切換至子目錄安裝相依套件與執行。
- **安全防護**：於根目錄 `.gitignore` 加入 `.env` 與 `**/.env`，確保個人 Token 絕不洩漏至公開儲存庫。

---

## 六、第六階段：GitHub Actions 取消/撤回、驗證方式與推播觸發條件說明

### 1. 如何撤回/取消 GitHub Actions 排程
- **暫時停用（推薦）**：前往 GitHub 專案頁籤 -> Actions -> Hospital Slot Monitor -> 點擊右上角 `...` -> 點擊 `Disable workflow`。隨時可點「Enable workflow」恢復。
- **永久刪除**：直接刪除 `.github/workflows/monitor.yml` 並 Push 到 GitHub。

### 2. 如何驗證 GitHub Actions 正常運作
1. **立即手動測試**：Actions -> Hospital Slot Monitor -> 點擊右側 `Run workflow`，約 20~30 秒即會出現綠色打勾（Success ✅）。
2. **檢視執行日誌**：點進紀錄 -> check-slots -> 展開「執行門診監控腳本」，可查看當次檢查的爬蟲日誌與名額狀況。
3. **確認定時觸發**：放著 20~30 分鐘後回來看，記錄清單出現標記為 `scheduled` 的紀錄，即代表 24 小時定時排程運行中。

### 3. Telegram 推播觸發條件
- **觸發條件**：
  1. 官網該診次出現 `<掛號>` 按鈕或直接預約連結（`web_netregMakeSureReg1.aspx`）。
  2. 該診次並非「預掛額滿」。
  3. 自動排除「當日不提供網路掛號」（現場號）。
- **完全安靜（不發訊息）**：全數預掛額滿、當日無號時，僅寫入 Log，不打擾使用者。
- **防洗版保護**：常駐循環模式下，若名額無變化，不重複推播。

---

## 七、第七階段：GitHub Actions 延遲排查與 Render 免費雲端常駐方案

### 1. 使用者提問
> 「我怎麼覺得 github action 並沒有 10 分鐘執行一次？上一個 slot 是 20 分鐘前，然後就沒有新的 slot 了？」
> 「請參考截圖：我查看 github action 的 usage，都沒看到有每 10 分鐘執行的任務也？為什麼會這樣？」

### 2. 排查分析
- **截圖盲點**：使用者查看的網址為 `.../actions/runs/.../usage`，此處顯示的是單次 Run 的執行秒數（8s、11s、9s，合計 28s），而非排程歷史紀錄。真正的歷史清單應點擊左上角 `← Hospital Slot Monitor`。
- **GitHub 官方限制**：GitHub 官方文檔明確說明，免費版伺服器的 Cron 排程為最低優先級（Best-effort），尖峰時段會延遲 10~30 分鐘甚至丟包（Drop）。熱門的整十分鐘（`*/10 * * * *`）尤其容易塞車。
- **優化對策**：將 cron 改為非整數分鐘（`7,17,27,37,47,57 * * * *`）避開尖峰。

---

## 八、第八階段：Render 專屬 Web 服務與狀態儀表板實作（web_app.py）

### 1. 使用者需求
> 「請問可以用 render 來部署嗎？能做到一樣的行為嗎？請詳細說明一下 Render 免費版 + Ping 這個方案要怎麼做？」
> 「請問能詳細說明一下 web_app.py 是在做什麼嗎？」

### 2. 方案架構設計
- **Render 免費版規則**：15 分鐘無外部流量會自動休眠（Spin Down）。
- **雙軌整合架構**：
  1. **背景執行緒（Worker）**：每 300 秒自動連線遠東聯合診所抓資料，有名額發送 Telegram。
  2. **對外 Web 服務（HTTP Dashboard）**：採用 Python 內建 `http.server` 監聽 Port，提供手機/電腦深色模式儀表板（顯示最新檢查時間、檢查次數、即時狀態、門診直接掛號按鈕與即時日誌）。
  3. **UptimeRobot 每 5 分鐘 Ping 一次**：每 5 分鐘造訪 Render 網址一次（小於 15 分鐘門檻），破解休眠限制，達成 **100% 免費、7x24 小時永不停機**。

---

## 九、第九階段：Render 雲端主機 8 小時時差排查與台灣時區鎖定修復

### 1. 使用者提問
> 「已經部署到 render，但發現一個 issue：網頁上顯示的 log 時間戳不對，例如顯示 08:23:04，請問怎麼解決？」

### 2. 問題診斷
Render 雲端 Linux 伺服器預設採用 UTC 時間（UTC+0），與台灣標準時間（UTC+8）正好相差整整 8 個小時。

### 3. 程式碼層級永久修復
在 `web_app.py` 與 `monitor.py` 中引入 `TZ_TAIPEI = datetime.timezone(datetime.timedelta(hours=8))`：
- 日誌紀錄與儀表板時間皆透過 `get_taipei_now_str()` 強制轉換。
- `monitor.py` 的 Logging Formatter 注入自訂 `taipei_time_converter`。
- 無論雲端主機位於世界何處，時間戳記均 100% 保證為台灣當前時間。

---

## 十、第十階段：Telegram Bot Token 安全性分析與 10 秒撤銷重置教學

### 1. 使用者提問
> 「TELEGRAM_BOT_TOKEN 這一串碼外露會怎樣嗎？很危險？」

### 2. 安全邊界解析
- **權限範圍**：Token 為該機器人的唯一金鑰。外露時他人可冒充機器人發訊息、讀取傳給機器人的對話與 Chat ID。
- **個人帳號安全**：**絕對無法**透過 Bot Token 存取使用者的個人 Telegram 私聊、好友清單或個人隱私資料。
- **10 秒快速換發步驟**：向 `@BotFather` 輸入 `/mybots` -> 選擇機器人 -> 【API Token】 -> 【Revoke current token】，舊 Token 瞬間作廢，將新 Token 更新至 `.env` 與 GitHub Secrets 即可。

---

## 十一、第十一階段：Git 查看 Remote Branch 建立與更新時間排序指令

### 1. 使用者提問
> 「請問在一個指定專案下，能怎麼看出 remote branch 建立的時間，從新建立的 branch 開始往後排序？」

### 2. 解決指令
- **依最新活動/提交時間排序（最推薦）**：
  ```bash
  git for-each-ref --sort=-committerdate --format="%(committerdate:iso8601) | %(refname:short) | %(authorname)" refs/remotes/
  ```
- **依最初分叉建立時間排序**：
  ```bash
  git log -1 --format="%cd" $(git merge-base origin/main origin/<branch>)
  ```
- **GitHub 網頁檢視**：專案頁面直接點擊 `Branches` 標籤。

---

## 十二、第十二階段：Render 額度機制全方位解析（750小時、每月重置、15分鐘 Spin Down）

### 1. 使用者提問
> 「請問我如果長期放著這個服務比如說放一週，或甚至更久，這樣子 uptimerobot 跟 render 的免費使用額度會不會被耗盡？」
> 「Render 的額度重置是每個月幾號？怎麼看當前的使用額度？能看出用了多少還剩多少嗎？有跟上最新策略嗎？」
> 「被 render suspend 的 web service 只要沒有再接入服務，是不是就不會消耗額度？未使用的頁面幾分鐘後會睡眠？這時候是不是不消耗額度？」

### 2. 官方最新政策與試算
1. **重置日期**：每個月的 **1 號（UTC 00:00）** 重新分配 750 個免費執行小時（不累計至下月）。
2. **用量查詢**：登入 Render -> 左側選單 **Billing** -> **Monthly Included Usage**，具備實時進度條（`Free Instance Hours`、`Bandwidth`、`Build Minutes`）。
3. **時數充足試算**：
   - 放一週（7天）：消耗 168 小時（僅佔 22%，非常充裕）。
   - 放整個月（30天）：消耗 720 小時（小於 750 小時上限）。
   - **條件**：該 Render 帳號僅運行這 1 個免費服務時，可 24 小時全月運行不中斷。
4. **15 分鐘 Spin Down（閒置休眠）**：
   - 連續 **15 分鐘** 無外部 HTTP 流量時自動進入睡眠。
   - **睡眠期間時數消耗 = 0**（計時器完全停止）。
   - 喚醒（Cold Start）需約 50 秒。
   - 若要節省時數，只需將 UptimeRobot 點擊暫停，15 分鐘後自動進入休眠完全不扣額度；若要 24 小時監控門診，則維持 UptimeRobot 每 5 分鐘 Ping 一次。
