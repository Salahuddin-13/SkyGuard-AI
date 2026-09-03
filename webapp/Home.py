"""
SkyGuard AI — Command Center
Environmental Intelligence & Early Warning Platform
"""
import streamlit as st

st.set_page_config(
    page_title="SkyGuard AI — Command Center",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys, os, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    apply_styling, STATIONS, fetch_all_stations, detect_anomalies, inject_fault,
    load_lstm_model, load_training_report, get_station_status, compute_spatial_context,
    status_badge, source_badge, severity_icon,
    STATUS_HEALTHY, STATUS_WARNING, STATUS_HIGH_RISK, STATUS_CRITICAL,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_HIGH, COLOR_CRITICAL, COLOR_OFFLINE, COLOR_INFO,
    SOURCE_OPENMETEO,
)

apply_styling()

# Session state
if "faults" not in st.session_state:
    st.session_state.faults = {}
if "alerts_log" not in st.session_state:
    st.session_state.alerts_log = []

# Load model once
model_info = load_lstm_model()
training_report = load_training_report()

# === SIDEBAR ===
with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 8px 0;">
        <div style="font-size: 1.1rem; font-weight: 700; color: #F9FAFB; letter-spacing: -0.01em;">SKYGUARD AI</div>
        <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.05em;">Environmental Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # System health indicators
    st.markdown('<div style="font-size:0.7rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">System Status</div>', unsafe_allow_html=True)

    model_ok = model_info and model_info.get("status") == "loaded"
    st.markdown(f"""
    <div style="font-size: 0.78rem; line-height: 2;">
        <span style="color: #10B981;">●</span> Data Provider Connected<br>
        <span style="color: {'#10B981' if model_ok else '#EF4444'};">{'●' if model_ok else '○'}</span> {'LSTM Model Loaded' if model_ok else 'LSTM Model Unavailable'}<br>
        <span style="color: #6B7280;">○</span> MQTT — Not connected<br>
        <span style="color: #6B7280;">○</span> Hardware — Prototype
    </div>
    """, unsafe_allow_html=True)

# === FETCH DATA ===
with st.spinner("Fetching station data..."):
    station_data = fetch_all_stations()

if not station_data:
    st.error("Unable to reach data provider. Check internet connection.")
    st.stop()

# Apply faults
for name in list(station_data.keys()):
    if name in st.session_state.faults:
        orig = station_data[name].copy()
        station_data[name] = inject_fault(station_data[name], st.session_state.faults[name])
        station_data[name].update({"lat": orig["lat"], "lon": orig["lon"], "id": orig["id"],
                                   "hourly": orig.get("hourly", {}), "elevation_m": orig.get("elevation_m", 0)})

# Compute full status for all stations
all_status = {}
for name, data in station_data.items():
    all_status[name] = get_station_status(name, data, station_data, model_info)

# Aggregate
total = len(all_status)
healthy = sum(1 for s in all_status.values() if s["status"] == STATUS_HEALTHY)
warning = sum(1 for s in all_status.values() if s["status"] == STATUS_WARNING)
high_risk = sum(1 for s in all_status.values() if s["status"] == STATUS_HIGH_RISK)
critical = sum(1 for s in all_status.values() if s["status"] == STATUS_CRITICAL)
total_alerts = sum(s["alert_count"] for s in all_status.values())
active_faults = len(st.session_state.faults)
now = datetime.now()

# Determine system status
if critical > 0:
    sys_status = "CRITICAL"
    sys_color = COLOR_CRITICAL
elif high_risk > 0:
    sys_status = "DEGRADED"
    sys_color = COLOR_HIGH
elif warning > 0:
    sys_status = "WARNING"
    sys_color = COLOR_WARNING
else:
    sys_status = "OPERATIONAL"
    sys_color = COLOR_HEALTHY

# === TOP BAR ===
bar_left, bar_right = st.columns([2, 1])
with bar_left:
    st.markdown(f"""
    <div style="margin-bottom: 4px;">
        <span style="font-size: 1.4rem; font-weight: 700; color: #111827;">Command Center</span>
    </div>
    <div style="font-size: 0.8rem; color: #6B7280;">
        Environmental Early Warning & Sensor Reliability Platform
    </div>
    """, unsafe_allow_html=True)

