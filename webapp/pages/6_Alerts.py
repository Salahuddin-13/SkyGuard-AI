import sys
import os
import pandas as pd
from datetime import datetime
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import (
    apply_styling, STATIONS, fetch_all_stations, inject_fault, get_station_status, load_lstm_model, generate_explanation,
    status_badge, source_badge, severity_icon, STATUS_HEALTHY, STATUS_WARNING, STATUS_HIGH_RISK, STATUS_CRITICAL,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_HIGH, COLOR_CRITICAL, COLOR_OFFLINE, COLOR_INFO,
    SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM
)

st.set_page_config(page_title="Alert Center | SkyGuard AI", layout="wide")
apply_styling()

st.title("Alert Center")
st.markdown("##### Operational alert management and incident tracking")

# Initialize session states
if "faults" not in st.session_state:
    st.session_state.faults = {}
if "alert_lifecycle" not in st.session_state:
    st.session_state.alert_lifecycle = {}
if "event_log" not in st.session_state:
    st.session_state.event_log = []

def add_event(event_str, station, detail):
    st.session_state.event_log.append({
        "timestamp": datetime.now().isoformat(),
        "event": event_str,
        "station": station,
        "detail": detail
    })

# Fetch Data & Generate Alerts
with st.spinner("Fetching data and computing statuses..."):
    all_data = fetch_all_stations()
    model_info = load_lstm_model()
    
    # Apply faults if any
    for station_name, fault_type in st.session_state.faults.items():
        if station_name in all_data:
            all_data[station_name] = inject_fault(all_data[station_name], fault_type)
    
    # Compute statuses
    station_statuses = {}
    for station_name, data in all_data.items():
        station_statuses[station_name] = get_station_status(station_name, data, all_data, model_info)

# Process Alerts into lifecycle
current_alerts = []

for station_name, status in station_statuses.items():
    for alert in status["alerts"]:
        alert_id = f"{station_name}_{alert['type']}"
        
        # Add to lifecycle if new
        if alert_id not in st.session_state.alert_lifecycle:
            st.session_state.alert_lifecycle[alert_id] = {
                "state": "NEW",
                "timestamps": {"NEW": datetime.now().isoformat()},
                "notes": ""
            }
            add_event("Alert generated", station_name, f"{alert['type']}: {alert['detail']}")
            
        current_alerts.append({
            "id": alert_id,
            "station": station_name,
            "station_id": status["id"],
            "type": alert["type"],
            "severity": alert["severity"],
            "detail": alert["detail"],
            "layer": alert["layer"],
            "classification": status["explanation"]["classification"],
            "lifecycle": st.session_state.alert_lifecycle[alert_id],
            "reading": f"T: {status.get('temperature')} | P: {status.get('pressure')} | H: {status.get('humidity')}"
        })

tabs = st.tabs(["ACTIVE", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "ALL"])

