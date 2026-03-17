## **Problem Statement 4: AquaGuard – Water Leakage Detection System**

**Theme:** SDG 6 – Clean Water and Sanitation  
**Curriculum Focus:** Python Basics, Classes (OOP), Linear Search, Arithmetic Operations

### **The Mission**
Aging water infrastructure leads to billions of litres of clean water being lost every year through undetected pipe leaks and pressure failures. Cities cannot fix what they cannot see. Your challenge is to build **AquaGuard**, a Python-based monitoring system that simulates a city-wide network of water sensors and automatically flags leaks, pressure anomalies, and burst pipes before they cause major damage.

Using object-oriented programming, you must design a **Sensor class** that holds the state of each node in the network—including location, current flow rate, baseline average, and pressure reading. A linear search algorithm must scan all sensors and flag those showing critical deviations. The system should generate a readable maintenance alert identifying the exact sensor, its location, and the type of anomaly detected.

### **Dataset Requirements**
* Synthesize a dataset of **300–500 sensor readings** across different city zones.
* Include columns: `sensor_id`, `location_zone`, `flow_rate_lpm`, `baseline_mean`, `pressure_psi`.
* Ensure at least **5% of sensors** show anomalous readings (zero flow, extreme pressure) to test detection.

### **Sample Dataset Structure**
| sensor_id | location_zone | flow_rate_lpm | baseline_mean | pressure_psi |
| :--- | :--- | :--- | :--- | :--- |
| S_N_01 | Residential_A | 15.5 | 15.0 | 45 |
| S_N_02 | Industrial_B | 0.0 | 120.0 | 10 |
| S_S_05 | Commercial_C | 300.5 | 150.0 | 85 |

### **Test Cases & Validation**
1.  **Leak Detection:** If a sensor's `flow_rate_lpm` is $0.0$ while its `baseline_mean` is above $10.0$, flag it as a **Major Burst**.
2.  **Object Integrity:** Updating the flow rate of one Sensor object must have no effect on any other sensor instance.
3.  **Pressure Alert:** If `pressure_psi` exceeds $80$, the alert must include the percentage by which it exceeds the safety threshold.

### **Submission Guidelines**
* **Source Code:** A Python script defining a `Sensor` class with `check_status()` and `report_leak()` methods.
* **Output Files:** A `leak_report.txt` listing all flagged sensor IDs, their zones, and anomaly type.
* **Presentation:** A Design Thinking slide deck detailing your class structure and the environmental impact of early leak detection.
* **Visualization:** A bar chart comparing actual flow vs. baseline flow across city zones to highlight where water loss is highest.