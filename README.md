# Home Sensors – ML Monitoring Dashboard

This project was developed as a school project and demonstrates
how machine learning can be used to analyze sensor data from a smart home.

The system collects sensor data, applies anomaly detection, and visualizes
the results in an interactive Streamlit dashboard.

## Features
- Sensor data ingestion (temperature, humidity, gas, etc.)
- Machine Learning anomaly detection (Isolation Forest)
- Real-time visualization with Streamlit
- Historical data analysis
- Simple and clean dashboard UI

## Machine Learning
The project uses an **Isolation Forest** model to detect anomalies in sensor data.
The model is trained on historical readings and flags unusual behavior that
may indicate problems such as gas leaks or abnormal temperature changes.

## Tech Stack
- Python 3.10+
- Streamlit
- scikit-learn
- pandas
- matplotlib
- ESP32 (data source)
- SQLite / CSV (data storage)

## Project Structure
```text
home-sensors/
├── app.py              # Streamlit dashboard
├── ml/
│   ├── train.py        # Model training
│   └── isoforest.joblib
├── data/
│   └── sensor_data.csv
├── requirements.txt
└── README.md
