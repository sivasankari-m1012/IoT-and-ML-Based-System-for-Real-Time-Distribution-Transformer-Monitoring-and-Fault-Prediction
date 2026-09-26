import streamlit as st
import pandas as pd
import os
import time

# ---------------- PAGE ----------------
st.set_page_config(
    page_title="Transformer Dashboard",
    layout="wide"
)

st.title("⚡ Smart Transformer Monitoring Dashboard")

# ---------------- CSV PATH ----------------
# This automatically finds data.csv in the SAME folder as this script,
# instead of a hardcoded path that only works on one computer.
# Make sure final.py sits in the same folder as main.py + data.csv.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file = os.path.join(BASE_DIR, "data.csv")

# ---------------- CHECK FILE ----------------
if os.path.exists(file):

    # READ CSV
    df = pd.read_csv(file)

    # ---------------- CHECK DATA ----------------
    if len(df) > 0:

        # CONVERT TO NUMERIC
        df["Temperature"] = pd.to_numeric(
            df["Temperature"],
            errors='coerce'
        )

        df["Voltage"] = pd.to_numeric(
            df["Voltage"],
            errors='coerce'
        )

        df["Current"] = pd.to_numeric(
            df["Current"],
            errors='coerce'
        )

        # ---------------- LATEST VALUES ----------------
        latest = df.iloc[-1]

        # ---------------- TOP CARDS ----------------
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "🌡 Temperature",
            f"{latest['Temperature']} °C"
        )

        col2.metric(
            "⚡ Voltage",
            f"{latest['Voltage']} V"
        )

        col3.metric(
            "🔌 Current",
            f"{latest['Current']} A"
        )

        col4.metric(
            "🛢 Oil %",
            f"{latest['Oil_Percentage']} %"
        )

        # ---------------- STATUS ----------------
        st.subheader("⚠️ Transformer Status")

        status = latest["Status"]

        if status == "FAULT":

            st.error("🚨 FAULT DETECTED")

        elif status == "OFF":

            st.warning("⚠️ POWER OFF")

        else:

            st.success("✅ NORMAL")

        # ---------------- ALERT SYSTEM ----------------
        if latest["Temperature"] > 60:
            st.error("🔥 HIGH TEMPERATURE ALERT")

        if latest["Voltage"] < 5:
            st.warning("⚡ LOW VOLTAGE ALERT")

        if latest["Oil_Percentage"] < 20:
            st.error("🛢 LOW OIL ALERT")

        # ---------------- LIVE GRAPHS ----------------
        st.subheader("📈 Voltage Graph")
        st.line_chart(df["Voltage"])

        st.subheader("📈 Current Graph")
        st.line_chart(df["Current"])

        st.subheader("📈 Temperature Graph")
        st.line_chart(df["Temperature"])

        # ---------------- TABLE ----------------
        st.subheader("📊 Latest Sensor Data")

        st.dataframe(
            df.tail(10),
            use_container_width=True
        )

    else:

        st.warning("CSV file empty")

else:

    st.warning("Waiting for sensor data...")

# ---------------- AUTO REFRESH ----------------
time.sleep(3)

st.rerun()