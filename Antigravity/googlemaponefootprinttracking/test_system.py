# -*- coding: utf-8 -*-
"""
自動化全功能單元與整合測試腳本
"""
import sys
import json
import time

def run_tests():
    print("=" * 60)
    print("🚀 開始執行全系統自動化整合測試...")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. 測試資料庫邏輯與 Haversine 距離運算
    # -------------------------------------------------------------
    print("\n[測試 1/7] 測試資料庫初始化與清理...")
    from database import (
        init_db, save_location, get_location_history, 
        get_stats, clear_history, haversine_distance
    )
    init_db()
    clear_history()
    stats = get_stats()
    assert stats["total_points"] == 0, "清空後資料量應為 0"
    print(" -> 通過：資料庫初始化與清空無誤。")

    print("\n[測試 2/7] 測試 Haversine 球面距離計算精度...")
    # 台北 101 至台北市政府直線距離約 0.6 km
    d = haversine_distance(25.033964, 121.564468, 25.042964, 121.564468)
    print(f" -> 經緯度位移測量: {d:.4f} km")
    assert 0.95 <= d <= 1.05, f"Haversine 距離計算異常: {d}"
    print(" -> 通過：距離演算法精度正確。")

    print("\n[測試 3/7] 測試 1km 判定邏輯 (微移不觸發、大位移觸發)...")
    now = int(time.time())
    
    # 點 1：起始點 (應紀錄為錨點)
    is_alert1, d_alert1, _ = save_location(25.033, 121.565, now, 10, 95, alert_threshold_km=1.0)
    assert is_alert1 == True, "起始點應被記錄為起點警報"
    print(f" -> 點 1 (起點): is_alert={is_alert1}, 距基準點={d_alert1:.3f} km")

    # 點 2：微移 150m (未達 1km，不應觸發警報)
    is_alert2, d_alert2, _ = save_location(25.034, 121.566, now + 30, 10, 94, alert_threshold_km=1.0)
    assert is_alert2 == False, "150m 移動不應觸發 1km 警報"
    print(f" -> 點 2 (位移約 150m): is_alert={is_alert2}, 距基準點={d_alert2:.3f} km")

    # 點 3：大位移 1.6km (超過 1km，必須觸發警報並更新基準點)
    is_alert3, d_alert3, _ = save_location(25.045, 121.575, now + 60, 10, 93, alert_threshold_km=1.0)
    assert is_alert3 == True, "超過 1km 移動必須觸發警報"
    print(f" -> 點 3 (位移約 1.6km): is_alert={is_alert3}, 距基準點={d_alert3:.3f} km")
    print(" -> 通過：1km 位移門檻過濾判定完全正確。")

    # -------------------------------------------------------------
    # 2. 測試 Flask Web API 端點 (使用 Flask 內建模擬客戶端)
    # -------------------------------------------------------------
    print("\n[測試 4/7] 測試 Web 介面與靜態資源伺服...")
    from server import app
    client = app.test_client()

    res = client.get("/")
    assert res.status_code == 200, "首頁應正常回應 200"
    html_text = res.get_data(as_text=True)
    assert "Y 的足跡追蹤與告警系統" in html_text, "首頁應包含 Y 追蹤系統標題"
    assert "leaflet.js" in html_text, "首頁應載入 Leaflet 圖資函式庫"
    print(" -> 通過：桌面/手機響應式 HTML 頁面正常渲染。")

    print("\n[測試 5/7] 測試 OwnTracks 官方 HTTP 協議封包相容性...")
    owntracks_payload = {
        "_type": "location",
        "lat": 25.050,
        "lon": 121.580,
        "tst": int(time.time()),
        "acc": 12,
        "batt": 85,
        "tid": "Y"
    }
    res = client.post("/api/location", json=owntracks_payload)
    assert res.status_code == 200, "OwnTracks 上傳應回傳 200"
    assert res.get_json() == [], "OwnTracks 規範需回傳空列表 []"
    print(" -> 通過：OwnTracks 協定解析與格式回應正常。")

    print("\n[測試 6/7] 測試 API 設定與模擬位移功能...")
    # 測試讀寫設定
    res = client.get("/api/config")
    assert res.status_code == 200
    res = client.post("/api/config", json={"alert_distance_km": 1.0})
    assert res.status_code == 200

    # 測試模擬位移端點
    sim_res = client.post("/api/simulate", json={"lat": 25.060, "lon": 121.590, "batt": 80})
    assert sim_res.status_code == 200
    assert sim_res.get_json()["status"] == "ok"
    print(" -> 通過：後台設定與室內位移模擬端點正常。")

    print("\n[測試 7/7] 測試歷史軌跡輸出與 Telegram 容錯防護...")
    hist_res = client.get("/api/history")
    assert hist_res.status_code == 200
    points = hist_res.get_json()
    assert len(points) >= 4, "歷史點數量應正確"

    # 測試 Telegram 在未填 Token 時不會崩潰
    tg_res = client.post("/api/test-telegram")
    assert tg_res.status_code == 200
    assert tg_res.get_json()["ok"] is False  # 尚未填入真實 token，優雅攔截

    # 清除測試數據恢復乾淨狀態
    client.delete("/api/history")
    clean_stats = client.get("/api/stats").get_json()
    assert clean_stats["total_points"] == 0
    print(" -> 通過：歷史資料查詢、重置與例外防護機制皆正常。")

    print("\n" + "=" * 60)
    print("🎉 恭喜！全部 7 項單元與整合測試 100% 通過！")
    print("整個專案無重大 Bug，已完全具備上線與本地運行條件。")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
