"""
SkyGuard AI — System & Hardware
System health, edge device info, and connectivity status.
"""
import sys, os
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import (
    apply_styling, load_lstm_model, load_training_report,
    STATIONS, SOURCE_OPENMETEO, SOURCE_HARDWARE,
    COLOR_HEALTHY, COLOR_OFFLINE, COLOR_WARNING,
)

st.set_page_config(page_title="System — SkyGuard AI", page_icon="⚙", layout="wide")
apply_styling()

model_info = load_lstm_model()
report = load_training_report()

st.markdown("""
<div style="margin-bottom:12px;">
    <span style="font-size:1.4rem;font-weight:700;color:#111827;">System Health</span><br>
    <span style="font-size:0.8rem;color:#6B7280;">Infrastructure, connectivity, and edge device status</span>
</div>
""", unsafe_allow_html=True)

# === SERVICE STATUS ===
st.markdown("##### Service Status")

services = [
    ("Open-Meteo Data Provider", "REST API", "✓ Connected", COLOR_HEALTHY, "https://api.open-meteo.com/v1/forecast"),
    ("LSTM Autoencoder", f"PyTorch · {report['lstm_ae']['total_params']:,} params" if report else "PyTorch",
     "✓ Loaded" if model_info and model_info.get("status") == "loaded" else "✗ Not loaded",
     COLOR_HEALTHY if model_info and model_info.get("status") == "loaded" else "#EF4444",
     "ml/models/lstm_ae_production.pt"),
    ("Rule Engine", "Deterministic", "✓ Active", COLOR_HEALTHY, "Built-in"),
    ("Physics Validator", "Magnus / Multivariate", "✓ Active", COLOR_HEALTHY, "Built-in"),
    ("Spatial Validator", f"{len(STATIONS)} stations", "✓ Active", COLOR_HEALTHY, "Built-in"),
    ("MQTT Broker", "Mosquitto", "○ Not connected — Prototype", COLOR_OFFLINE, "Planned: mosquitto:1883"),
    ("FastAPI Backend", "Python", "○ Not implemented — Prototype", COLOR_OFFLINE, "Planned: localhost:8000"),
    ("WebSocket", "Streamlit SSE", "○ Not implemented — Prototype", COLOR_OFFLINE, "Planned"),
    ("Database", "PostgreSQL / TimescaleDB", "○ Not implemented — Prototype", COLOR_OFFLINE, "Planned"),
]

for name, tech, status, color, endpoint in services:
    st.markdown(f"""
<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:6px;padding:10px 16px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 1px 2px rgba(0,0,0,0.03);">
    <div>
        <span style="font-weight:600;color:#111827;font-size:0.85rem;">{name}</span>
        <span style="color:#9CA3AF;font-size:0.75rem;margin-left:8px;">{tech}</span>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
        <span style="color:#9CA3AF;font-size:0.72rem;font-family:monospace;">{endpoint}</span>
        <span style="color:{color};font-weight:600;font-size:0.78rem;">{status}</span>
    </div>
</div>""", unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#E5E7EB;margin:20px 0 16px 0;"></div>', unsafe_allow_html=True)

# === HARDWARE / EDGE ===
st.markdown("##### Edge Hardware — Prototype Specification")
st.info("Hardware is designed but not connected to this dashboard prototype. The specifications below are from the selected components.")

h1, h2 = st.columns(2)

with h1:
    st.markdown("""
<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:6px;padding:16px;">
    <div style="font-weight:600;color:#111827;margin-bottom:8px;">ESP32 Microcontroller</div>
    <table style="width:100%;font-size:0.8rem;color:#374151;">
        <tr><td style="color:#6B7280;padding:3px 0;">MCU</td><td>Espressif ESP32-WROOM-32</td></tr>
        <tr><td style="color:#6B7280;padding:3px 0;">Clock</td><td>240 MHz dual-core Xtensa</td></tr>
        <tr><td style="color:#6B7280;padding:3px 0;">RAM</td><td>520 KB SRAM</td></tr>
        <tr><td style="color:#6B7280;padding:3px 0;">Connectivity</td><td>WiFi 802.11 b/g/n + Bluetooth 4.2</td></tr>
        <tr><td style="color:#6B7280;padding:3px 0;">Protocol</td><td>MQTT over WiFi</td></tr>
        <tr><td style="color:#6B7280;padding:3px 0;">Sampling</td><td>Every 5 seconds</td></tr>
        <tr><td style="color:#6B7280;padding:3px 0;">Cost</td><td>~₹399</td></tr>
        <tr><td style="color:#6B7280;padding:3px 0;">Status</td><td><span style="color:#6B7280;">○ Prototype — ordered, not connected</span></td></tr>
    </table>
</div>""", unsafe_allow_html=True)

with h2:
    st.markdown("""
<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:6px;padding:16px;">
    <div style="font-weight:600;color:#111827;margin-bottom:8px;">Sensors</div>
    <table style="width:100%;font-size:0.8rem;color:#374151;">
        <tr><td colspan="2" style="color:#111827;font-weight:600;padding:6px 0 3px 0;">BMP280 — Pressure & Temperature</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Range</td><td>300–1100 hPa, -40 to +85°C</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Accuracy</td><td>±1 hPa, ±1°C</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Interface</td><td>I²C (0x76/0x77)</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Cost</td><td>~₹39</td></tr>
        <tr><td colspan="2" style="color:#111827;font-weight:600;padding:8px 0 3px 0;">DHT22 — Humidity & Temperature</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Range</td><td>0–100% RH, -40 to +80°C</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Accuracy</td><td>±2% RH, ±0.5°C</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Interface</td><td>Digital one-wire (GPIO)</td></tr>
        <tr><td style="color:#6B7280;padding:2px 0;">Cost</td><td>~₹131</td></tr>
    </table>
</div>""", unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#E5E7EB;margin:20px 0 16px 0;"></div>', unsafe_allow_html=True)

# === STATION REGISTRY ===
st.markdown("##### Station Registry")
import pandas as pd
rows = []
for name, info in STATIONS.items():
    rows.append({
        "ID": info["id"],
        "Station": info["name"],
        "Full Name": name,
        "State": info.get("state", ""),
        "Lat": f"{info['lat']:.4f}",
        "Lon": f"{info['lon']:.4f}",
        "Elevation": f"{info.get('elevation_m', 0)} m",
        "Source": SOURCE_OPENMETEO,
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

st.caption("SkyGuard AI · SIH26073 · Ministry of Earth Sciences")