with bar_right:
    source_label = SOURCE_OPENMETEO
    if active_faults > 0:
        source_label += " + Simulation"
    st.markdown(f"""
    <div style="text-align: right; font-size: 0.78rem;">
        <span style="color: {sys_color}; font-weight: 600;">● {sys_status}</span><br>
        <span style="color: #6B7280;">Last sync: {now.strftime('%H:%M:%S IST')} · Source: {source_label}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#E5E7EB;margin:12px 0;"></div>', unsafe_allow_html=True)

# === KPI ROW ===
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Stations", total)
k2.metric("Healthy", healthy, delta=None)
k3.metric("Warning", warning, delta=None)
k4.metric("Critical", critical, delta=None)
k5.metric("Active Alerts", total_alerts, delta=None)
k6.metric("Faults Injected", active_faults, delta=None)

# Health bar
health_pct = (healthy / max(total, 1)) * 100
st.progress(health_pct / 100, text=f"Network Health: {health_pct:.0f}% — {healthy}/{total} stations healthy")

# === MAIN CONTENT ===
left_col, right_col = st.columns([3, 2])

with left_col:
    st.markdown("##### Station Network")

    import pandas as pd
    rows = []
    for name, s in all_status.items():
        risk_score = s["risk"]["score"]
        t = s["temperature"]
        p = s["pressure"]
        h = s["humidity"]
        rows.append({
            "Status": {"HEALTHY": "✓", "WARNING": "!", "HIGH_RISK": "!!", "CRITICAL": "!!!", "OFFLINE": "○"}.get(s["status"], "?"),
            "Station": STATIONS[name]["name"],
            "Temp": f"{t:.1f} °C" if t is not None else "—",
            "Press": f"{p:.0f} hPa" if p is not None else "—",
            "RH": f"{h:.0f}%" if h is not None else "—",
            "Risk": f"{risk_score}/100",
            "Source": s["source"],
            "Alerts": s["alert_count"],
        })

    # Sort by risk (highest first)
    rows.sort(key=lambda r: int(r["Risk"].split("/")[0]), reverse=True)
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True, height=380)

with right_col:
    st.markdown("##### Active Alerts")

    has_any = False
    for name, s in all_status.items():
        for a in s["alerts"]:
            if a.get("type") == "METEOROLOGICAL_EVENT":
                continue
            has_any = True
            sev = a.get("severity", "")
            color = {"CRITICAL": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#D97706"}.get(sev, "#6B7280")
            st.markdown(f"""
<div style="background:#FFFFFF;border-left:3px solid {color};border:1px solid #E5E7EB;border-radius:6px;padding:10px 14px;margin-bottom:8px;box-shadow:0 1px 2px rgba(0,0,0,0.04);">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-weight:600;color:#111827;font-size:0.85rem;">{severity_icon(sev)} {a.get('type','')}</span>
        <span style="font-size:0.68rem;color:#6B7280;font-family:monospace;">{a.get('layer','')}</span>
    </div>
    <div style="color:#374151;font-size:0.78rem;margin-top:4px;">{STATIONS[name]['name']} — {a.get('detail','')[:100]}</div>
</div>""", unsafe_allow_html=True)

    if not has_any:
        st.markdown("""
<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:6px;padding:20px;text-align:center;">
    <div style="font-weight:600;color:#166534;">✓ All Clear</div>
    <div style="color:#6B7280;font-size:0.8rem;margin-top:4px;">All stations operating normally</div>
</div>""", unsafe_allow_html=True)

# === DETECTION ENGINE STATUS ===
st.markdown('<div style="height:1px;background:#E5E7EB;margin:16px 0 12px 0;"></div>', unsafe_allow_html=True)

st.markdown("##### Detection Engine")
e1, e2, e3, e4 = st.columns(4)

with e1:
    st.markdown(f"""
<div style="background:#FFFFFF;border-top:3px solid {COLOR_HEALTHY};border:1px solid #E5E7EB;border-radius:6px;padding:12px 16px;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.05em;">Layer 1</div>
    <div style="font-weight:600;color:#111827;margin-top:2px;">Rule Engine</div>
    <div style="color:{COLOR_HEALTHY};font-size:0.78rem;margin-top:4px;">✓ Active</div>
</div>""", unsafe_allow_html=True)

with e2:
    ml_label = "LSTM Autoencoder" if model_info and model_info.get("status") == "loaded" else "Z-score Proxy"
    ml_color = COLOR_HEALTHY if model_info and model_info.get("status") == "loaded" else COLOR_WARNING
    st.markdown(f"""
<div style="background:#FFFFFF;border-top:3px solid {ml_color};border:1px solid #E5E7EB;border-radius:6px;padding:12px 16px;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.05em;">Layer 2</div>
    <div style="font-weight:600;color:#111827;margin-top:2px;">{ml_label}</div>
    <div style="color:{ml_color};font-size:0.78rem;margin-top:4px;">{'✓ Model loaded' if ml_color == COLOR_HEALTHY else '! Fallback mode'}</div>
</div>""", unsafe_allow_html=True)

with e3:
    st.markdown(f"""
<div style="background:#FFFFFF;border-top:3px solid {COLOR_HEALTHY};border:1px solid #E5E7EB;border-radius:6px;padding:12px 16px;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.05em;">Layer 3</div>
    <div style="font-weight:600;color:#111827;margin-top:2px;">Physics Validator</div>
    <div style="color:{COLOR_HEALTHY};font-size:0.78rem;margin-top:4px;">✓ Active</div>
</div>""", unsafe_allow_html=True)

with e4:
    st.markdown(f"""
<div style="background:#FFFFFF;border-top:3px solid {COLOR_INFO};border:1px solid #E5E7EB;border-radius:6px;padding:12px 16px;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.05em;">Spatial</div>
    <div style="font-weight:600;color:#111827;margin-top:2px;">Neighbor Comparison</div>
    <div style="color:{COLOR_INFO};font-size:0.78rem;margin-top:4px;">✓ Active (12 stations)</div>
</div>""", unsafe_allow_html=True)

# === FOOTER ===
st.markdown('<div style="height:1px;background:#E5E7EB;margin:16px 0 8px 0;"></div>', unsafe_allow_html=True)
st.caption(f"SkyGuard AI · SIH26073 · Ministry of Earth Sciences · Data: Open-Meteo API · LSTM: {training_report['lstm_ae']['total_params']:,} params, val_loss={training_report['lstm_ae']['best_val_loss']:.4f}" if training_report else "SkyGuard AI · SIH26073")
