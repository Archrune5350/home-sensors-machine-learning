import numpy as np
import joblib
from pathlib import Path
from backend.database import get_db

# Paths to ML models
MODEL_TEMP = Path(__file__).resolve().parent / "isoforest_temp.joblib"
MODEL_HUM  = Path(__file__).resolve().parent / "isoforest_hum.joblib"
MODEL_RATIO= Path(__file__).resolve().parent / "isoforest_ratio.joblib"

# ---------------- TRAIN MODELS ----------------
def train_model(min_rows=30):
    db = get_db()
    rows = db.execute("SELECT temp, hum, ratio FROM readings").fetchall()
    db.close()

    if len(rows) < min_rows:
        return False

    # convert data to numpy arrays
    data = np.array(rows, dtype=float)
    temp_data  = data[:,0].reshape(-1,1)  # Kun temp
    hum_data   = data[:,1].reshape(-1,1)  # Kun hum
    ratio_data = data[:,2].reshape(-1,1)  # Kun ratio

    from sklearn.ensemble import IsolationForest

    # Train and save temp model
    model_temp = IsolationForest(contamination=0.03, random_state=42)
    model_temp.fit(temp_data)
    joblib.dump(model_temp, MODEL_TEMP)

    # Train and save hum model
    model_hum = IsolationForest(contamination=0.03, random_state=42)
    model_hum.fit(hum_data)
    joblib.dump(model_hum, MODEL_HUM)

    # Train and save ratio model
    model_ratio = IsolationForest(contamination=0.03, random_state=42)
    model_ratio.fit(ratio_data)
    joblib.dump(model_ratio, MODEL_RATIO)

    return True

# ---------------- PREDICT SINGLE ----------------
def predict_single(record):
    temp, hum, ratio = record
    flags = []

    # Temp
    if MODEL_TEMP.exists():
        model_temp = joblib.load(MODEL_TEMP)
        pred_temp = model_temp.predict(np.array([[temp]]))
        flags.append(1 if pred_temp[0] == -1 else 0)
    else:
        flags.append(0)

    # Hum
    if MODEL_HUM.exists():
        model_hum = joblib.load(MODEL_HUM)
        pred_hum = model_hum.predict(np.array([[hum]]))
        flags.append(1 if pred_hum[0] == -1 else 0)
    else:
        flags.append(0)

    # Ratio
    if MODEL_RATIO.exists():
        model_ratio = joblib.load(MODEL_RATIO)
        pred_ratio = model_ratio.predict(np.array([[ratio]]))
        flags.append(1 if pred_ratio[0] == -1 else 0)
    else:
        flags.append(0)

    return tuple(flags)  # returnerer (temp_flag, hum_flag, ratio_flag)