def render_alert_card(alert):
    lifecycle = alert["lifecycle"]
    state = lifecycle["state"]
    alert_id = alert["id"]
    
    color_map = {
        SEV_CRITICAL: COLOR_CRITICAL,
        SEV_HIGH: COLOR_HIGH,
        SEV_MEDIUM: COLOR_WARNING
    }
    bcolor = color_map.get(alert["severity"], COLOR_INFO)
    
    html = f"""
    <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-left:4px solid {bcolor};border-radius:8px;padding:16px;margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <div style="font-weight:600;">{severity_icon(alert['severity'])} {alert['type']} - {alert['station']} ({alert['station_id']})</div>
            <div style="font-size:0.75rem;color:#6B7280;font-weight:bold;background:#F3F4F6;padding:2px 6px;border-radius:4px;">{state}</div>
        </div>
        <div style="font-size:0.85rem;color:#374151;margin-bottom:4px;"><b>Detail:</b> {alert['detail']}</div>
        <div style="font-size:0.85rem;color:#374151;margin-bottom:4px;"><b>Detection Layer:</b> {alert['layer']}</div>
        <div style="font-size:0.85rem;color:#374151;margin-bottom:4px;"><b>Classification:</b> {alert['classification']}</div>
        <div style="font-size:0.85rem;color:#374151;margin-bottom:12px;"><b>Observed:</b> {alert['reading']}</div>
        <div style="font-size:0.75rem;color:#9CA3AF;">Created: {lifecycle['timestamps'].get('NEW', '')[:19].replace('T', ' ')}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    
    # Actions
    col1, col2, col3 = st.columns([1,1,2])
    
    def transition(new_state):
        st.session_state.alert_lifecycle[alert_id]["state"] = new_state
        st.session_state.alert_lifecycle[alert_id]["timestamps"][new_state] = datetime.now().isoformat()
        add_event(f"Alert marked as {new_state}", alert["station"], alert["type"])
    
    with col1:
        if state == "NEW":
            if st.button("ACKNOWLEDGE", key=f"ack_{alert_id}"):
                transition("ACKNOWLEDGED")
                st.rerun()
        elif state == "ACKNOWLEDGED":
            if st.button("INVESTIGATE", key=f"inv_{alert_id}"):
                transition("INVESTIGATING")
                st.rerun()
        elif state == "INVESTIGATING":
            if st.button("RESOLVE", key=f"res_{alert_id}"):
                transition("RESOLVED")
                st.rerun()
                
    with col2:
        if state == "NEW":
            if st.button("INVESTIGATE", key=f"inv2_{alert_id}"):
                transition("INVESTIGATING")
                st.rerun()
        elif state in ["ACKNOWLEDGED", "INVESTIGATING"]:
            if st.button("RESOLVE", key=f"res2_{alert_id}"):
                transition("RESOLVED")
                st.rerun()
        
    with col3:
        if state in ["ACKNOWLEDGED", "INVESTIGATING"]:
            if st.button("MARK FALSE POSITIVE", key=f"fp_{alert_id}"):
                st.session_state.alert_lifecycle[alert_id]["notes"] += " [Marked False Positive]"
                transition("RESOLVED")
                st.rerun()
                
    # Operator Notes
    new_notes = st.text_input("Operator Notes", value=lifecycle.get("notes", ""), key=f"notes_{alert_id}", disabled=(state=="RESOLVED"))
    if new_notes != lifecycle.get("notes", ""):
        st.session_state.alert_lifecycle[alert_id]["notes"] = new_notes
        add_event("Notes updated", alert["station"], alert["type"])

for i, tab_state in enumerate(["ACTIVE", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "ALL"]):
    with tabs[i]:
        count = 0
        for alert in current_alerts:
            state = alert["lifecycle"]["state"]
            if tab_state == "ACTIVE" and state != "RESOLVED":
                render_alert_card(alert)
                count += 1
            elif tab_state == "ALL" or state == tab_state:
                render_alert_card(alert)
                count += 1
                
        if count == 0:
            st.info(f"No {tab_state.lower()} alerts.")

st.markdown("---")
st.markdown("##### Event Log")
if not st.session_state.event_log:
    st.info("No events recorded yet.")
else:
    log_events = st.session_state.event_log[-20:][::-1]
    for ev in log_events:
        st.markdown(f"<div style='font-size:0.85rem;margin-bottom:4px;padding:8px;background:#FFFBF5;border:1px solid #E5E7EB;border-radius:4px;'><span style='color:#6B7280;font-family:monospace;margin-right:8px;'>{ev['timestamp'][:19].replace('T', ' ')}</span> <b style='color:#111827'>{ev['event']}</b> <span style='color:#374151'>— {ev['station']}: {ev['detail']}</span></div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("##### Export")
export_data = []
for a in current_alerts:
    export_data.append({
        "Alert ID": a["id"],
        "Station": a["station"],
        "Type": a["type"],
        "State": a["lifecycle"]["state"],
        "Severity": a["severity"],
        "Classification": a["classification"],
        "Notes": a["lifecycle"]["notes"],
        "Created At": a["lifecycle"]["timestamps"].get("NEW", "")
    })

if export_data:
    df_export = pd.DataFrame(export_data)
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Export Alerts CSV",
        csv,
        "skyguard_alerts_export.csv",
        "text/csv"
    )
else:
    st.download_button("Export Alerts CSV", b"", "alerts.csv", disabled=True)
