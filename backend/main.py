from fastapi import FastAPI
from pydantic import BaseModel
from backend.database import init_db, get_db
from backend import ml

# Initialize db
init_db()

# Set fastapi to app
app = FastAPI()

# Sensor data class
class SensorData(BaseModel):
    temp: float
    hum: float
    ratio: float

# Upload method, accept http post to /upload
@app.post("/upload")
def upload(data: SensorData):

    # Set db to variable
    db = get_db()
    cur = db.cursor()

    # Save raw data
    cur.execute(
        "INSERT INTO readings (temp, hum, ratio) VALUES (?, ?, ?)",
        (data.temp, data.hum, data.ratio)
    )
    db.commit()
    rowid = cur.lastrowid

    # ---------------- HARD RULES ----------------
    # Set flags based on custom rules if out of spectrum
    temp_flag = 1 if data.temp < 10 or data.temp > 35 else 0
    hum_flag  = 1 if data.hum < 20 or data.hum > 80 else 0

    # ---------------- ML ----------------
    # ML evaluates temp + hum + ratio individually if within spectrum
    ml_temp_flag = ml_hum_flag = ml_ratio_flag = 0
    if temp_flag == 0 and hum_flag == 0:
        try:
            ml_temp_flag, ml_hum_flag, ml_ratio_flag = ml.predict_single(
                (data.temp, data.hum, data.ratio)
            )
        except Exception as e:
            print("ML predict error:", e)

    # ---------------- FINAL ANOMALY ----------------
    # Hard rules OR ML anomaly
    final_anomaly = 1 if (
        temp_flag == 1 or
        hum_flag == 1 or
        ml_temp_flag == 1 or
        ml_hum_flag == 1 or
        ml_ratio_flag == 1
    ) else 0

    # Save the flags in db
    db.execute("""
        UPDATE readings
        SET temp_flag = ?, hum_flag = ?, ratio_flag = ?, anomaly = ?
        WHERE id = ?
    """, (
        temp_flag | ml_temp_flag,  # kombiner hard rule + ML
        hum_flag | ml_hum_flag,
        ml_ratio_flag,
        final_anomaly,
        rowid
    ))
    db.commit()

    # ---------------- TRAIN ML ----------------
    # Train model only on normal-spectrum data
    try:
        ml.train_model(min_rows=50)
    except Exception as e:
        print("ML train error:", e)

    db.close()

    return {
        "status": "ok",
        "temp_flag": temp_flag | ml_temp_flag,
        "hum_flag": hum_flag | ml_hum_flag,
        "ml_flag": ml_ratio_flag,
        "final_anomaly": final_anomaly
    }

# get data method, accept http get at /data
@app.get("/data")
def get_data(limit: int = 100):

    db = get_db()
    rows = db.execute(
        "SELECT * FROM readings ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    db.close()

    return [dict(r) for r in rows]
