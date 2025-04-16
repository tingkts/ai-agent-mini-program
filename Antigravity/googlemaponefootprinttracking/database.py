import os
import math
import json
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DATABASE_URL)
DB_PATH = os.path.join(os.path.dirname(__file__), "footprints.db")

def get_connection():
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """通用查詢執行器，自動適配 SQLite (?) 與 PostgreSQL (%s)"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if IS_POSTGRES:
            query = query.replace("?", "%s")

        cur.execute(query, params)
        if commit:
            conn.commit()
        if fetchone:
            row = cur.fetchone()
            return dict(row) if row else None
        if fetchall:
            rows = cur.fetchall()
            return [dict(r) for r in rows] if rows else []
        return None
    finally:
        cur.close()
        conn.close()

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        if IS_POSTGRES:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id SERIAL PRIMARY KEY,
                    timestamp BIGINT NOT NULL,
                    created_at VARCHAR(50) NOT NULL,
                    latitude DOUBLE PRECISION NOT NULL,
                    longitude DOUBLE PRECISION NOT NULL,
                    accuracy DOUBLE PRECISION,
                    battery INT,
                    distance_from_last DOUBLE PRECISION DEFAULT 0.0,
                    is_alert INT DEFAULT 0,
                    raw_data TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    accuracy REAL,
                    battery INTEGER,
                    distance_from_last REAL DEFAULT 0.0,
                    is_alert INTEGER DEFAULT 0,
                    raw_data TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
        conn.commit()
    finally:
        cur.close()
        conn.close()

def haversine_distance(lat1, lon1, lat2, lon2):
    """計算兩組經緯度之間的地球表面距離 (公里 km)"""
    R = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def get_setting(key, default=None):
    row = execute_query("SELECT value FROM settings WHERE key = ?", (key,), fetchone=True)
    return row["value"] if row else default

def set_setting(key, value):
    if IS_POSTGRES:
        query = """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
        """
    else:
        query = "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
    execute_query(query, (key, str(value)), commit=True)

def save_location(lat, lon, timestamp, accuracy=None, battery=None, raw_data=None, alert_threshold_km=1.0):
    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    last_alert_lat = get_setting("last_alert_lat")
    last_alert_lon = get_setting("last_alert_lon")
    last_point = get_latest_location()

    dist_from_last_point = 0.0
    if last_point:
        dist_from_last_point = haversine_distance(last_point["latitude"], last_point["longitude"], lat, lon)

    is_alert = False
    dist_from_last_alert = 0.0

    if last_alert_lat is None or last_alert_lon is None:
        is_alert = True
        dist_from_last_alert = 0.0
        set_setting("last_alert_lat", lat)
        set_setting("last_alert_lon", lon)
    else:
        dist_from_last_alert = haversine_distance(float(last_alert_lat), float(last_alert_lon), lat, lon)
        if dist_from_last_alert >= alert_threshold_km:
            is_alert = True
            set_setting("last_alert_lat", lat)
            set_setting("last_alert_lon", lon)

    raw_json = json.dumps(raw_data, ensure_ascii=False) if raw_data else "{}"

    insert_sql = """
        INSERT INTO locations 
        (timestamp, created_at, latitude, longitude, accuracy, battery, distance_from_last, is_alert, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(
        insert_sql,
        (timestamp, time_str, lat, lon, accuracy, battery, dist_from_last_point, 1 if is_alert else 0, raw_json),
        commit=True
    )

    return is_alert, dist_from_last_alert, dist_from_last_point

def get_latest_location():
    return execute_query("SELECT * FROM locations ORDER BY id DESC LIMIT 1", fetchone=True)

def get_location_history(limit=1000):
    return execute_query("SELECT * FROM locations ORDER BY id ASC LIMIT ?", (limit,), fetchall=True)

def get_stats():
    total_row = execute_query("SELECT COUNT(*) as count FROM locations", fetchone=True)
    alert_row = execute_query("SELECT COUNT(*) as count FROM locations WHERE is_alert = 1", fetchone=True)
    sum_row = execute_query("SELECT SUM(distance_from_last) as total_dist FROM locations", fetchone=True)
    latest = get_latest_location()

    total_points = total_row["count"] if total_row else 0
    total_alerts = alert_row["count"] if alert_row else 0
    total_dist = (sum_row["total_dist"] if sum_row and sum_row["total_dist"] is not None else 0.0)

    return {
        "total_points": total_points,
        "total_alerts": total_alerts,
        "total_distance_km": round(float(total_dist), 2),
        "latest": latest,
        "database_type": "PostgreSQL" if IS_POSTGRES else "SQLite"
    }

def clear_history():
    execute_query("DELETE FROM locations", commit=True)
    execute_query("DELETE FROM settings", commit=True)
