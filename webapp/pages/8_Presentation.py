"""
SkyGuard AI — Presentation Mode
Optimized for SIH judging. Maximum visual impact, minimal noise.
"""
import sys, os
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import (
    apply_styling, STATIONS, fetch_all_stations, inject_fault,
    get_station_status, load_lstm_model, load_training_report,
    status_badge, source_badge,
    STATUS_HEALTHY, STATUS_WARNING, STATUS_HIGH_RISK, STATUS_CRITICAL,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_HIGH, COLOR_CRITICAL, COLOR_OFFLINE, COLOR_INFO,
    SOURCE_OPENMETEO,
)

st.set_page_config(page_title="SkyGuard AI — Presentation", page_icon="🛡", layout="wide")
apply_styling()

# Hide sidebar and reduce padding for presentation
st.markdown("""
<style>
    section[data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 1rem; padding-bottom: 0.5rem; max-width: 1400px; }
    header[data-testid="stHeader"] { display: none; }
</style>
""", unsafe_allow_html=True)

if "faults" not in st.session_state:
    st.session_state.faults = {}

model_info = load_lstm_model()
report = load_training_report()

with st.spinner("Loading..."):
    station_data = fetch_all_stations()

for name in list(station_data.keys()):
    if name in st.session_state.faults:
        orig = station_data[name].copy()
        station_data[name] = inject_fault(station_data[name], st.session_state.faults[name])
        station_data[name].update({"lat": orig["lat"], "lon": orig["lon"], "id": orig["id"],
                                   "hourly": orig.get("hourly", {}), "elevation_m": orig.get("elevation_m", 0)})

all_status = {}
for name, data in station_data.items():
    all_status[name] = get_station_status(name, data, station_data, model_info)

total = len(all_status)
healthy = sum(1 for s in all_status.values() if s["status"] == STATUS_HEALTHY)
warning = sum(1 for s in all_status.values() if s["status"] == STATUS_WARNING)
critical = sum(1 for s in all_status.values() if s["status"] in (STATUS_HIGH_RISK, STATUS_CRITICAL))
alerts = sum(s["alert_count"] for s in all_status.values())
now = datetime.now()

if critical > 0:
    sys_status, sys_color = "CRITICAL", COLOR_CRITICAL
elif warning > 0:
    sys_status, sys_color = "WARNING", COLOR_WARNING
else:
    sys_status, sys_color = "OPERATIONAL", COLOR_HEALTHY

model_loaded = model_info and model_info.get("status") == "loaded"

