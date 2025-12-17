import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd

# Set api url
API_URL = "http://0.0.0.0:50106"

# Set page configuration
st.set_page_config(page_title="IoT Dashboard", layout="wide")

# Auto refresh the page every minute
st_autorefresh(interval=60000, key="auto_refresh")

# Side selection
if "page" not in st.session_state:
    st.session_state.page = "home"

def go_home():
    st.session_state.page = "home"
    st.rerun()  # ← redirect instantly

def go_dashboard():
    st.session_state.page = "dashboard"
    st.rerun()  # ← redirect instantly

# Caching section
@st.cache_data(ttl=10)
def fetch_data(limit=200):
    resp = requests.get(f"{API_URL}/data?limit={limit}", verify=False)
    return resp.json()

# Fetch data 
data = fetch_data(200)
df = pd.DataFrame(data) if data else None
if df is not None and "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"])

########################################################
#                         HOME
########################################################
if st.session_state.page == "home":

    st.title("IoT Sensor System")

    st.header("Oversigt")

    # Check if dataframe contains data
    if df is None or df.empty:
        st.warning("Ingen data endnu…")
    else:
        latest = df.iloc[0]

        # Choose the color of the card
        def status_color(flag):
            return "#14da14" if flag == 0 else "#e61212"

        temp_color = status_color(latest.get("temp_flag", 0))
        hum_color = status_color(latest.get("hum_flag", 0))
        ratio_color = status_color(latest.get("ratio_flag", 0))
        
        # Make columns 
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style="padding:20px; border-radius:20px; background:{temp_color}; text-align:center;">
                <h2>Temperatur</h2>
                <h1>{latest['temp']:.1f}°C</h1>
                <p>{'Normal' if latest['temp_flag']==0 else 'Advarsel!'}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="padding:20px; border-radius:20px; background:{hum_color}; text-align:center;">
                <h2>Fugtighed</h2>
                <h1>{latest['hum']:.1f}%</h1>
                <p>{'Normal' if latest['hum_flag']==0 else 'Advarsel!'}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="padding:20px; border-radius:20px; background:{ratio_color}; text-align:center;">
                <h2>Kulilte Niveau</h2>
                <h1>{'Godt' if latest['ratio_flag']==0 else 'Advarsel!'}</h1>
                <p>{'Normal' if latest['ratio_flag']==0 else 'For højt'}</p>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Button to navigate to dashboard
    if st.button("📊 Åbn detaljeret dashboard"):
        go_dashboard()

    st.stop()

########################################################
#                       DASHBOARD
########################################################
if st.session_state.page == "dashboard":

    st.title("📊 Detaljeret Sensor Dashboard")

    if st.button("⬅️ Tilbage"):
        go_home()

    if df is None or df.empty:
        st.warning("Ingen data endnu…")
        st.stop()

    # Latest values
    st.subheader("Seneste målinger")
    st.dataframe(df.head(50))

    # Line graph
    st.subheader("Historik (Temp, Hum, Ratio)")
    st.line_chart(df[["temp", "hum", "ratio"]].tail(200))

    # Flags
    st.subheader("Individuelle sensor flags")
    flag_cols = ["temp_flag", "hum_flag", "ratio_flag", "anomaly"]
    existing = [c for c in flag_cols if c in df.columns]
    st.dataframe(df[existing].head(20))

    # Anomalier
    st.subheader("Registrerede Anomalier")
    anomalies = df[df["anomaly"] == 1]

    if anomalies.empty:
        st.success("Ingen anomalies registreret.")
    else:
        st.dataframe(anomalies.head(20)[[
            "timestamp", "temp", "hum", "ratio",
            "temp_flag", "hum_flag", "ratio_flag", "anomaly"
        ]])

    # Color codes
    def highlight_flags(row):
        color = "background-color: #ffcccc"
        normal = ""
        return [
            color if row["temp_flag"] else normal,
            color if row["hum_flag"] else normal,
            color if row["ratio_flag"] else normal,
            color if row["anomaly"] else normal,
        ]

    st.subheader("Visuel oversigt (Farvekodet)")
    st.dataframe(
        df[["temp_flag", "hum_flag", "ratio_flag", "anomaly"]].head(50)
        .style.apply(highlight_flags, axis=1)
    )