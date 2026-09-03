# 🛡️ SkyGuard AI — Intelligent Real-Time Anomaly Detection for Automatic Weather Stations

> **Smart India Hackathon (SIH 2026)** | **Problem Statement:** SIH26073  
> **Organization:** Ministry of Earth Sciences / India Meteorological Department (IMD)  
> **Platform:** React 18 (TypeScript + Tailwind CSS) + FastAPI (WebSockets + PyTorch + Scikit-Learn)

---

## 🌟 Executive Summary

**SkyGuard AI** is an enterprise-grade environmental monitoring, sensor reliability, and anomaly detection platform designed for the India Meteorological Department's (IMD) nationwide network of Automatic Weather Stations (AWS). 

Traditional monitoring approaches rely either on naive thresholding (which fails during genuine convective storm fronts) or high-latency batch analytics. SkyGuard AI solves this with a **4-Layer Defense Architecture** that combines deterministic physical thermodynamics, geospatial barometric consensus, and a **Dual-ML Ensemble** (PyTorch LSTM Autoencoder + Scikit-Learn Isolation Forest) with $<12\text{ms}$ inference latency.

---

## 📐 System Architecture

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │           Pan-India IMD AWS Network (35 Stations)      │
                                  │      Open-Meteo REST + ESP32 Edge Hardware Telemetry   │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                                                              ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │                 SkyGuard Core Ingestion                │
                                  │         ThreadPoolExecutor Concurrency & Buffer        │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                    ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                    │                                                                                   │
                    ▼                                                                                   ▼