# === HEADER ===
st.markdown(f"""
<div style="text-align:center;padding:8px 0;">
    <div style="font-size:2rem;font-weight:800;color:#111827;letter-spacing:-0.02em;">SKYGUARD AI</div>
    <div style="font-size:0.9rem;color:#6B7280;margin-top:2px;">Environmental Intelligence & Early Warning Platform</div>
    <div style="font-size:0.8rem;color:#9CA3AF;margin-top:4px;">SIH26073 · Ministry of Earth Sciences · India Meteorological Department</div>
    <div style="margin-top:10px;">
        <span style="color:{sys_color};font-weight:700;font-size:1rem;">● SYSTEM {sys_status}</span>
        <span style="color:#9CA3AF;font-size:0.78rem;margin-left:16px;">Last sync: {now.strftime('%H:%M:%S IST')}</span>
        <span style="color:#9CA3AF;font-size:0.78rem;margin-left:16px;">Source: {SOURCE_OPENMETEO}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#D1D5DB;margin:12px 0;"></div>', unsafe_allow_html=True)

# === KPIs ===
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Stations", total)
k2.metric("Healthy", healthy)
k3.metric("Warning", warning)
k4.metric("Critical", critical)
k5.metric("Active Alerts", alerts)
k6.metric("Faults Injected", len(st.session_state.faults))

st.markdown('<div style="height:1px;background:#E5E7EB;margin:12px 0;"></div>', unsafe_allow_html=True)

# === MAP + ALERTS ===
try:
    import folium
    from streamlit_folium import st_folium

    map_col, info_col = st.columns([3, 2])

    with map_col:
        m = folium.Map(location=[22.0, 79.0], zoom_start=5, tiles='OpenStreetMap',
                       width='100%', height=400)

        for name, s in all_status.items():
            lat, lon = STATIONS[name]["lat"], STATIONS[name]["lon"]
            color_map = {STATUS_HEALTHY: "green", STATUS_WARNING: "#D97706",
                        STATUS_HIGH_RISK: "#EA580C", STATUS_CRITICAL: "red"}
            c = color_map.get(s["status"], "gray")
            radius = 12 if s["alert_count"] > 0 else 8

            t = f"{s['temperature']:.1f}" if s['temperature'] is not None else "—"
            p = f"{s['pressure']:.0f}" if s['pressure'] is not None else "—"
            h = f"{s['humidity']:.0f}" if s['humidity'] is not None else "—"

            popup_html = f"""
            <div style="font-family:Inter,sans-serif;min-width:180px;">
                <b>{STATIONS[name]['name']}</b> ({STATIONS[name]['id']})<br>
                <span style="color:{s['color']};font-weight:600;">{s['status'].replace('_',' ')}</span><br>
                <hr style="margin:4px 0;">
                Temp: {t} °C<br>
                Press: {p} hPa<br>
                RH: {h}%<br>
                Risk: {s['risk']['score']}/100<br>
                Source: {s['source']}
            </div>
            """

            folium.CircleMarker(
                [lat, lon], radius=radius, color=c, fill=True, fill_color=c, fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)

        st_folium(m, width=None, height=400, returned_objects=[])

    with info_col:
        st.markdown("##### Station Status")
        import pandas as pd
        rows = []
        for name, s in all_status.items():
            icon = {"HEALTHY": "✓", "WARNING": "!", "HIGH_RISK": "!!", "CRITICAL": "!!!"}.get(s["status"], "○")
            t = f"{s['temperature']:.1f}" if s['temperature'] is not None else "—"
            rows.append({
                "": icon,
                "Station": STATIONS[name]["name"],
                "Temp": t,
                "Risk": f"{s['risk']['score']}",
                "Alerts": s["alert_count"],
            })
        rows.sort(key=lambda r: int(r["Risk"]), reverse=True)
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=360)

except ImportError:
    st.warning("Folium not available. Install with: pip install folium streamlit-folium")

st.markdown('<div style="height:1px;background:#E5E7EB;margin:12px 0;"></div>', unsafe_allow_html=True)

# === DETECTION ENGINE + KEY STORY ===
e1, e2, e3, e4 = st.columns(4)

with e1:
    st.markdown(f"""
<div style="background:#FFF;border:1px solid #E5E7EB;border-top:3px solid {COLOR_HEALTHY};border-radius:6px;padding:12px;text-align:center;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;">Layer 1</div>
    <div style="font-weight:700;color:#111827;font-size:0.9rem;">Rule Engine</div>
    <div style="color:{COLOR_HEALTHY};font-size:0.78rem;">✓ Active</div>
</div>""", unsafe_allow_html=True)

with e2:
    ml_label = "LSTM" if model_loaded else "Z-score"
    ml_color = COLOR_HEALTHY if model_loaded else COLOR_WARNING
    st.markdown(f"""
<div style="background:#FFF;border:1px solid #E5E7EB;border-top:3px solid {ml_color};border-radius:6px;padding:12px;text-align:center;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;">Layer 2</div>
    <div style="font-weight:700;color:#111827;font-size:0.9rem;">{ml_label}</div>
    <div style="color:{ml_color};font-size:0.78rem;">{'✓ Model loaded' if model_loaded else '! Fallback'}</div>
</div>""", unsafe_allow_html=True)

with e3:
    st.markdown(f"""
<div style="background:#FFF;border:1px solid #E5E7EB;border-top:3px solid {COLOR_HEALTHY};border-radius:6px;padding:12px;text-align:center;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;">Layer 3</div>
    <div style="font-weight:700;color:#111827;font-size:0.9rem;">Physics</div>
    <div style="color:{COLOR_HEALTHY};font-size:0.78rem;">✓ Active</div>
</div>""", unsafe_allow_html=True)

with e4:
    params = f"{report['lstm_ae']['total_params']:,}" if report else "—"
    vloss = f"{report['lstm_ae']['best_val_loss']:.4f}" if report else "—"
    st.markdown(f"""
<div style="background:#FFF;border:1px solid #E5E7EB;border-top:3px solid {COLOR_INFO};border-radius:6px;padding:12px;text-align:center;">
    <div style="font-size:0.7rem;color:#6B7280;text-transform:uppercase;">Model</div>
    <div style="font-weight:700;color:#111827;font-size:0.9rem;">{params} params</div>
    <div style="color:{COLOR_INFO};font-size:0.78rem;">Val loss: {vloss}</div>
</div>""", unsafe_allow_html=True)

# === CORE VALUE PROPOSITION ===
st.markdown(f"""
<div style="text-align:center;padding:16px 0 8px 0;">
    <div style="display:inline-flex;gap:40px;align-items:center;">
        <div style="text-align:center;">
            <div style="font-size:1.4rem;font-weight:700;color:#059669;">DETECT</div>
            <div style="font-size:0.75rem;color:#6B7280;">3-layer analysis</div>
        </div>
        <div style="font-size:1.2rem;color:#D1D5DB;">→</div>
        <div style="text-align:center;">
            <div style="font-size:1.4rem;font-weight:700;color:#2563EB;">EXPLAIN</div>
            <div style="font-size:0.75rem;color:#6B7280;">Why the alert fired</div>
        </div>
        <div style="font-size:1.2rem;color:#D1D5DB;">→</div>
        <div style="text-align:center;">
            <div style="font-size:1.4rem;font-weight:700;color:#DC2626;">RESPOND</div>
            <div style="font-size:0.75rem;color:#6B7280;">Actionable guidance</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center;padding:4px 0 12px 0;font-size:0.75rem;color:#9CA3AF;">
    SkyGuard AI · {total} stations · Real-time Open-Meteo data · LSTM Autoencoder ({params} params) · Jena Climate trained · Spatial + Physics validation
</div>
""", unsafe_allow_html=True)
