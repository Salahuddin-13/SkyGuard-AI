import sys
import os
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import (
    apply_styling, STATIONS, fetch_all_stations, inject_fault,
    get_station_status, load_lstm_model, load_training_report,
    magnus_dewpoint, compute_spatial_context, assess_data_quality,
    status_badge, source_badge, severity_icon, COLOR_HEALTHY,
    COLOR_WARNING, COLOR_CRITICAL, STATUS_HEALTHY, generate_explanation, get_layer_status
)

st.set_page_config(page_title="SkyGuard AI - Dashboard", layout="wide")
apply_styling()

if "faults" not in st.session_state:
    st.session_state.faults = {}

st.markdown("### SkyGuard AI Environmental Dashboard")

model_info = load_lstm_model()
raw_data = fetch_all_stations()

all_data = {}
for name, data in raw_data.items():
    if name in st.session_state.faults and st.session_state.faults[name]:
        all_data[name] = inject_fault(data, st.session_state.faults[name])
    else:
        all_data[name] = data

statuses = {}
for name, data in all_data.items():
    statuses[name] = get_station_status(name, data, all_data, model_info)

total_stations = len(statuses)
healthy_stations = sum(1 for s in statuses.values() if s["status"] == STATUS_HEALTHY)
total_alerts = sum(s["alert_count"] for s in statuses.values())

temps = [s["temperature"] for s in statuses.values() if s["temperature"] is not None]
pressures = [s["pressure"] for s in statuses.values() if s["pressure"] is not None]
humidities = [s["humidity"] for s in statuses.values() if s["humidity"] is not None]

avg_temp = sum(temps) / len(temps) if temps else 0.0
avg_pressure = sum(pressures) / len(pressures) if pressures else 0.0
avg_rh = sum(humidities) / len(humidities) if humidities else 0.0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Stations", total_stations)
col2.metric("Healthy", healthy_stations)
col3.metric("Alerts", total_alerts)
col4.metric("Avg Temp", f"{avg_temp:.1f} °C")
col5.metric("Avg Pressure", f"{avg_pressure:.1f} hPa")
col6.metric("Avg RH", f"{avg_rh:.1f} %")

st.markdown("---")
st.markdown("##### Station Deep Dive")

station_names = list(STATIONS.keys())
selected_station = st.selectbox("Select Station", station_names)