┌───────────────────────────────────────┐                                           ┌───────────────────────────────────────┐
│     Layer 1: Deterministic Rules      │                                           │       Layer 2: Dual ML Ensemble       │
│  - Altitude-Aware WMO Range Bounds    │                                           │  - PyTorch LSTM Autoencoder (57k par) │
│  - Instant Rate-of-Change (>6°C/hr)   │                                           │  - Scikit-Learn Isolation Forest (200t│
│  - Frozen Flatlines (std < 0.01)      │                                           │  - Station-Relative Dynamic Z-Scores  │
└───────────────────┬───────────────────┘                                           └───────────────────┬───────────────────┘
                    │                                                                                   │
                    └─────────────────────────────────────────┬─────────────────────────────────────────┘
                                                              │
                    ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                    │                                                                                   │
                    ▼                                                                                   ▼
┌───────────────────────────────────────┐                                           ┌───────────────────────────────────────┐
│     Layer 3: Thermodynamic Physics    │                                           │      Layer 4: Spatial Distance        │
│  - Magnus Dew-Point Law (Td <= Ta)    │                                           │  - Haversine Neighborhood (800km)     │
│  - Convective Storm Recognizer        │                                           │  - Barometric Sea-Level Reduction     │
│    (T↓, P↑, RH↑ = Real Weather Event) │                                           │  - Regional Sensor Consensus          │
└───────────────────┬───────────────────┘                                           └───────────────────┬───────────────────┘
                    │                                                                                   │
                    └─────────────────────────────────────────┬─────────────────────────────────────────┘
                                                              │
                                                              ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │       Root-Cause Explanation & Risk Scoring Engine     │
                                  │    Deterministic Risk Score (0-100) + English Action   │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                    ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                    │                                                                                   │
                    ▼                                                                                   ▼
┌───────────────────────────────────────┐                                           ┌───────────────────────────────────────┐
│     FastAPI Gateway & WebSockets      │                                           │      React 18 Enterprise Frontend     │
│  - REST Endpoints (/api/overview)     │ ◀═══════════════════════════════════════▶ │  - Real-Time Command Center & GIS Map │
│  - WebSocket Telemetry Pulse (/ws)    │                                           │  - Hardware Edge Console & Fault Lab  │
│  - Incident Lifecycle State Machine   │                                           │  - ML Intelligence & SIH Kiosk Mode   │
└───────────────────────────────────────┘                                           └───────────────────────────────────────┘
```

---

## 🧠 Dual Machine Learning Intelligence

SkyGuard AI implements an ensemble of complementary machine learning paradigms:

### 1. PyTorch Deep LSTM Autoencoder (`ml/models/lstm_ae_production.pt`)
- **Parameters**: `57,196` trainable weights across a 4-layer recurrent encoder-decoder.
- **Input Dimension**: `(batch_size, 60, 3)` representing 60 continuous time steps (5-day window) of $[T, P, RH]$.
- **Bottleneck**: Compressed 16-unit latent space.
- **Inference**: Computes mean squared reconstruction error against station-relative dynamic baseline ($\mu_{\text{history}}, \sigma_{\text{history}}$).
- **Threshold**: $2.50$ MSE. Outliers exceeding this threshold indicate severe temporal waveform degradation, phase shifts, or uncharacteristic diurnal anomalies.

### 2. Scikit-Learn Isolation Forest Ensemble (`ml/models/isolation_forest.joblib`)
- **Estimators**: `200` binary partition trees.
- **Training Corpus**: `100,000` continuous climate records from the Jena Climate Dataset.
- **Features**: 15 multi-sensor rolling statistical indicators:
  $$\text{Features} = [T_{\text{cur}}, \mu_T, \sigma_T, \Delta\mu_T, \Delta_{\text{step}}T, \quad P_{\text{cur}}, \mu_P, \sigma_P, \Delta\mu_P, \Delta_{\text{step}}P, \quad RH_{\text{cur}}, \mu_{RH}, \sigma_{RH}, \Delta\mu_{RH}, \Delta_{\text{step}}RH]$$
- **Inference**: Isolates instantaneous multivariate anomalies with high computational speed ($<2\text{ms}$).

---

## 🛰️ 35 Pan-India IMD Station Coverage

The platform continuously monitors 35 strategic automatic weather stations spanning all 6 meteorological zones of India:

1. **North**: Delhi (Safdarjung & Palam), Srinagar, Leh Ladakh ($3,514\text{m}$), Shimla ($2,205\text{m}$), Dehradun, Chandigarh, Amritsar, Jaipur, Lucknow, Varanasi.
2. **West & Central**: Mumbai (Colaba & Santa Cruz), Pune, Ahmedabad, Surat, Jodhpur, Bhopal, Nagpur, Panaji Goa.
3. **East & North-East**: Kolkata, Patna, Bhubaneswar, Ranchi, Raipur, Guwahati, Shillong ($1,525\text{m}$), Agartala.
4. **South & Island**: Bengaluru ($920\text{m}$), Chennai, Hyderabad, Visakhapatnam, Kochi, Thiruvananthapuram, Port Blair Andaman.

### Altitude-Aware Sea-Level Pressure Reduction
Because station elevations range from $6\text{m}$ (Chennai) to $3,514\text{m}$ (Leh Ladakh), raw barometric pressure differs by $>330\text{ hPa}$. SkyGuard normalizes all pressures using Laplace's barometric reduction formula:
$$P_0 = P \times \left(1 - \frac{0.0065 \cdot h}{T + 0.0065 \cdot h + 273.15}\right)^{-5.257}$$
This brings all 35 stations into a normalized regional range ($1005 - 1020\text{ hPa}$) for unbiased spatial consensus checks.

---

## 🔌 Dedicated Hardware & Edge Telemetry Ingestion

SkyGuard AI includes a dedicated **Hardware Edge Diagnostics Console** simulating edge-node sensor buses:

- **Edge Controller**: ESP32-WROOM-32D ($240\text{MHz}$ Dual Core, Wi-Fi $802.11\text{b/g/n}$, Bluetooth $4.2$).
- **Digital Barometer & Temperature**: Bosch Sensortec BMP280 ($0\text{x}76$ I2C bus at $400\text{kHz}$).
- **Digital Relative Humidity**: Aosong DHT22 (Single-Wire proprietary pulse protocol on GPIO4).
- **Physical Hardware Bill of Materials (BOM)**:
  - ESP32-WROOM-32D Development Board: $\text{₹ }320$
  - BMP280 Barometric Pressure & Temp Sensor Module: $\text{₹ }125$
  - DHT22 Capacitive Humidity Sensor: $\text{₹ }110$
  - Jumper Wires & Pull-Up Resistors ($4.7\text{k}\Omega$): $\text{₹ }27$
  - **Total Prototype Hardware Cost**: **$\text{₹ }582$**

### Edge Hardware Fault Sandbox:
1. `I2C Bus Lockup / Stall`: Simulates SCL line held LOW by slave device; flags I2C communication timeout.
2. `1-Wire Checksum Failure`: Simulates DHT22 CRC parity corruption.
3. `Wi-Fi RSSI Degradation & 85% Packet Drop`: Simulates RF antenna attenuation and transmission queue overflow.
4. `Power Brownout (<3.0V)`: Simulates battery rail voltage drop during monsoon overcast causing ADC voltage instability.

---

## 💻 React 18 Application Views

1. **Command Center**: Real-time KPI summary, station status grid, and active alert feed.
2. **Live Risk Map**: Leaflet GIS map with status-colored pulsing markers and 800km spatial radius inspector.
3. **Station Diagnostics (Deep Dive)**: Synchronized 24h multi-variable charts, Magnus dew-point curve, and data quality checklist.
4. **Fault Injection Lab**: Interactive 4-layer animated SVG pipeline, 4 fault scenarios (Spike, Freeze, Drift, Dropout), before/after JSON viewer, and **1-Click "▶ Run Complete SIH Demo"**.
5. **Hardware & Edge Ingestion**: ESP32 telemetry, hardware fault injection, and live UART/MQTT stream.
6. **Incident Command & Alert Center**: Operational lifecycle state machine (`New` $\rightarrow$ `Acknowledged` $\rightarrow$ `Investigating` $\rightarrow$ `Resolved`), operator notes, and CSV export.
7. **ML Model Intelligence**: Visual comparison of LSTM vs Isolation Forest, 50-epoch validation loss curve, and 15-feature importance table.
8. **Analytics & Reliability**: Station availability ($99.98\%$), mean detection latency ($<12\text{ms}$), prototype cost ($\text{₹ }582$), and zonal coverage distribution.
9. **Presentation Mode**: Fullscreen kiosk mode for SIH evaluators.

---

## 🚀 Quickstart Guide

### Prerequisites
- Node.js `v18+` & npm
- Python `3.10+` with PyTorch, Scikit-Learn, FastAPI, Uvicorn

### 1. Start Backend
```bash
# Install dependencies
pip install fastapi uvicorn torch scikit-learn numpy pandas requests joblib

# Launch FastAPI server on port 8000
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Frontend
```bash
cd frontend

# Install Node modules
npm install

# Start Vite dev server on port 3000
npm run dev -- --port 3000
```

Open `http://localhost:3000` in your web browser.

---

## 📋 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/overview` | `GET` | Returns full network snapshot, 35 stations, alerts, and KPIs |
| `/api/stations` | `GET` | Returns list of all 35 AWS stations |
| `/api/stations/{name}` | `GET` | Returns detailed 24h waveform and 4-layer diagnostics for one station |
| `/api/faults/inject` | `POST` | Injects meteorological fault (`spike`, `freeze`, `drift`, `dropout`) |
| `/api/faults/clear` | `POST` | Clears active faults and restores nominal telemetry |
| `/api/hardware/inject` | `POST` | Injects edge hardware fault (`i2c_bus_stall`, `dht22_crc_error`, `packet_loss`, `power_brownout`) |
| `/api/alerts/action` | `POST` | Updates alert state machine (`ACKNOWLEDGED`, `INVESTIGATING`, `RESOLVED`) |
| `/api/system/health` | `GET` | Returns status of all microservices, ML engines, and bridges |
| `/api/export/csv` | `GET` | Exports alerts and incident audit log as downloadable CSV |
| `/ws/telemetry` | `WebSocket` | Real-time 3-second streaming telemetry pulses |

---

## 🏆 Smart India Hackathon Presentation Workflow

For judges and evaluators, use the following demonstration flow:

1. **Step 1: Baseline Health** $\rightarrow$ Open **Command Center** and note that all 35 Pan-India stations are nominal ($100\%$ availability, $0$ false alarms).
2. **Step 2: GIS Spatial Context** $\rightarrow$ Open **Live Risk Map** and inspect the Himalayan stations (Leh Ladakh, Shimla) to verify altitude-adjusted barometric sea-level normalization.
3. **Step 3: Fault Injection** $\rightarrow$ Open **Fault Injection Lab**, select *Delhi (Safdarjung)*, and click **Inject Temperature Spike**. Observe Layer 1 rate jump, Layer 2 LSTM surge ($>2.50$), and instant plain-English root cause explanation.
4. **Step 4: Hardware vs Weather Disambiguation** $\rightarrow$ Open **Hardware & Edge Ingestion**, simulate an **I2C Bus Lockup**, and show how SkyGuard separates transducer electrical failures from convective storm fronts.
5. **Step 5: Incident Resolution** $\rightarrow$ Open **Alert Center**, acknowledge the incident, add operator triage notes, and transition to **Resolved**.
