import sqlite3
import os
from datetime import datetime


DB_PATH = None


def get_db_path():
    global DB_PATH
    if DB_PATH is None:
        from config import Config
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), Config.DATABASE_PATH)
    return DB_PATH


def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS city (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ip          TEXT NOT NULL,
            city        TEXT NOT NULL,
            lat         REAL,
            lon         REAL,
            country     TEXT,
            region      TEXT,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_snapshot (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            city         TEXT NOT NULL,
            temp         REAL,
            feels_like   REAL,
            weather_text TEXT,
            wind_dir     TEXT,
            wind_speed   REAL,
            humidity     REAL,
            visibility   REAL,
            cloud        REAL,
            obs_time     TIMESTAMP,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS air_snapshot (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            city        TEXT NOT NULL,
            aqi         INTEGER,
            category    TEXT,
            pm2p5       REAL,
            pm10        REAL,
            so2         REAL,
            no2         REAL,
            co          REAL,
            o3          REAL,
            obs_time    TIMESTAMP,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS forecast (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            city         TEXT NOT NULL,
            date         TEXT NOT NULL,
            temp_max     REAL,
            temp_min     REAL,
            humidity     REAL,
            weather_text TEXT,
            wind_dir     TEXT,
            wind_speed   REAL,
            updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, date)
        )
    """)

    conn.commit()
    conn.close()


def save_city(ip, city, lat, lon, country="", region=""):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("SELECT id FROM city WHERE ip = ?", (ip,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE city SET city=?, lat=?, lon=?, country=?, region=?, updated_at=? WHERE ip=?",
            (city, lat, lon, country, region, now, ip)
        )
    else:
        cur.execute(
            "INSERT INTO city (ip, city, lat, lon, country, region, updated_at) VALUES (?,?,?,?,?,?,?)",
            (ip, city, lat, lon, country, region, now)
        )
    conn.commit()
    conn.close()


def get_city_by_ip(ip):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM city WHERE ip = ?", (ip,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def save_weather(city, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO weather_snapshot (city, temp, feels_like, weather_text, wind_dir, wind_speed, humidity, visibility, cloud, obs_time)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            city,
            data.get("temp"),
            data.get("feelsLike"),
            data.get("text"),
            data.get("windDir"),
            data.get("windSpeed"),
            data.get("humidity"),
            data.get("vis"),
            data.get("cloud"),
            data.get("obsTime")
        )
    )
    conn.commit()
    conn.close()


def save_air(city, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO air_snapshot (city, aqi, category, pm2p5, pm10, so2, no2, co, o3, obs_time)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            city,
            data.get("aqi"),
            data.get("category"),
            data.get("pm2p5"),
            data.get("pm10"),
            data.get("so2"),
            data.get("no2"),
            data.get("co"),
            data.get("o3"),
            data.get("obsTime")
        )
    )
    conn.commit()
    conn.close()


def save_forecast_batch(city, forecast_list):
    conn = get_conn()
    cur = conn.cursor()
    for item in forecast_list:
        cur.execute(
            """INSERT OR REPLACE INTO forecast (city, date, temp_max, temp_min, humidity, weather_text, wind_dir, wind_speed, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                city,
                item.get("date"),
                item.get("temp_max"),
                item.get("temp_min"),
                item.get("humidity"),
                item.get("weather_text"),
                item.get("wind_dir"),
                item.get("wind_speed"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
    conn.commit()
    conn.close()


def get_forecast(city):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM forecast WHERE city = ? ORDER BY date", (city,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
