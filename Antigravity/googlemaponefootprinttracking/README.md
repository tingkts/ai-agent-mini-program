# 📍 Y 的足跡追蹤與 1km 位移告警系統

本系統專為追蹤特定目標（Y）設計，配合手機端開源極省電的 **OwnTracks**，當 Y 產生 **1 公里以上的實質位移** 時，立即透過 **Telegram** 發送即時警報訊息，並在網頁地圖上精準繪製動態軌跡路線與里程碑。

---

## 🌟 核心特色

1. **雙模支援（桌面端 & 手機端網頁）**：
   - **桌面版**：左側資訊欄（總里程、警報次數、電量、里程碑清單）+ 右側高清全螢幕 Leaflet 地圖。
   - **手機版**：滿版地圖 + 頂部浮動膠囊 + 底部抽屜卡片（Bottom Sheet），觸控體驗流暢。
2. **智慧位移判定（Haversine 球面幾何）**：
   - 剛啟動時記錄起始錨點。
   - 移動達標（預設 $\ge 1.0\text{ km}$）時自動發送 Telegram 推播並在地圖標註紅色里程碑。
3. **免出門模擬測試**：
   - 網頁內建「🧪 測試位移模擬」按鈕，可直接在室內點擊模擬 1.5km 位移，立即驗證 Telegram 告警與軌跡畫線。
4. **極致省電與低流量**：
   - Y 的手機不用執行複雜運算與 Telegram 推播，單次傳輸僅 300 Bytes，靜止時耗電幾乎為 0。

---

## 🚀 快速啟動指南

### 步驟 1：啟動伺服器
在專案目錄下雙擊執行：
```bash
start.bat
```
或在終端機執行：
```bash
python server.py
```
啟動後打開瀏覽器訪問：**`http://localhost:5000`**

---

### 步驟 2：設定 Telegram 機器人推播（只需 1 分鐘）
1. 在 Telegram 搜尋 `@BotFather`，發送 `/newbot` 按照提示建立機器人，取得 **Bot Token**。
2. 在 Telegram 搜尋 `@userinfobot`，點擊 Start 取得您的個人 **Chat ID**。
3. 開啟網頁後台點擊「⚙️ Telegram 告警與門檻設定」，填入 Token 與 Chat ID，點擊「🔔 測試發送」確認收到通知即可！

---

### 步驟 3：Y 的 Android 手機設定 (OwnTracks)
1. 在 Y 的手機開啟 Google Play 下載安裝 **OwnTracks**。
2. 點擊右上角 (或左側選單) 進入 **Preferences (設定)**：
   - **Connection (連線)**：
     - **Mode**：選擇 **HTTP**
     - **Host**：填入伺服器位址，例如 `http://<你的電腦IP>:5000/api/location`（若是不同網路，可搭配 Cloudflare Tunnel 或 ngrok）。
     - **Identification**：Tracker ID 填寫 `Y`。
   - **Monitoring (監控模式)**：選擇 **Significant (顯著變動模式)**，這是最省電且最靈敏的模式。
3. 允許 OwnTracks 的「永遠允許位置資訊」與「忽視電池最佳化」。

---

## ☁️ 部署到 Render.com 指南 (免費 HTTPS 公網)

若希望讓 Y 的手機在室外 4G/5G 隨時回傳，推薦部署到免費的 Render.com：

1. **上傳程式碼到 GitHub**：
   將本資料夾推送到您自己的 GitHub Private 或 Public Repository。
2. **在 Render.com 建立 Web Service**：
   - 登入 [Render.com](https://render.com) 點選 **New +** ➔ **Web Service**。
   - 連結您的 GitHub Repository。
   - **Environment**：選擇 `Python 3`
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`gunicorn server:app`
   - **Plan**：選擇 `Free`
3. **設定環境變數 (Environment Variables)**：
   - `TELEGRAM_BOT_TOKEN`：填入您的 Telegram Bot Token
   - `TELEGRAM_CHAT_ID`：填入您的 Telegram Chat ID
   - `ALERT_DISTANCE_KM`：`1.0`
4. **取得 HTTPS 網址**：
   部署完成後，Render 會提供如 `https://footprint-tracker-y.onrender.com` 的網址。
   將此網址填入 Y 手機的 OwnTracks：
   👉 `https://<你的Render網址>/api/location`
5. **防止免費版 15 分鐘休眠（建議）**：
   - 到 [UptimeRobot](https://uptimerobot.com) 免費註冊，建立一個 HTTP Monitor，每 10 分鐘 Ping 一次 `https://<你的Render網址>/api/stats`，即可維持 24 小時不休眠！

---

## 📁 檔案結構說明

- `server.py`：Flask 後端核心，負責接收 OwnTracks 座標、判定 1km 距離與調用 Telegram Bot API。
- `database.py`：SQLite 資料庫封裝，負責記錄足跡與距離運算。
- `config.json`：儲存 Telegram 憑證、告警距離門檻（可於網頁直接修改）。
- `static/index.html`：同時適配手機與電腦瀏覽器的 Leaflet 動態軌跡地圖。
- `start.bat`：Windows 一鍵啟動腳本。
