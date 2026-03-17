import streamlit as st
import random
import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt

# =========================
# Sensor Class (OOP)
# =========================
class Sensor:
    def __init__(self, sensor_id, location, flow_rate, baseline, pressure):
        self.sensor_id = sensor_id
        self.location = location
        self.flow_rate = flow_rate
        self.baseline = baseline
        self.pressure = pressure

    def check_status(self):
        anomalies = []

        if self.flow_rate == 0 and self.baseline > 10:
            anomalies.append("Major Leak")

        if self.pressure > 80:
            excess = ((self.pressure - 80) / 80) * 100
            anomalies.append(f"High Pressure ({excess:.1f}%)")

        if self.flow_rate < 0.5 * self.baseline and self.flow_rate != 0:
            anomalies.append("Low Flow")

        return anomalies

    def get_severity(self):
        score = 0

        if self.flow_rate == 0:
            score += 50
        elif self.flow_rate < 0.5 * self.baseline:
            score += 20

        if self.pressure > 80:
            score += (self.pressure - 80)

        return score


# =========================
# Dataset
# =========================
def generate_dataset(n=400):
    sensors = []
    zones = ["Residential_A", "Industrial_B", "Commercial_C", "Zone_D"]

    for i in range(n):
        sensor_id = f"S_{i:03}"
        location = random.choice(zones)

        baseline = random.uniform(10, 200)
        flow_rate = random.uniform(5, 250)
        pressure = random.uniform(20, 90)

        if random.random() < 0.05:
            flow_rate = 0

        if random.random() < 0.05:
            pressure = random.uniform(85, 120)

        sensors.append(Sensor(sensor_id, location, flow_rate, baseline, pressure))

    return sensors


# =========================
# Detection
# =========================
def detect_anomalies(sensors):
    records = []

    for s in sensors:  # Linear Search
        issues = s.check_status()
        severity = s.get_severity()

        records.append({
            "Sensor ID": s.sensor_id,
            "Zone": s.location,
            "Flow": round(s.flow_rate, 2),
            "Baseline": round(s.baseline, 2),
            "Pressure": round(s.pressure, 2),
            "Issues": ", ".join(issues) if issues else "Normal",
            "Severity": round(severity, 2)
        })

    return pd.DataFrame(records)


# =========================
# ML Detection
# =========================
def ml_detection(df):
    model = IsolationForest(contamination=0.05, random_state=42)

    X = df[["Flow", "Baseline", "Pressure"]]
    preds = model.fit_predict(X)

    df["ML Flag"] = preds
    df["ML Flag"] = df["ML Flag"].apply(lambda x: "Anomaly" if x == -1 else "Normal")

    return df


# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="AquaGuard", layout="wide")

st.title("💧 AquaGuard Smart Water Monitoring Dashboard")

st.sidebar.header("Controls")

num_sensors = st.sidebar.slider("Number of Sensors", 100, 500, 300)

if st.sidebar.button("Run Simulation 🚀"):

    sensors = generate_dataset(num_sensors)

    df = detect_anomalies(sensors)
    df = ml_detection(df)

    # Metrics
    total = len(df)
    rule_anomalies = len(df[df["Issues"] != "Normal"])
    ml_anomalies = len(df[df["ML Flag"] == "Anomaly"])

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Sensors", total)
    col2.metric("Rule-based Anomalies", rule_anomalies)
    col3.metric("ML Detected", ml_anomalies)

    st.subheader("📊 Sensor Data")
    st.dataframe(df)

    # Zone Analysis
    st.subheader("🚨 Zone Risk Analysis")
    zone_counts = df[df["Issues"] != "Normal"]["Zone"].value_counts()
    st.bar_chart(zone_counts)

    # Flow vs Baseline
    st.subheader("📈 Flow vs Baseline")
    zone_avg = df.groupby("Zone")[["Flow", "Baseline"]].mean()
    st.bar_chart(zone_avg)

    # High severity alerts
    st.subheader("🔥 Critical Alerts")
    critical = df[df["Severity"] > 50]
    st.dataframe(critical)

    # Download report
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Report", csv, "report.csv", "text/csv")

else:
    st.write("👈 Use the sidebar to run the simulation")