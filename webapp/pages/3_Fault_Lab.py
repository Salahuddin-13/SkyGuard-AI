import sys, os
import json
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import (
    apply_styling, STATIONS, fetch_all_stations, inject_fault, 
    detect_anomalies, get_station_status, load_lstm_model, 
    get_layer_status, generate_explanation, compute_spatial_context, 
    magnus_dewpoint, status_badge, source_badge, severity_icon, 
    layer_badge, card_html, SOURCE_SIMULATION, COLOR_HEALTHY, 
    COLOR_CRITICAL, COLOR_WARNING, COLOR_INFO, COLOR_HIGH
)

st.set_page_config(page_title="Fault Lab | SkyGuard AI", layout="wide")
apply_styling()

if "faults" not in st.session_state:
    st.session_state.faults = {}

# 1. Header
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown("## Fault Injection Lab")
    st.markdown("<p style='color:#6B7280; font-size: 0.85rem;'>Simulate hardware failures and validate the 3-Layer Detection Engine in real-time.</p>", unsafe_allow_html=True)
with col_badge:
    st.markdown(f"<div style='text-align: right; margin-top: 10px;'>{source_badge(SOURCE_SIMULATION)}</div>", unsafe_allow_html=True)

# Fetch data and model
all_data_orig = fetch_all_stations()
model_info = load_lstm_model()

st.markdown("---")

