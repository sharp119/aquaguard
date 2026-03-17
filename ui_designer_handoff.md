# AquaGuard — Technical & Data Summary (UI Designer Handoff)

## Project Overview
AquaGuard is a data-driven dashboard for monitoring a city-wide water sensor network. Its primary purpose is to real-time process sensor telemetry to detect water leaks (bursts) and pressure anomalies, allowing city officials to quickly respond to infrastructure failures. 

This document outlines the underlying data structure, business logic, and functional requirements. **All visual styling is completely unopinionated — the goal is to design a professional, intuitive interface that accommodates these data points.**

---

## 1. Data Architecture

The application processes telemetry from **400 synthetic sensors** distributed across 8 city zones.

### Sensor Attributes
Every sensor provides the following data points:
*   `sensor_id` (String): e.g., `S_RA_001`
*   `location_zone` (String): One of 8 predefined categorical zones (e.g., `Residential_A`, `Industrial_B`).
*   `flow_rate_lpm` (Float): Current water flow in Litres Per Minute.
*   `baseline_mean` (Float): The historical normal flow rate for this specific sensor.
*   `pressure_psi` (Float): Current pipeline pressure in PSI.

### Business Logic & Status Calculation
Based on the incoming data, the backend automatically assigns one of three statuses to every sensor:
1.  **Major Burst (Critical):** Triggered when `flow_rate_lpm == 0.0` but the `baseline_mean > 10.0`.
2.  **Pressure Alert (Warning):** Triggered when `pressure_psi > 80.0` (The Safety Threshold).
3.  **Normal (Healthy):** Applied to all sensors that do not meet the anomaly conditions above.

*(Roughly 8% of the data points will be anomalous at any given time).*

---

## 2. Functional UI Requirements

The interface must support the following functional modules/views. The current implementation uses a Sidebar and Tabs, but the layout is entirely open to redesign.

### A. Global Filters
Users must be able to filter the entire dashboard by:
*   **City Zones:** Checkbox/Multiselect.
*   **Anomaly Type:** Normal, Major Burst, Pressure Alert.
*   **Pressure Range:** A dual-ended slider (Numerical from min to max PSI).

### B. High-Level KPIs (Key Performance Indicators)
A summary view showing aggregated metrics based on the current filters:
1.  **Total Sensors** (Count)
2.  **Major Bursts** (Count of critical anomalies)
3.  **Pressure Alerts** (Count of warning anomalies)
4.  **Anomaly Rate** (Percentage: `[Total Anomalies / Total Sensors] * 100`)

### C. Detailed Data Views
1.  **Raw Sensor Dataset:** A searchable, sortable table displaying all active sensors and their 5 attributes + their calculated [status](file:///Users/adityapaswan/soup/projects/aquaguard/app.py#55-61).
2.  **Flagged Anomalies:** A filtered view showing *only* the anomalous sensors. Ideally split to show Bursts and Pressure Alerts distinctly.
3.  **Sensor Drilldown:** A focused view where a user can select a specific `sensor_id` and see a detailed card of its metrics and a generated alert message (e.g., *"⚠️ PRESSURE ALERT | Exceeds safety threshold by X%"*).

### D. Required Data Visualizations
The dashboard must represent the following data relationships visually (currently using Plotly):
1.  **Anomaly Distribution:** A breakdown of anomaly types (e.g., a pie or donut chart showing Bursts vs. Alerts).
2.  **Actual vs. Baseline Flow by Zone:** Comparing expected water flow against actual flow aggregated by city zone. 
3.  **Water Loss by Zone:** Charting the calculated variance (`baseline_mean` minus `flow_rate_lpm`) across zones.
4.  **Pressure Distribution:** A scatter plot mapping all sensors' pressure readings, highlighting which sensors cross the static **80 PSI safety threshold line**.
5.  **Sensor Status Breakdown:** A stacked bar chart showing the composition of healthy vs. anomalous sensors within each of the 8 zones.

### E. Export Functionality
*   **Leak Report:** A text-based summary of all anomalies that users can preview and download as [.txt](file:///Users/adityapaswan/soup/projects/aquaguard/requirements.txt) or `.csv`. 

---

## Design Goals
*   The data needs to be easily scanable by municipal workers.
*   Critical alerts (Major Bursts) must draw immediate attention over warnings (Pressure) and normal states.
*   The transition between high-level overviews (KPIs, Charts) and deep-dive investigations (Sensor Drilldown, Data tables) must feel seamless.
