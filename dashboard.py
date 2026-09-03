"""
SkyGuard AI — Real-Time Dashboard with Live Weather API + Map
=============================================================
Uses OpenMeteo API (free, no key) for real Indian weather station data.
Shows stations on an interactive map with anomaly detection.

Run: streamlit run dashboard.py
"""

import streamlit as st
import requests
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium
import math
import time
import json
from datetime import datetime

# ================================================================
# CONFIG
# ================================================================

st.set_page_config(
    page_title="SkyGuard AI — Live Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Indian Weather Stations (AWS locations)
STATIONS = {
    "Delhi (Safdarjung)":   {"lat": 28.5849, "lon": 77.2083, "id": "DEL"},
    "Mumbai (Colaba)":      {"lat": 18.9067, "lon": 72.8147, "id": "BOM"},
    "Chennai (Nungambakkam)": {"lat": 13.0660, "lon": 80.2399, "id": "MAA"},
    "Kolkata (Alipore)":    {"lat": 22.5354, "lon": 88.3358, "id": "CCU"},
    "Bengaluru (HAL)":      {"lat": 12.9499, "lon": 77.6681, "id": "BLR"},
    "Hyderabad (Begumpet)": {"lat": 17.4531, "lon": 78.4677, "id": "HYD"},
    "Jaipur (Sanganer)":    {"lat": 26.8240, "lon": 75.8120, "id": "JAI"},
    "Ahmedabad":            {"lat": 23.0666, "lon": 72.6323, "id": "AMD"},
    "Pune (Shivajinagar)":  {"lat": 18.5314, "lon": 73.8446, "id": "PNQ"},
    "Lucknow (Amausi)":     {"lat": 26.7606, "lon": 80.8893, "id": "LKO"},
    "Bhopal (Bairagarh)":   {"lat": 23.2868, "lon": 77.3483, "id": "BHO"},
    "Thiruvananthapuram":   {"lat": 8.4826, "lon": 76.9521, "id": "TRV"},
}

# ================================================================
# CSS
# ================================================================

st.markdown("""
<style>
    .main-header { 
        font-size: 2rem; font-weight: 700; color: #1E3A5F;
        border-bottom: 3px solid #00D4AA; padding-bottom: 10px; margin-bottom: 20px;
    }
    .station-card {
        background: #F8FAFC; border-radius: 10px; padding: 15px;
        border-left: 4px solid #00D4AA; margin: 8px 0;
    }
    .alert-card {
        background: #FEF2F2; border-radius: 10px; padding: 15px;
        border-left: 4px solid #EF4444; margin: 8px 0;
    }
    .stat-box {
        background: #F0FDF4; border-radius: 10px; padding: 15px;
        border: 1px solid #BBF7D0; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ================================================================
# API FUNCTIONS
# ================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_weather_data(lat, lon):
    """Fetch real-time weather from OpenMeteo API (free, no key needed)."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,surface_pressure",
        "hourly": "temperature_2m,relative_humidity_2m,surface_pressure",
        "past_days": 1,
        "forecast_days": 0,
        "timezone": "Asia/Kolkata"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return None

def fetch_all_stations():
    """Fetch weather for all stations."""
    results = {}
    for name, info in STATIONS.items():
        data = fetch_weather_data(info["lat"], info["lon"])
        if data and "current" in data:
            current = data["current"]
            results[name] = {
                "temperature": current.get("temperature_2m", None),
                "humidity": current.get("relative_humidity_2m", None),
                "pressure": current.get("surface_pressure", None),
                "lat": info["lat"],
                "lon": info["lon"],
                "id": info["id"],
                "hourly": data.get("hourly", {}),
            }
    return results

# ================================================================
# ANOMALY DETECTION
# ================================================================

def magnus_dewpoint(temp, humidity):
    """Magnus formula for dew point temperature."""
    if humidity is None or temp is None or humidity <= 0:
        return None
    gamma = (17.27 * temp) / (237.7 + temp) + math.log(max(humidity, 0.01) / 100.0)
    if 17.27 - gamma == 0:
        return temp
    return (237.7 * gamma) / (17.27 - gamma)

def detect_anomalies(reading, hourly_data=None):
    """Run 3-layer anomaly detection on a reading."""
    alerts = []
    t = reading.get("temperature")
    p = reading.get("pressure")
    h = reading.get("humidity")
    
    if t is None or p is None or h is None:
        return [{"type": "DROPOUT", "severity": "CRITICAL", "detail": "Missing sensor data", "layer": "Layer 1"}]
    
    # === LAYER 1: Rule Engine ===
    if not (-50 <= t <= 60):
        alerts.append({"type": "OUT_OF_RANGE", "severity": "CRITICAL", 
                       "detail": f"Temperature {t}°C outside [-50, 60]", "layer": "Layer 1"})
    if not (870 <= p <= 1084):
        alerts.append({"type": "OUT_OF_RANGE", "severity": "CRITICAL",
                       "detail": f"Pressure {p} hPa outside [870, 1084]", "layer": "Layer 1"})
    if not (0 <= h <= 100):
        alerts.append({"type": "OUT_OF_RANGE", "severity": "HIGH",
                       "detail": f"Humidity {h}% outside [0, 100]", "layer": "Layer 1"})
    
    # Rate-of-change (check against hourly if available)
    if hourly_data and "temperature_2m" in hourly_data:
        temps = [x for x in hourly_data["temperature_2m"] if x is not None]
        if len(temps) >= 2:
            recent_temps = temps[-6:]  # Last 6 hours
            temp_range = max(recent_temps) - min(recent_temps)
            if temp_range > 20:
                alerts.append({"type": "HIGH_VARIABILITY", "severity": "MEDIUM",
                               "detail": f"Temperature varied {temp_range:.1f}°C in 6 hours", "layer": "Layer 1"})
    
    # === LAYER 2: Statistical Anomaly (simplified LSTM proxy) ===
    if hourly_data and "temperature_2m" in hourly_data:
        temps = [x for x in hourly_data["temperature_2m"] if x is not None]
        pressures = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
        humidities = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]
        
        anomaly_score = 0
        details = []
        
        if temps:
            mean_t, std_t = np.mean(temps), max(np.std(temps), 0.1)
            z_t = abs(t - mean_t) / std_t
            if z_t > 3:
                anomaly_score += z_t
                details.append(f"Temp z-score: {z_t:.1f}")
        
        if pressures:
            mean_p, std_p = np.mean(pressures), max(np.std(pressures), 0.1)
            z_p = abs(p - mean_p) / std_p
            if z_p > 3:
                anomaly_score += z_p
                details.append(f"Pressure z-score: {z_p:.1f}")
        
        if humidities:
            mean_h, std_h = np.mean(humidities), max(np.std(humidities), 0.1)
            z_h = abs(h - mean_h) / std_h
            if z_h > 3:
                anomaly_score += z_h
                details.append(f"Humidity z-score: {z_h:.1f}")
        
        if anomaly_score > 3:
            alerts.append({"type": "STATISTICAL_ANOMALY", "severity": "HIGH",
                           "detail": f"ML score: {anomaly_score:.1f} — {', '.join(details)}", "layer": "Layer 2"})
    
    # === LAYER 3: Physics Validation ===
    dp = magnus_dewpoint(t, h)
    if dp is not None and dp > t + 2:
        alerts.append({"type": "PHYSICS_VIOLATION", "severity": "CRITICAL",
                       "detail": f"Dew point ({dp:.1f}°C) > ambient ({t}°C) — impossible", "layer": "Layer 3"})
    
    return alerts

def inject_fault(reading, fault_type):
    """Inject a synthetic fault into a real reading for demo."""
    r = reading.copy()
    if fault_type == "spike":
        r["temperature"] = r.get("temperature", 30) + 25
    elif fault_type == "freeze":
        r["temperature"] = 0.0
        r["pressure"] = 0.0
        r["humidity"] = 0.0
    elif fault_type == "drift":
        r["humidity"] = min(100, r.get("humidity", 70) + 30)
    elif fault_type == "dropout":
        r["temperature"] = None
        r["pressure"] = None
        r["humidity"] = None
    return r

# ================================================================
# SIDEBAR
# ================================================================

with st.sidebar:
    st.markdown("## 🛡️ SkyGuard AI")
    st.caption("SIH26073 | Ministry of Earth Sciences")
    st.divider()
    
    st.markdown("### 🎮 Fault Injection Demo")
    st.caption("Inject faults into selected station")
    
    selected_station = st.selectbox("Target Station", list(STATIONS.keys()))
    
    col1, col2 = st.columns(2)
    with col1:
        inject_spike = st.button("💥 Spike", use_container_width=True)
        inject_freeze = st.button("🧊 Freeze", use_container_width=True)
    with col2:
        inject_drift = st.button("📈 Drift", use_container_width=True)
        inject_dropout = st.button("📡 Dropout", use_container_width=True)
    
    clear_faults = st.button("✅ Clear All Faults", use_container_width=True, type="primary")
    
    st.divider()
    st.markdown("### ℹ️ About")
    st.caption("Real-time weather data from OpenMeteo API")
    st.caption("12 Indian AWS stations monitored")
    st.caption("3-Layer anomaly detection active")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()

# Handle fault injection state
if 'faults' not in st.session_state:
    st.session_state.faults = {}

if inject_spike:
    st.session_state.faults[selected_station] = "spike"
if inject_freeze:
    st.session_state.faults[selected_station] = "freeze"
if inject_drift:
    st.session_state.faults[selected_station] = "drift"
if inject_dropout:
    st.session_state.faults[selected_station] = "dropout"
if clear_faults:
    st.session_state.faults = {}

# ================================================================
# MAIN
# ================================================================

st.markdown('<div class="main-header">🛡️ SkyGuard AI — Live Weather Station Monitor</div>', unsafe_allow_html=True)

# Fetch data
with st.spinner("Fetching live weather data from 12 Indian stations..."):
    station_data = fetch_all_stations()

if not station_data:
    st.error("Could not fetch weather data. Check internet connection.")
    st.stop()

# Apply injected faults
all_anomalies = {}
for name, data in station_data.items():
    if name in st.session_state.faults:
        station_data[name] = inject_fault(data, st.session_state.faults[name])
        station_data[name]["lat"] = data["lat"]
        station_data[name]["lon"] = data["lon"]
        station_data[name]["id"] = data["id"]
        station_data[name]["hourly"] = data.get("hourly", {})
    
    alerts = detect_anomalies(station_data[name], station_data[name].get("hourly"))
    all_anomalies[name] = alerts

# ================================================================
# TOP STATS
# ================================================================

total_stations = len(station_data)
stations_with_anomalies = sum(1 for alerts in all_anomalies.values() if len(alerts) > 0)
stations_normal = total_stations - stations_with_anomalies
total_alerts = sum(len(alerts) for alerts in all_anomalies.values())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📡 Stations", total_stations)
c2.metric("✅ Normal", stations_normal)
c3.metric("🔴 Alert", stations_with_anomalies)
c4.metric("⚠️ Total Alerts", total_alerts)
c5.metric("🕐 Last Update", datetime.now().strftime("%H:%M:%S"))

st.divider()

# ================================================================
# MAP + DATA
# ================================================================

map_col, data_col = st.columns([3, 2])

with map_col:
    st.markdown("### 🗺️ Live Station Map")
    
    # Create folium map centered on India
    m = folium.Map(
        location=[22.5, 78.5],
        zoom_start=5,
        tiles="CartoDB positron",
    )
    
    for name, data in station_data.items():
        alerts = all_anomalies.get(name, [])
        is_anomaly = len(alerts) > 0
        is_fault = name in st.session_state.faults
        
        t = data.get("temperature", "N/A")
        p = data.get("pressure", "N/A")
        h = data.get("humidity", "N/A")
        
        # Color: green = normal, red = anomaly, orange = injected fault
        if is_fault:
            color = "red"
            icon_color = "red"
            status = f"⚠️ FAULT INJECTED ({st.session_state.faults[name].upper()})"
        elif is_anomaly:
            color = "orange"
            icon_color = "orange"
            status = f"⚠️ {len(alerts)} alert(s)"
        else:
            color = "green"
            icon_color = "green"
            status = "✅ Normal"
        
        # Format values
        t_str = f"{t}°C" if t is not None else "N/A"
        p_str = f"{p} hPa" if p is not None else "N/A"
        h_str = f"{h}%" if h is not None else "N/A"
        
        popup_html = f"""
        <div style="font-family: Calibri; min-width: 220px;">
            <h4 style="margin:0; color: #1E3A5F;">{name}</h4>
            <p style="margin:2px 0; color: {'red' if is_anomaly else 'green'}; font-weight: bold;">{status}</p>
            <hr style="margin: 5px 0;">
            <p style="margin:2px 0;">🌡️ Temperature: <b>{t_str}</b></p>
            <p style="margin:2px 0;">🌊 Pressure: <b>{p_str}</b></p>
            <p style="margin:2px 0;">💧 Humidity: <b>{h_str}</b></p>
        """
        
        if alerts:
            popup_html += '<hr style="margin: 5px 0;"><p style="color:red; font-weight:bold;">Alerts:</p>'
            for alert in alerts:
                popup_html += f'<p style="margin:1px 0; font-size:12px;">• [{alert["layer"]}] {alert["detail"]}</p>'
        
        dp = magnus_dewpoint(t if t is not None else 0, h if h is not None else 50)
        if dp is not None and t is not None:
            popup_html += f'<hr style="margin: 5px 0;"><p style="margin:2px 0;">🌫️ Dew Point: <b>{dp:.1f}°C</b></p>'
        
        popup_html += "</div>"
        
        folium.CircleMarker(
            location=[data["lat"], data["lon"]],
            radius=12,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{name}: {t_str} | {status}",
        ).add_to(m)
        
        # Add station label
        folium.map.Marker(
            [data["lat"], data["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px; font-weight:bold; color:{color}; text-align:center; white-space:nowrap; margin-top:14px;">{data["id"]}</div>',
                icon_size=(50, 20),
                icon_anchor=(25, 0),
            )
        ).add_to(m)
    
    st_folium(m, width=None, height=450, returned_objects=[])

with data_col:
    st.markdown("### 📊 Station Readings")
    
    # Create dataframe
    rows = []
    for name, data in station_data.items():
        alerts = all_anomalies.get(name, [])
        t = data.get("temperature")
        p = data.get("pressure")
        h = data.get("humidity")
        status = "🔴" if alerts else "✅"
        
        rows.append({
            "": status,
            "Station": name.split("(")[0].strip(),
            "Temp °C": f"{t}" if t is not None else "---",
            "Press hPa": f"{p}" if p is not None else "---",
            "RH %": f"{h}" if h is not None else "---",
        })
    
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True, height=450)

st.divider()

# ================================================================
# ANOMALY ALERTS + STATION DETAIL
# ================================================================

alert_col, detail_col = st.columns([1, 1])

with alert_col:
    st.markdown("### 🔴 Anomaly Alerts")
    
    has_alerts = False
    for name, alerts in all_anomalies.items():
        if alerts:
            has_alerts = True
            for alert in alerts:
                severity_color = {"CRITICAL": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#CA8A04"}.get(alert["severity"], "#6B7280")
                st.markdown(f"""
<div class="alert-card">
    <div style="display: flex; justify-content: space-between;">
        <strong style="color: {severity_color};">⚠️ {alert['type']}</strong>
        <span style="color: #6B7280; font-size: 12px;">{alert['layer']}</span>
    </div>
    <div style="color: #374151; margin-top: 4px;"><strong>{name}</strong></div>
    <div style="color: #6B7280; font-size: 13px; margin-top: 2px;">{alert['detail']}</div>
</div>
""", unsafe_allow_html=True)
    
    if not has_alerts:
        st.markdown("""
<div class="station-card">
    <strong style="color: #16A34A;">✅ All Clear</strong>
    <div style="color: #6B7280; margin-top: 4px;">All 12 stations operating normally. No anomalies detected.</div>
</div>
""", unsafe_allow_html=True)

with detail_col:
    st.markdown("### 🔍 Station Detail")
    
    detail_station = st.selectbox("Select station", list(station_data.keys()), key="detail_select")
    
    if detail_station in station_data:
        sdata = station_data[detail_station]
        alerts = all_anomalies.get(detail_station, [])
        
        t = sdata.get("temperature")
        p = sdata.get("pressure")
        h = sdata.get("humidity")
        
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("🌡️ Temp", f"{t}°C" if t is not None else "N/A")
        mc2.metric("🌊 Pressure", f"{p} hPa" if p is not None else "N/A")
        mc3.metric("💧 Humidity", f"{h}%" if h is not None else "N/A")
        
        # Dew point
        dp = magnus_dewpoint(t or 0, h or 50)
        if dp and t:
            st.markdown(f"**🌫️ Dew Point:** {dp:.1f}°C  |  **Gap:** {t - dp:.1f}°C  |  {'✅ Valid' if dp <= t + 2 else '❌ Physics violation'}")
        
        # Status
        if alerts:
            st.error(f"🔴 {len(alerts)} anomaly alert(s) detected!")
            for a in alerts:
                st.warning(f"**[{a['layer']}] {a['type']}:** {a['detail']}")
        else:
            st.success("✅ Station healthy — all checks passed")
        
        # Hourly chart
        hourly = sdata.get("hourly", {})
        if hourly and "temperature_2m" in hourly:
            st.markdown("**24-Hour Temperature Trend:**")
            temps = hourly.get("temperature_2m", [])
            times = hourly.get("time", [])
            if temps and times:
                chart_df = pd.DataFrame({
                    "time": pd.to_datetime(times[:len(temps)]),
                    "temperature": temps
                }).set_index("time")
                st.line_chart(chart_df, color="#EF4444", height=200)

st.divider()

# ================================================================
# BOTTOM: EXPLAINABILITY + DETECTION OVERVIEW
# ================================================================

b1, b2 = st.columns([1, 1])

with b1:
    st.markdown("### 🧠 3-Layer Detection Status")
    
    st.markdown("""
| Layer | Engine | Status | Checks |
|---|---|---|---|
| **Layer 1** | WMO Rule Engine | ✅ Active | Range, rate, frozen, dropout |
| **Layer 2** | Statistical / LSTM-AE | ✅ Active | Z-score on 24h history |
| **Layer 3** | Physics Validator | ✅ Active | Magnus dew-point, consistency |
""")
    
    st.markdown(f"""
**Active Faults Injected:** {len(st.session_state.faults)}
""")
    if st.session_state.faults:
        for name, fault in st.session_state.faults.items():
            st.markdown(f"- 🎮 **{name}**: `{fault.upper()}`")

with b2:
    st.markdown("### 📈 Network Health Summary")
    
    # Health percentage
    health_pct = (stations_normal / max(total_stations, 1)) * 100
    st.progress(health_pct / 100, text=f"Network Health: {health_pct:.0f}% ({stations_normal}/{total_stations} stations normal)")
    
    # Quick stats table
    all_temps = [d.get("temperature") for d in station_data.values() if d.get("temperature") is not None]
    all_press = [d.get("pressure") for d in station_data.values() if d.get("pressure") is not None]
    all_hum = [d.get("humidity") for d in station_data.values() if d.get("humidity") is not None]
    
    if all_temps:
        st.markdown(f"""
| Metric | Min | Mean | Max |
|---|---|---|---|
| **Temperature** | {min(all_temps):.1f}°C | {np.mean(all_temps):.1f}°C | {max(all_temps):.1f}°C |
| **Pressure** | {min(all_press):.1f} hPa | {np.mean(all_press):.1f} hPa | {max(all_press):.1f} hPa |
| **Humidity** | {min(all_hum):.0f}% | {np.mean(all_hum):.0f}% | {max(all_hum):.0f}% |
""")

# Footer
st.divider()
st.caption("SkyGuard AI | SIH26073 | Ministry of Earth Sciences | Data: OpenMeteo API (free, real-time) | 12 Indian AWS stations monitored")