if selected_station in statuses:
    s = statuses[selected_station]
    sd = all_data[selected_station]
    
    st.markdown(f"**{sd['full_name']} ({sd['id']})** — {sd['state']} | Elev: {sd['elevation_m']}m | {sd['lat']}°N, {sd['lon']}°E")
    st.markdown(f"{status_badge(s['status'], 'lg')} &nbsp; {source_badge(s['source'])}", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    t_val = f"{s['temperature']:.1f} °C" if s['temperature'] is not None else "N/A"
    p_val = f"{s['pressure']:.1f} hPa" if s['pressure'] is not None else "N/A"
    h_val = f"{s['humidity']:.1f} %" if s['humidity'] is not None else "N/A"
    dp_val = f"{s['dew_point']:.1f} °C" if s['dew_point'] is not None else "N/A"
    
    kpi1.metric("Temperature", t_val)
    kpi2.metric("Pressure", p_val)
    kpi3.metric("Humidity", h_val)
    kpi4.metric("Dew Point", dp_val)

    colA, colB = st.columns(2)
    
    with colA:
        st.markdown("###### Data Quality")
        q = s["quality"]
        st.markdown(f"**Quality Score:** {q['score']}/100")
        st.markdown(f"- Freshness: {'Pass' if q['fresh'] else 'Fail'}")
        st.markdown(f"- Completeness: {'Pass' if q['complete'] else 'Fail'}")
        st.markdown(f"- Validity: {'Pass' if q['valid'] else 'Fail'}")
        st.markdown(f"- Consistency: {'Pass' if q['consistent'] else 'Fail'}")
        if q["issues"]:
            for issue in q["issues"]:
                st.markdown(f"<span style='color:{COLOR_CRITICAL};font-size:0.8rem;'>- {issue}</span>", unsafe_allow_html=True)
        
        st.markdown("###### Spatial Context")
        sp = s["spatial"]
        if sp.get("available"):
            st.markdown(f"Compared to {sp['nearby_count']} nearby stations")
            st.markdown(f"- Temp Regional Avg: {sp.get('temp_regional_avg', 'N/A')} °C (Dev: {sp.get('temp_deviation', 'N/A')} °C) - Consistent: {sp.get('temp_consistent', 'N/A')}")
            st.markdown(f"- Pres Regional Avg: {sp.get('pres_regional_avg', 'N/A')} hPa (Dev: {sp.get('pres_deviation', 'N/A')} hPa) - Consistent: {sp.get('pres_consistent', 'N/A')}")
            st.markdown(f"- Hum Regional Avg: {sp.get('hum_regional_avg', 'N/A')} % (Dev: {sp.get('hum_deviation', 'N/A')} %) - Consistent: {sp.get('hum_consistent', 'N/A')}")
            overall_sp = 'Pass' if sp.get('overall_consistent') else 'Fail'
            st.markdown(f"**Overall Spatial Consistency:** {overall_sp}")
        else:
            st.markdown("Spatial context not available.")
            
        st.markdown("###### Physics Validation")
        st.markdown(f"Magnus Dew Point: {dp_val}")
        if s['temperature'] is not None and s['dew_point'] is not None:
            if s['dew_point'] > s['temperature'] + 0.5:
                st.markdown(f"<span style='color:{COLOR_CRITICAL};font-size:0.8rem;'>Thermodynamic violation: Dew point exceeds ambient temperature.</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:#16A34A;font-size:0.8rem;'>Thermodynamic consistency: Pass.</span>", unsafe_allow_html=True)
        else:
             st.markdown("Not enough data for physics validation.")

    with colB:
        st.markdown("###### 3-Layer Detection Status")
        ls = s["layer_status"]
        st.markdown(f"**Layer 1 (Rule Engine):** <span style='color:{ls['layer1']['color']}'>{ls['layer1']['status']}</span> - {ls['layer1']['detail']}", unsafe_allow_html=True)
        st.markdown(f"**Layer 2 (LSTM/ML):** <span style='color:{ls['layer2']['color']}'>{ls['layer2']['status']}</span> - {ls['layer2']['detail']}", unsafe_allow_html=True)
        st.markdown(f"**Layer 3 (Physics):** <span style='color:{ls['layer3']['color']}'>{ls['layer3']['status']}</span> - {ls['layer3']['detail']}", unsafe_allow_html=True)
        
        st.markdown("###### 24h Trends")
        if "hourly" in sd and "time" in sd["hourly"]:
            hourly = sd["hourly"]
            if "temperature_2m" in hourly and "surface_pressure" in hourly and "relative_humidity_2m" in hourly:
                times = pd.to_datetime(hourly["time"][-24:])
                chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Temp (°C)", "Pressure (hPa)", "RH (%)"])
                with chart_tab1:
                    df_t = pd.DataFrame({"Temperature (°C)": hourly["temperature_2m"][-24:]}, index=times)
                    st.line_chart(df_t, height=180)
                with chart_tab2:
                    df_p = pd.DataFrame({"Pressure (hPa)": hourly["surface_pressure"][-24:]}, index=times)
                    st.line_chart(df_p, height=180)
                with chart_tab3:
                    df_h = pd.DataFrame({"Humidity (%)": hourly["relative_humidity_2m"][-24:]}, index=times)
                    st.line_chart(df_h, height=180)
            else:
                st.markdown("Hourly trend data format not valid.")
        else:
            st.markdown("Hourly trend data not available.")

    st.markdown("---")
    st.markdown("###### Alert Details")
    if s["alerts"]:
        exp = s["explanation"]
        st.markdown(f"**Classification:** {exp['classification']}")
        st.markdown(f"**Conclusion:** {exp['conclusion']}")
        st.markdown(f"**Recommended Action:** {exp['recommended_action']}")
        
        for alert in s["alerts"]:
            sev_icon = severity_icon(alert['severity'])
            st.markdown(f"- {sev_icon} **{alert['layer']} | {alert['type']}**: {alert['detail']}")
    else:
        st.markdown("No active alerts.")