# 2 & 3. Target Selection and Fault Injection
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("##### Target Station")
    station_names = list(STATIONS.keys())
    
    # Check if we need to auto-select Delhi for demo
    demo_mode = False
    if "demo_trigger" in st.session_state and st.session_state.demo_trigger:
        default_index = station_names.index("Delhi (Safdarjung)") if "Delhi (Safdarjung)" in station_names else 0
        st.session_state.demo_trigger = False
    else:
        default_index = 0
        
    selected_station = st.selectbox("Select a station to inject faults", station_names, index=default_index, label_visibility="collapsed")
    
    # Show station info card
    s_info = STATIONS[selected_station]
    
    active_fault = st.session_state.faults.get(selected_station)
    
    st.markdown(f"""
    <div style="background:#FFFBF5; border:1px solid #E5E7EB; border-radius:8px; padding:16px;">
        <div style="font-weight:600; font-size:1rem; color:#111827; margin-bottom:8px;">{s_info['full_name']}</div>
        <div style="font-size:0.78rem; color:#6B7280;">ID: {s_info['id']} | Elev: {s_info['elevation_m']}m</div>
        <div style="font-size:0.78rem; color:#6B7280;">Lat: {s_info['lat']} | Lon: {s_info['lon']}</div>
        <div style="margin-top:12px; font-size:0.85rem;">Active Fault: <b>{active_fault.upper() if active_fault else 'None'}</b></div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("##### Fault Scenarios")
    
    # 4 scenarios
    scenarios = [
        {"name": "SPIKE", "icon": "📈", "desc": "Temp +25°C", "layers": "Layer 1, Layer 2"},
        {"name": "FREEZE", "icon": "❄️", "desc": "All sensors = 0", "layers": "Layer 1"},
        {"name": "DRIFT", "icon": "〰️", "desc": "RH +30%", "layers": "Layer 1, Layer 2, Layer 3"},
        {"name": "DROPOUT", "icon": "🔌", "desc": "Null readings", "layers": "Layer 1"}
    ]
    
    cols = st.columns(4)
    for i, scen in enumerate(scenarios):
        with cols[i]:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:12px; text-align:center; height: 120px;">
                <div style="font-size:1.2rem; margin-bottom:4px;">{scen['icon']}</div>
                <div style="font-weight:600; font-size:0.85rem; color:#111827;">{scen['name']}</div>
                <div style="font-size:0.75rem; color:#6B7280; margin-top:2px;">{scen['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Inject", key=f"btn_{scen['name']}", use_container_width=True):
                st.session_state.faults[selected_station] = scen['name'].lower()
                st.rerun()
                
    st.markdown("<br>", unsafe_allow_html=True)
    bc1, bc2, bc3 = st.columns([1, 1, 2])
    with bc1:
        if st.button("Clear Station", use_container_width=True):
            if selected_station in st.session_state.faults:
                del st.session_state.faults[selected_station]
                st.rerun()
    with bc2:
        if st.button("Clear All", use_container_width=True):
            st.session_state.faults = {}
            st.rerun()
    with bc3:
        if st.button("▶ Run Complete Demo", type="primary", use_container_width=True):
            st.session_state.faults = {"Delhi (Safdarjung)": "spike"}
            st.session_state.demo_trigger = True
            st.rerun()

st.markdown("---")

# Prepare data for all to compute status correctly
all_data_injected = {}
for name, data in all_data_orig.items():
    if name in st.session_state.faults:
        all_data_injected[name] = inject_fault(data, st.session_state.faults[name])
    else:
        all_data_injected[name] = data

# 4. Detection Result
if active_fault:
    st.markdown("##### Detection Results")
    
    orig_data = all_data_orig[selected_station]
    inj_data = all_data_injected[selected_station]
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("###### Before (Healthy)")
        clean_orig = {"temperature": orig_data.get("temperature"), "pressure": orig_data.get("pressure"), "humidity": orig_data.get("humidity")}
        st.json(clean_orig)
    with c2:
        st.markdown("###### After (Fault Injected)")
        clean_inj = {"temperature": inj_data.get("temperature"), "pressure": inj_data.get("pressure"), "humidity": inj_data.get("humidity")}
        st.json(clean_inj)
        
    st.markdown("###### 3-Layer Verdict Panel")
    
    # Compute statuses
    status_info = get_station_status(selected_station, inj_data, all_data_injected, model_info)
    layer_status = status_info["layer_status"]
    
    def format_layer(layer_name, info):
        bg = "#FEF2F2" if info['status'] != "PASS" else "#F0FDF4"
        return f"""
        <div style="background:{bg}; border:1px solid {info['color']}; border-radius:8px; padding:12px; margin-bottom:8px; height: 100px;">
            <div style="font-weight:600; font-size:0.85rem; color:#111827;">{layer_name}</div>
            <div style="font-size:0.78rem; font-weight:600; color:{info['color']}; margin-top:4px;">{info['status']}</div>
            <div style="font-size:0.78rem; color:#6B7280; margin-top:2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{info['detail']}</div>
        </div>
        """
    
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        st.markdown(format_layer("Layer 1: Rule Engine", layer_status['layer1']), unsafe_allow_html=True)
    with l2:
        st.markdown(format_layer("Layer 2: LSTM/Z-score", layer_status['layer2']), unsafe_allow_html=True)
    with l3:
        st.markdown(format_layer("Layer 3: Physics", layer_status['layer3']), unsafe_allow_html=True)
    with l4:
        # Final Decision
        bg_dec = "#FEF2F2" if status_info['status'] in ["CRITICAL", "HIGH_RISK"] else "#F0FDF4"
        st.markdown(f"""
        <div style="background:{bg_dec}; border:1px solid {status_info['color']}; border-radius:8px; padding:12px; height: 100px;">
            <div style="font-weight:600; font-size:0.85rem; color:#111827; margin-bottom:8px;">Final Decision</div>
            <div>{status_badge(status_info['status'])}</div>
            <div style="font-size:0.78rem; color:#6B7280; margin-top:8px;">Risk Score: {status_info['risk']['score']}/100</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("###### Why This Alert Fired")
    exp = status_info["explanation"]
    
    reasons_html = "".join([f"<li>{r}</li>" for r in exp['reasons']])
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:16px; margin-bottom:16px;">
        <div style="font-size:0.85rem; color:#374151;">
            <b style="color:#111827;">Classification:</b> {exp['classification']}<br>
            <b style="color:#111827;">Conclusion:</b> {exp['conclusion']}<br>
            <b style="color:#111827;">Recommended Action:</b> {exp['recommended_action']}
        </div>
        <div style="font-size:0.85rem; color:#374151; margin-top:12px;">
            <b style="color:#111827;">Reasons:</b>
            <ul style="margin-top:4px; margin-bottom:0; padding-left:20px;">{reasons_html}</ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("###### Spatial Context")
    spatial = status_info["spatial"]
    if spatial.get("available"):
        con_color = COLOR_HEALTHY if spatial.get("overall_consistent") else COLOR_CRITICAL
        con_text = "Consistent" if spatial.get("overall_consistent") else "Inconsistent"
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:16px; font-size:0.85rem; color:#374151;">
            <b>Comparison with {spatial['nearby_count']} nearby stations:</b> <span style="color:{con_color}; font-weight:600;">{con_text}</span>
            <br><br>
            Regional Avg Temp: {spatial.get('temp_regional_avg', 'N/A')}°C | Deviation: {spatial.get('temp_deviation', 'N/A')}°C<br>
            Regional Avg Pres: {spatial.get('pres_regional_avg', 'N/A')} hPa | Deviation: {spatial.get('pres_deviation', 'N/A')} hPa<br>
            Regional Avg Hum: {spatial.get('hum_regional_avg', 'N/A')}% | Deviation: {spatial.get('hum_deviation', 'N/A')}%
        </div>
        """, unsafe_allow_html=True)

    # Detection Timeline
    from datetime import datetime as dt
    st.markdown("###### Detection Timeline")
    now_ts = dt.now().strftime("%H:%M:%S")
    
    timeline_events = [
        (f"{now_ts}.000", "Fault Injected", f"{active_fault.upper()} on {STATIONS[selected_station]['name']}", COLOR_WARNING),
    ]
    
    for a in status_info.get("alerts", []):
        layer = a.get("layer", "")
        if "Rule Engine" in layer:
            timeline_events.append((f"{now_ts}.001", "Layer 1 — Rule Engine", a.get("type", ""), COLOR_CRITICAL if a.get("severity") == "CRITICAL" else COLOR_WARNING))
        elif "LSTM" in layer or "Statistical" in layer:
            timeline_events.append((f"{now_ts}.002", "Layer 2 — ML Analysis", a.get("type", ""), COLOR_HIGH))
        elif "Physics" in layer:
            timeline_events.append((f"{now_ts}.003", "Layer 3 — Physics", a.get("type", ""), "#2563EB"))
    
    if status_info.get("spatial", {}).get("available"):
        sp_status = "Consistent" if status_info["spatial"].get("overall_consistent") else "Inconsistent"
        timeline_events.append((f"{now_ts}.004", "Spatial Validation", sp_status, COLOR_INFO))
    
    timeline_events.append((f"{now_ts}.005", "Alert Generated", f"Risk: {status_info['risk']['score']}/100 — {status_info['risk']['level']}", status_info["color"]))
    
    for ts, event, detail, color in timeline_events:
        st.markdown(f"""
<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:6px;">
    <div style="min-width:90px;font-family:monospace;font-size:0.75rem;color:#9CA3AF;padding-top:2px;">{ts}</div>
    <div style="width:8px;height:8px;border-radius:50%;background:{color};margin-top:6px;flex-shrink:0;"></div>
    <div>
        <span style="font-weight:600;font-size:0.82rem;color:#111827;">{event}</span>
        <span style="font-size:0.78rem;color:#6B7280;margin-left:8px;">{detail}</span>
    </div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# 6. Active Faults Table
st.markdown("##### Active Faults")
if st.session_state.faults:
    active_data = [{"Station": name, "Fault": fault.upper()} for name, fault in st.session_state.faults.items()]
    st.dataframe(active_data, use_container_width=True)
else:
    st.markdown("<div style='font-size:0.85rem; color:#6B7280;'>No active faults injected.</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 7. Educational Table
st.markdown("##### Educational Reference")
ref_data = [
    {"Fault Type": "SPIKE", "Description": "Sudden +25°C jump in temp", "Caught By": "Layer 1 (Rate, Range), Layer 2 (LSTM)"},
    {"Fault Type": "FREEZE", "Description": "All sensor values lock at 0", "Caught By": "Layer 1 (Frozen, Range)"},
    {"Fault Type": "DRIFT", "Description": "Gradual RH +30% offset", "Caught By": "Layer 2 (LSTM), Layer 3 (Physics - Dew Point)"},
    {"Fault Type": "DROPOUT", "Description": "Missing sensor data (Null)", "Caught By": "Layer 1 (Dropout)"},
]
st.dataframe(ref_data, use_container_width=True)
