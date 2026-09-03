import sys
import os
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

st.set_page_config(page_title='Live Map', page_icon='map', layout='wide')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import (
    apply_styling, STATIONS, fetch_all_stations, inject_fault, get_station_status, 
    load_lstm_model, status_badge, source_badge, severity_icon, 
    COLOR_HEALTHY, COLOR_WARNING, COLOR_HIGH, COLOR_CRITICAL, COLOR_OFFLINE, 
    STATUS_HEALTHY, STATUS_WARNING, STATUS_HIGH_RISK, STATUS_CRITICAL
)

apply_styling()

st.title("Live Station Map")
st.markdown("##### Real-time geographic monitoring of 12 Indian AWS stations")

if 'faults' not in st.session_state:
    st.session_state.faults = {}

model_info = load_lstm_model()
raw_data = fetch_all_stations()
all_data = {}

for s_name, s_data in raw_data.items():
    if s_name in st.session_state.faults:
        all_data[s_name] = inject_fault(s_data, st.session_state.faults[s_name])
    else:
        all_data[s_name] = s_data

statuses = {}
for s_name, s_data in all_data.items():
    statuses[s_name] = get_station_status(s_name, s_data, all_data, model_info)

# Metrics
total_stations = len(statuses)
healthy_count = sum(1 for s in statuses.values() if s["status"] == STATUS_HEALTHY)
warn_crit_count = sum(1 for s in statuses.values() if s["status"] in [STATUS_WARNING, STATUS_HIGH_RISK, STATUS_CRITICAL])
active_faults = len(st.session_state.faults)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Stations", total_stations)
c2.metric("Healthy", healthy_count)
c3.metric("Warning/Critical", warn_crit_count)
c4.metric("Active Faults", active_faults)

col1, col2 = st.columns([3, 2])

with col1:
    m = folium.Map(location=[22.0, 79.0], zoom_start=5, tiles='OpenStreetMap')
    
    for s_name, s_obj in statuses.items():
        lat = all_data[s_name]["lat"]
        lon = all_data[s_name]["lon"]
        color = s_obj["color"]
        radius = 13 if s_obj["alert_count"] > 0 else 10
        
        spatial = s_obj.get("spatial", {})
        if spatial.get("available") and "temp_regional_avg" in spatial:
            spatial_str = f"Regional avg: {spatial['temp_regional_avg']}°C, Deviation: {spatial.get('temp_deviation', 0):+g}°C"
        else:
            spatial_str = "N/A"
            
        issues_html = ""
        if s_obj["alerts"]:
            issues_list = "".join([f"<li style='margin-bottom:4px;font-size:0.85rem;'>{severity_icon(a.get('severity'))} {a['detail']}</li>" for a in s_obj['alerts']])
            issues_html = f"<div style='margin-top:8px;'><b>Active Issues:</b><ul style='padding-left:20px;margin-top:4px;'>{issues_list}</ul></div>"
        
        popup_html = f"""
        <div style="font-family: 'Inter', sans-serif; min-width: 240px; padding: 4px;">
            <div style="margin-bottom: 8px;">
                <h4 style="margin: 0 0 4px 0; color: #111827;">{s_name} ({s_obj['id']})</h4>
                {status_badge(s_obj['status'])}
            </div>
            <div style="font-size: 0.85rem; color: #374151;">
                <b>Readings:</b><br>
                Temp: {s_obj['temperature']} °C<br>
                Pressure: {s_obj['pressure']} hPa<br>
                Humidity: {s_obj['humidity']} %<br>
            </div>
            <div style="margin: 8px 0;">{source_badge(s_obj['source'])}</div>
            <div style="font-size: 0.85rem; color: #374151;">
                <b>Spatial Context:</b> {spatial_str}
            </div>
            {issues_html}
        </div>
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=320)
        ).add_to(m)
        
    legend_html = f'''
         <div style="position: fixed; 
         bottom: 20px; left: 20px; width: 130px; height: auto; 
         border: 1px solid #E5E7EB; z-index:9999; font-size:12px;
         background-color: #FFFBF5;
         padding: 10px;
         border-radius: 8px;
         box-shadow: 0 2px 4px rgba(0,0,0,0.1);
         font-family: 'Inter', sans-serif;">
         <div style="font-weight: 600; margin-bottom: 6px;">Status Legend</div>
         <div style="display:flex; align-items:center; margin-bottom:4px;">
             <i style="background:{COLOR_HEALTHY};border-radius:50%;width:10px;height:10px;margin-right:6px;"></i> Healthy
         </div>
         <div style="display:flex; align-items:center; margin-bottom:4px;">
             <i style="background:{COLOR_WARNING};border-radius:50%;width:10px;height:10px;margin-right:6px;"></i> Warning
         </div>
         <div style="display:flex; align-items:center; margin-bottom:4px;">
             <i style="background:{COLOR_HIGH};border-radius:50%;width:10px;height:10px;margin-right:6px;"></i> High Risk
         </div>
         <div style="display:flex; align-items:center;">
             <i style="background:{COLOR_CRITICAL};border-radius:50%;width:10px;height:10px;margin-right:6px;"></i> Critical
         </div>
         </div>
         '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    st_folium(m, width="100%", height=500, returned_objects=[])

with col2:
    df_data = []
    for s_name, s_obj in statuses.items():
        icon = {
            "HEALTHY": "🟢", 
            "WARNING": "🟡", 
            "HIGH_RISK": "🟠", 
            "CRITICAL": "🔴", 
            "OFFLINE": "⚫"
        }.get(s_obj["status"], "⚫")
        df_data.append({
            "Status": icon,
            "Station": s_name,
            "Temp": f"{s_obj['temperature']}°C" if s_obj['temperature'] is not None else "N/A",
            "Press": f"{s_obj['pressure']}hPa" if s_obj['pressure'] is not None else "N/A",
            "RH": f"{s_obj['humidity']}%" if s_obj['humidity'] is not None else "N/A",
            "Risk": s_obj['risk']['score'],
            "Source": s_obj['source'],
            "Alerts": s_obj['alert_count'],
        })
    df = pd.DataFrame(df_data)
    df = df.sort_values("Risk", ascending=False).reset_index(drop=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("##### Active Alerts")

has_alerts = False
for s_name, s_obj in statuses.items():
    if s_obj["alerts"]:
        has_alerts = True
        color = s_obj["color"]
        alert_content = "".join([f"<li style='margin-bottom:8px;'>{severity_icon(a.get('severity'))} <b>{a.get('type', 'Alert')}</b>: {a.get('detail', '')}</li>" for a in s_obj["alerts"]])
        
        card = f"""
        <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 5px solid {color}; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 12px;">
                <h4 style="margin:0; font-size:1rem; color:#111827;">{s_name}</h4>
                {status_badge(s_obj['status'])}
            </div>
            <ul style="margin:0; padding-left:20px; color:#374151; font-size:0.85rem; line-height:1.6;">
                {alert_content}
            </ul>
        </div>
        """
        st.markdown(card, unsafe_allow_html=True)

if not has_alerts:
    st.info("No active alerts across the network. All stations operating nominally.")
