"""
🌊 AquaGuard — Water Leakage Detection Dashboard
Streamlit application for monitoring city-wide water sensors.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import csv
import os

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
PRESSURE_SAFETY_THRESHOLD = 80
BASELINE_MIN = 10.0

ZONES = [
    "Residential_A", "Residential_B",
    "Industrial_A", "Industrial_B",
    "Commercial_A", "Commercial_B",
    "Municipal_A", "Downtown_A",
]

ZONE_PREFIXES = {
    "Residential_A": "S_RA", "Residential_B": "S_RB",
    "Industrial_A": "S_IA", "Industrial_B": "S_IB",
    "Commercial_A": "S_CA", "Commercial_B": "S_CB",
    "Municipal_A": "S_MA", "Downtown_A": "S_DA",
}

ZONE_FLOW_RANGES = {
    "Residential_A": (10, 30), "Residential_B": (10, 30),
    "Industrial_A": (80, 200), "Industrial_B": (80, 200),
    "Commercial_A": (40, 150), "Commercial_B": (40, 150),
    "Municipal_A": (20, 60), "Downtown_A": (30, 100),
}


# ─────────────────────────────────────────────
# Sensor Class (OOP)
# ─────────────────────────────────────────────
class Sensor:
    """Represents a single water-network sensor node."""

    def __init__(self, sensor_id, location_zone, flow_rate_lpm, baseline_mean, pressure_psi):
        self.sensor_id = sensor_id
        self.location_zone = location_zone
        self.flow_rate_lpm = float(flow_rate_lpm)
        self.baseline_mean = float(baseline_mean)
        self.pressure_psi = float(pressure_psi)

    def check_status(self):
        if self.flow_rate_lpm == 0.0 and self.baseline_mean > BASELINE_MIN:
            return "Major Burst"
        if self.pressure_psi > PRESSURE_SAFETY_THRESHOLD:
            return "Pressure Alert"
        return "Normal"

    def report_leak(self):
        status = self.check_status()
        if status == "Major Burst":
            return (
                f"🚨 MAJOR BURST  |  Sensor: {self.sensor_id}  |  "
                f"Zone: {self.location_zone}  |  "
                f"Flow: {self.flow_rate_lpm} LPM (baseline: {self.baseline_mean} LPM)  |  "
                f"Pressure: {self.pressure_psi} PSI"
            )
        if status == "Pressure Alert":
            pct = round(((self.pressure_psi - PRESSURE_SAFETY_THRESHOLD) / PRESSURE_SAFETY_THRESHOLD) * 100, 1)
            return (
                f"⚠️ PRESSURE ALERT  |  Sensor: {self.sensor_id}  |  "
                f"Zone: {self.location_zone}  |  "
                f"Pressure: {self.pressure_psi} PSI  |  "
                f"Exceeds safety threshold by {pct}%"
            )
        return f"✅ NORMAL  |  Sensor: {self.sensor_id}  |  Zone: {self.location_zone}"


# ─────────────────────────────────────────────
# Data Generation
# ─────────────────────────────────────────────
@st.cache_data
def generate_sensor_data(total=400, anomaly_pct=0.08, seed=42):
    random.seed(seed)
    data = []
    num_anomalies = int(total * anomaly_pct)
    num_bursts = num_anomalies // 2
    num_pressure = num_anomalies - num_bursts
    zone_counters = {z: 0 for z in ZONES}

    for i in range(total):
        zone = random.choice(ZONES)
        zone_counters[zone] += 1
        prefix = ZONE_PREFIXES[zone]
        sensor_id = f"{prefix}_{zone_counters[zone]:03d}"
        flow_min, flow_max = ZONE_FLOW_RANGES[zone]
        baseline = round(random.uniform(flow_min, flow_max), 1)

        if i < num_bursts:
            flow_rate = 0.0
            pressure = round(random.uniform(30, 70), 1)
        elif i < num_bursts + num_pressure:
            flow_rate = round(random.uniform(baseline * 0.8, baseline * 1.2), 1)
            pressure = round(random.uniform(81, 120), 1)
        else:
            flow_rate = round(random.uniform(baseline * 0.85, baseline * 1.15), 1)
            pressure = round(random.uniform(30, 75), 1)

        data.append({
            "sensor_id": sensor_id,
            "location_zone": zone,
            "flow_rate_lpm": flow_rate,
            "baseline_mean": baseline,
            "pressure_psi": pressure,
        })

    random.shuffle(data)
    return data


def classify_sensors(data):
    """Add status column to data."""
    results = []
    for row in data:
        s = Sensor(**row)
        status = s.check_status()
        exceed_pct = None
        if status == "Pressure Alert":
            exceed_pct = round(((s.pressure_psi - PRESSURE_SAFETY_THRESHOLD) / PRESSURE_SAFETY_THRESHOLD) * 100, 1)
        results.append({**row, "status": status, "exceed_pct": exceed_pct})
    return results


def build_report_text(df_flagged):
    """Generate the leak report as a string."""
    lines = []
    lines.append("=" * 72)
    lines.append("  AQUAGUARD — WATER LEAKAGE DETECTION REPORT")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Total Anomalies Found:  {len(df_flagged)}")
    lines.append("")
    lines.append("-" * 72)
    lines.append("")

    bursts = df_flagged[df_flagged["status"] == "Major Burst"]
    lines.append("🚨 MAJOR BURSTS")
    lines.append("-" * 36)
    if len(bursts):
        for _, r in bursts.iterrows():
            lines.append(
                f"  {r.sensor_id:<12} | {r.location_zone:<16} | "
                f"Flow: {r.flow_rate_lpm} LPM | Baseline: {r.baseline_mean} LPM | "
                f"Pressure: {r.pressure_psi} PSI"
            )
    else:
        lines.append("  (none detected)")

    lines.append("")
    pressures = df_flagged[df_flagged["status"] == "Pressure Alert"]
    lines.append("⚠️  PRESSURE ALERTS")
    lines.append("-" * 36)
    if len(pressures):
        for _, r in pressures.iterrows():
            lines.append(
                f"  {r.sensor_id:<12} | {r.location_zone:<16} | "
                f"Pressure: {r.pressure_psi} PSI | Exceeds by: {r.exceed_pct}%"
            )
    else:
        lines.append("  (none detected)")

    lines.append("")
    lines.append("=" * 72)
    lines.append("  END OF REPORT")
    lines.append("=" * 72)
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Page Config & Theme
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AquaGuard — Water Leak Detection",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    /* -- Global -- */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* -- KPI Cards -- */
    .kpi-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 24px 20px;
        text-align: center;
        backdrop-filter: blur(12px);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(52, 152, 219, 0.25);
    }
    .kpi-value {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 4px 0;
        background: linear-gradient(90deg, #3498db, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    .kpi-value.danger {
        background: linear-gradient(90deg, #e74c3c, #f39c12);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }

    /* -- Section headers -- */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ecf0f1;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(52, 152, 219, 0.4);
    }

    /* -- Sidebar -- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0c29 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #ecf0f1;
    }

    /* -- Tables -- */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Data Load
# ─────────────────────────────────────────────
raw_data = generate_sensor_data()
classified = classify_sensors(raw_data)
df = pd.DataFrame(classified)


# ─────────────────────────────────────────────
# Sidebar Filters
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌊 AquaGuard")
    st.markdown("**Water Leakage Detection System**")
    st.markdown("---")

    st.markdown("### 🔧 Filters")
    selected_zones = st.multiselect(
        "City Zones",
        options=sorted(df["location_zone"].unique()),
        default=sorted(df["location_zone"].unique()),
    )

    selected_status = st.multiselect(
        "Anomaly Type",
        options=["Normal", "Major Burst", "Pressure Alert"],
        default=["Normal", "Major Burst", "Pressure Alert"],
    )

    pressure_range = st.slider(
        "Pressure Range (PSI)",
        min_value=int(df["pressure_psi"].min()),
        max_value=int(df["pressure_psi"].max()),
        value=(int(df["pressure_psi"].min()), int(df["pressure_psi"].max())),
    )

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(
        "AquaGuard monitors city-wide water sensors "
        "and automatically flags leaks, pressure anomalies, "
        "and burst pipes."
    )
    st.markdown("**SDG 6** — Clean Water & Sanitation")

# Apply filters
mask = (
    df["location_zone"].isin(selected_zones)
    & df["status"].isin(selected_status)
    & df["pressure_psi"].between(pressure_range[0], pressure_range[1])
)
df_filtered = df[mask]


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown(
    "<h1 style='text-align:center; color:#ecf0f1; margin-bottom:0;'>"
    "🌊 AquaGuard Dashboard</h1>"
    "<p style='text-align:center; color:rgba(255,255,255,0.5); margin-top:4px;'>"
    "Real-time Water Leakage Detection &amp; Monitoring System</p>",
    unsafe_allow_html=True,
)
st.markdown("")


# ─────────────────────────────────────────────
# KPI Row
# ─────────────────────────────────────────────
total = len(df_filtered)
bursts_count = len(df_filtered[df_filtered["status"] == "Major Burst"])
pressure_count = len(df_filtered[df_filtered["status"] == "Pressure Alert"])
normal_count = len(df_filtered[df_filtered["status"] == "Normal"])
anomaly_rate = ((bursts_count + pressure_count) / total * 100) if total else 0

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Total Sensors</div>'
        f'<div class="kpi-value">{total}</div></div>',
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Major Bursts</div>'
        f'<div class="kpi-value danger">{bursts_count}</div></div>',
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Pressure Alerts</div>'
        f'<div class="kpi-value danger">{pressure_count}</div></div>',
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">Anomaly Rate</div>'
        f'<div class="kpi-value danger">{anomaly_rate:.1f}%</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("")


# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tab_data, tab_anomaly, tab_charts, tab_report, tab_drill = st.tabs([
    "📋 Sensor Data",
    "🚨 Anomaly Detection",
    "📊 Visualizations",
    "📝 Leak Report",
    "🔍 Sensor Drilldown",
])


# === Tab 1: Full data table ===
with tab_data:
    st.markdown('<div class="section-header">📋 Sensor Dataset</div>', unsafe_allow_html=True)

    # Colour-map for status
    def highlight_status(val):
        if val == "Major Burst":
            return "background-color: rgba(231,76,60,0.3); color: #e74c3c; font-weight: bold"
        elif val == "Pressure Alert":
            return "background-color: rgba(243,156,18,0.3); color: #f39c12; font-weight: bold"
        return "color: #2ecc71"

    styled = df_filtered.style.applymap(highlight_status, subset=["status"])
    st.dataframe(styled, use_container_width=True, height=480)
    st.caption(f"Showing {len(df_filtered)} of {len(df)} sensors (after filters)")


# === Tab 2: Anomaly detection ===
with tab_anomaly:
    st.markdown('<div class="section-header">🚨 Flagged Sensors</div>', unsafe_allow_html=True)

    df_flagged = df_filtered[df_filtered["status"] != "Normal"]

    if len(df_flagged) == 0:
        st.info("No anomalies found with current filters.")
    else:
        col_burst, col_pressure = st.columns(2)

        with col_burst:
            st.markdown("#### 🚨 Major Bursts")
            b = df_flagged[df_flagged["status"] == "Major Burst"][
                ["sensor_id", "location_zone", "flow_rate_lpm", "baseline_mean", "pressure_psi"]
            ]
            if len(b):
                st.dataframe(b, use_container_width=True, height=320)
            else:
                st.info("No burst anomalies in current view.")

        with col_pressure:
            st.markdown("#### ⚠️ Pressure Alerts")
            p = df_flagged[df_flagged["status"] == "Pressure Alert"][
                ["sensor_id", "location_zone", "pressure_psi", "exceed_pct"]
            ]
            if len(p):
                st.dataframe(p, use_container_width=True, height=320)
            else:
                st.info("No pressure anomalies in current view.")

        # Anomaly distribution pie
        st.markdown("")
        anomaly_counts = df_flagged["status"].value_counts().reset_index()
        anomaly_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(
            anomaly_counts,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map={
                "Major Burst": "#e74c3c",
                "Pressure Alert": "#f39c12",
            },
            title="Anomaly Distribution",
            hole=0.45,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ecf0f1",
        )
        st.plotly_chart(fig_pie, use_container_width=True)


# === Tab 3: Charts ===
with tab_charts:
    st.markdown('<div class="section-header">📊 Zone-wise Analysis</div>', unsafe_allow_html=True)

    # --- Chart 1: Actual vs Baseline flow ---
    zone_agg = (
        df_filtered.groupby("location_zone")
        .agg(avg_flow=("flow_rate_lpm", "mean"), avg_baseline=("baseline_mean", "mean"))
        .reset_index()
    )
    zone_agg["water_loss"] = zone_agg["avg_baseline"] - zone_agg["avg_flow"]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=zone_agg["location_zone"],
        y=zone_agg["avg_baseline"],
        name="Baseline Mean (LPM)",
        marker_color="#3498db",
    ))
    fig_bar.add_trace(go.Bar(
        x=zone_agg["location_zone"],
        y=zone_agg["avg_flow"],
        name="Actual Mean Flow (LPM)",
        marker_color="#e74c3c",
    ))
    fig_bar.update_layout(
        barmode="group",
        title="Actual Flow vs Baseline Flow by Zone",
        xaxis_title="City Zone",
        yaxis_title="Flow Rate (LPM)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ecf0f1",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig_bar.update_xaxes(showgrid=False)
    fig_bar.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Chart 2: Water Loss by Zone ---
    fig_loss = px.bar(
        zone_agg.sort_values("water_loss", ascending=False),
        x="location_zone",
        y="water_loss",
        color="water_loss",
        color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
        title="Water Loss by Zone (Baseline − Actual)",
        labels={"water_loss": "Water Loss (LPM)", "location_zone": "Zone"},
    )
    fig_loss.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ecf0f1",
    )
    fig_loss.update_xaxes(showgrid=False)
    fig_loss.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
    st.plotly_chart(fig_loss, use_container_width=True)

    # --- Chart 3: Pressure Distribution ---
    st.markdown('<div class="section-header">🔴 Pressure Distribution</div>', unsafe_allow_html=True)

    fig_pressure = px.scatter(
        df_filtered,
        x="sensor_id",
        y="pressure_psi",
        color="status",
        color_discrete_map={
            "Normal": "#2ecc71",
            "Major Burst": "#e74c3c",
            "Pressure Alert": "#f39c12",
        },
        title="Pressure Readings Across All Sensors",
        labels={"pressure_psi": "Pressure (PSI)", "sensor_id": "Sensor ID"},
        hover_data=["location_zone", "flow_rate_lpm", "baseline_mean"],
    )
    fig_pressure.add_hline(
        y=PRESSURE_SAFETY_THRESHOLD,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"Safety Threshold ({PRESSURE_SAFETY_THRESHOLD} PSI)",
        annotation_position="top left",
        annotation_font_color="#e74c3c",
    )
    fig_pressure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ecf0f1",
        xaxis=dict(showticklabels=False),
    )
    fig_pressure.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
    st.plotly_chart(fig_pressure, use_container_width=True)

    # --- Chart 4: Anomaly Count per Zone ---
    st.markdown('<div class="section-header">📍 Anomaly Heatmap by Zone</div>', unsafe_allow_html=True)

    zone_status = (
        df_filtered.groupby(["location_zone", "status"])
        .size()
        .reset_index(name="count")
    )
    fig_heat = px.bar(
        zone_status,
        x="location_zone",
        y="count",
        color="status",
        color_discrete_map={
            "Normal": "#2ecc71",
            "Major Burst": "#e74c3c",
            "Pressure Alert": "#f39c12",
        },
        title="Sensor Status Breakdown by Zone",
        barmode="stack",
    )
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ecf0f1",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig_heat.update_xaxes(showgrid=False)
    fig_heat.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
    st.plotly_chart(fig_heat, use_container_width=True)


# === Tab 4: Leak Report ===
with tab_report:
    st.markdown('<div class="section-header">📝 Leak Report</div>', unsafe_allow_html=True)

    df_all_flagged = df[df["status"] != "Normal"]
    report_text = build_report_text(df_all_flagged)

    st.code(report_text, language="text")

    col_dl1, col_dl2 = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            label="⬇️  Download Report",
            data=report_text,
            file_name="leak_report.txt",
            mime="text/plain",
        )
    with col_dl2:
        st.caption(
            f"Report contains {len(df_all_flagged)} flagged sensor(s) "
            f"out of {len(df)} total."
        )


# === Tab 5: Sensor Drilldown ===
with tab_drill:
    st.markdown('<div class="section-header">🔍 Sensor Drilldown</div>', unsafe_allow_html=True)

    sensor_ids = sorted(df_filtered["sensor_id"].unique())
    if sensor_ids:
        selected_id = st.selectbox("Select a Sensor ID", sensor_ids)
        row = df[df["sensor_id"] == selected_id].iloc[0]
        sensor_obj = Sensor(
            row["sensor_id"], row["location_zone"],
            row["flow_rate_lpm"], row["baseline_mean"], row["pressure_psi"],
        )
        status = sensor_obj.check_status()

        # Status badge colour
        badge_color = {"Normal": "#2ecc71", "Major Burst": "#e74c3c", "Pressure Alert": "#f39c12"}

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 16px;
                padding: 28px 32px;
                margin-top: 12px;
            ">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:18px;">
                    <span style="font-size:1.6rem; font-weight:800; color:#ecf0f1;">{row['sensor_id']}</span>
                    <span style="
                        background: {badge_color.get(status, '#95a5a6')};
                        color: #fff;
                        padding: 4px 14px;
                        border-radius: 20px;
                        font-size: 0.8rem;
                        font-weight: 700;
                    ">{status}</span>
                </div>
                <table style="width:100%; color:#bdc3c7; font-size:1rem;">
                    <tr><td style="padding:6px 0; color:rgba(255,255,255,0.5);">Zone</td>
                        <td style="padding:6px 0; font-weight:600; color:#ecf0f1;">{row['location_zone']}</td></tr>
                    <tr><td style="padding:6px 0; color:rgba(255,255,255,0.5);">Flow Rate</td>
                        <td style="padding:6px 0; font-weight:600; color:#ecf0f1;">{row['flow_rate_lpm']} LPM</td></tr>
                    <tr><td style="padding:6px 0; color:rgba(255,255,255,0.5);">Baseline Mean</td>
                        <td style="padding:6px 0; font-weight:600; color:#ecf0f1;">{row['baseline_mean']} LPM</td></tr>
                    <tr><td style="padding:6px 0; color:rgba(255,255,255,0.5);">Pressure</td>
                        <td style="padding:6px 0; font-weight:600; color:#ecf0f1;">{row['pressure_psi']} PSI</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("")
        st.markdown("**Alert Message:**")
        st.code(sensor_obj.report_leak(), language="text")
    else:
        st.warning("No sensors match the current filter selection.")


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:rgba(255,255,255,0.3); font-size:0.85rem;'>"
    "AquaGuard v1.0 — SDG 6: Clean Water &amp; Sanitation  •  "
    "Built with Python, Streamlit &amp; Plotly</p>",
    unsafe_allow_html=True,
)
