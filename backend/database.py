import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sensor_data.db"

def get_db():
    connect = sqlite3.connect(DB_PATH)
    connect.row_factory = sqlite3.Row
    return connect

def init_db():
    connect = get_db()
    connect.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        temp REAL,
        hum REAL,
        ratio REAL,
        temp_flag INTEGER DEFAULT 0,
        hum_flag INTEGER DEFAULT 0,
        ratio_flag INTEGER DEFAULT 0,
        anomaly INTEGER DEFAULT 0
    )
    """)
    connect.execute("""
    CREATE TABLE IF NOT EXISTS model_store (
        name TEXT PRIMARY KEY,
        blob BLOB
    )
    """)
    connect.commit()
    connect.close()
