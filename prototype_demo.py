"""
SkyGuard AI — Streamlit Prototype Dashboard
Run: streamlit run prototype_demo.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import time
import math
import json
from datetime import datetime, timedelta

st.set_page_config(
    page_title="SkyGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS ===
st.markdown("""
<style>
    .stApp { background-color: #0F172A; }
    .metric-card {
        background: #1E293B;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #334155;
    }
    .alert-card {
        background: #7F1D1D;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #EF4444;
    }
    .normal-card {
        background: #14532D;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #22C55E;
    }
    h1, h2, h3, p, span, label { color: #E2E8F0 !important; }
    .stMetric label { color: #94A3B8 !important; font-size: 14px !important; }
    .stMetric [data-testid="stMetricValue"] { color: #E2E8F0 !important; }
</style>
""", unsafe_allow_html=True)

# === STATE INIT ===
if 'readings' not in st.session_state:
    st.session_state.readings = []
    st.session_state.anomalies = []
    st.session_state.step = 0
    st.session_state.fault_mode = 'normal'
    st.session_state.drift_acc = 0.0
    st.session_state.frozen_val = None
    st.session_state.running = False
    st.session_state.sensor_health = {'temperature': 100, 'pressure': 100, 'humidity': 100}

# === PHYSICS ===
def magnus_dewpoint(temp, humidity):
    if humidity <= 0:
        return -999
    gamma = (17.27 * temp) / (237.7 + temp) + math.log(max(humidity, 0.01) / 100.0)
    if 17.27 - gamma == 0:
        return temp
    return (237.7 * gamma) / (17.27 - gamma)

# === WEATHER SIMULATOR ===
def generate_reading(step, fault_mode):
    hour = (step * 5 / 3600) % 24
    temp = 25 + 8 * math.sin((hour - 6) * math.pi / 12) + np.random.randn() * 0.3
    pressure = 1013 + 3 * math.sin(hour * math.pi / 24) + np.random.randn() * 0.2
    humidity = 60 - 15 * math.sin((hour - 6) * math.pi / 12) + np.random.randn() * 1.0
    humidity = max(0, min(100, humidity))
    
    anomaly_type = None
    
    if fault_mode == 'spike':
        temp += 25
        anomaly_type = 'SPIKE'
        st.session_state.fault_mode = 'normal'
    elif fault_mode == 'freeze':
        if st.session_state.frozen_val is None:
            st.session_state.frozen_val = (temp, pressure, humidity)
        temp, pressure, humidity = st.session_state.frozen_val
        anomaly_type = 'FROZEN'
    elif fault_mode == 'drift':
        st.session_state.drift_acc += 0.5
        humidity += st.session_state.drift_acc
        humidity = min(humidity, 100)
        if st.session_state.drift_acc > 5:
            anomaly_type = 'DRIFT'
    elif fault_mode == 'dropout':
        return None, 'DROPOUT'
    
    return {
        'timestamp': datetime.now() - timedelta(seconds=(100 - step) * 5),
        'temperature': round(temp, 1),
        'pressure': round(pressure, 1),
        'humidity': round(humidity, 1),
        'step': step
    }, anomaly_type

# === RULE ENGINE ===
def check_rules(reading, prev_reading):
    alerts = []
    t, p, h = reading['temperature'], reading['pressure'], reading['humidity']
    
    if not (-50 <= t <= 60):
        alerts.append(('OUT_OF_RANGE', 'CRITICAL', f'Temperature {t} C outside bounds'))
    if not (870 <= p <= 1084):
        alerts.append(('OUT_OF_RANGE', 'CRITICAL', f'Pressure {p} hPa outside bounds'))
    
    if prev_reading:
        dt = abs(t - prev_reading['temperature'])
        if dt > 5:
            alerts.append(('SPIKE', 'HIGH', f'Temperature changed {dt:.1f} C in one step'))
    
    dp = magnus_dewpoint(t, h)
    if dp > t + 0.5:
        alerts.append(('PHYSICS', 'CRITICAL', f'Dew point ({dp:.1f} C) > ambient ({t} C)'))
    
    return alerts

# === ANOMALY SCORING ===
def compute_anomaly_score(readings_buffer):
    if len(readings_buffer) < 5:
        return 0, [0, 0, 0]
    recent = np.array([(r['temperature'], r['pressure'], r['humidity']) for r in readings_buffer[-20:]])
    current = recent[-1]
    mean = recent[:-1].mean(axis=0)
    std = recent[:-1].std(axis=0) + 0.01
    z_scores = np.abs((current - mean) / std)
    return z_scores.mean(), z_scores.tolist()

# === SIDEBAR ===
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/cloud-protection.png", width=60)
    st.title("SkyGuard AI")
    st.caption("SIH26073 | MoES | Disaster Management")
    
    st.divider()
    st.subheader("🎮 Fault Injection")
    st.caption("Simulate sensor failures in real-time")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💥 Spike", use_container_width=True):
            st.session_state.fault_mode = 'spike'
        if st.button("🧊 Freeze", use_container_width=True):
            st.session_state.fault_mode = 'freeze'
            st.session_state.frozen_val = None
    with col2:
        if st.button("📈 Drift", use_container_width=True):
            st.session_state.fault_mode = 'drift'
            st.session_state.drift_acc = 0.0
        if st.button("📡 Dropout", use_container_width=True):
            st.session_state.fault_mode = 'dropout'
    
    if st.button("✅ Reset Normal", use_container_width=True, type="primary"):
        st.session_state.fault_mode = 'normal'
        st.session_state.frozen_val = None
        st.session_state.drift_acc = 0.0
    
    st.divider()
    st.caption(f"Current Mode: **{st.session_state.fault_mode.upper()}**")
    
    st.divider()
    st.subheader("Station Info")
    st.text("Station: AWS-DEMO-001")
    st.text("Location: Demo Lab")
    st.text(f"Uptime: {st.session_state.step * 5}s")

# === MAIN CONTENT ===
st.title("🛡️ SkyGuard AI — Weather Station Monitor")

# Generate new reading
st.session_state.step += 1
reading, anomaly_type = generate_reading(st.session_state.step, st.session_state.fault_mode)

if reading is not None:
    st.session_state.readings.append(reading)
    if len(st.session_state.readings) > 200:
        st.session_state.readings = st.session_state.readings[-200:]
    
    prev = st.session_state.readings[-2] if len(st.session_state.readings) > 1 else None
    rule_alerts = check_rules(reading, prev)
    score, per_feature = compute_anomaly_score(st.session_state.readings)
    
    is_anomaly = anomaly_type is not None or score > 2.5 or len(rule_alerts) > 0
    confidence = min(score / 2.5 * 100, 99.9) if score > 0 else 0
    
    if is_anomaly:
        atype = anomaly_type or (rule_alerts[0][0] if rule_alerts else 'PATTERN')
        st.session_state.anomalies.append({
            'timestamp': reading['timestamp'].strftime('%H:%M:%S'),
            'type': atype,
            'confidence': f"{confidence:.0f}%",
            'sensor': ['Temperature', 'Pressure', 'Humidity'][np.argmax(per_feature)] if max(per_feature) > 0 else 'Unknown',
            'reading': reading,
            'details': rule_alerts[0][2] if rule_alerts else f'Anomaly score: {score:.2f}'
        })
        if len(st.session_state.anomalies) > 50:
            st.session_state.anomalies = st.session_state.anomalies[-50:]

# === TOP METRICS ===
col1, col2, col3, col4, col5 = st.columns(5)

if reading:
    with col1:
        st.metric("🌡️ Temperature", f"{reading['temperature']} C",
                  delta=f"{reading['temperature'] - (st.session_state.readings[-2]['temperature'] if len(st.session_state.readings) > 1 else reading['temperature']):.1f} C")
    with col2:
        st.metric("🌊 Pressure", f"{reading['pressure']} hPa",
                  delta=f"{reading['pressure'] - (st.session_state.readings[-2]['pressure'] if len(st.session_state.readings) > 1 else reading['pressure']):.1f}")
    with col3:
        st.metric("💧 Humidity", f"{reading['humidity']:.1f}%",
                  delta=f"{reading['humidity'] - (st.session_state.readings[-2]['humidity'] if len(st.session_state.readings) > 1 else reading['humidity']):.1f}%")
    with col4:
        status = "🔴 ANOMALY" if (anomaly_type or len(st.session_state.anomalies) > 0 and st.session_state.anomalies[-1]['timestamp'] == reading['timestamp'].strftime('%H:%M:%S')) else "✅ NORMAL"
        st.metric("Status", status)
    with col5:
        st.metric("Readings", f"{len(st.session_state.readings)}")
else:
    with col1:
        st.metric("🌡️ Temperature", "---")
    with col2:
        st.metric("🌊 Pressure", "---")
    with col3:
        st.metric("💧 Humidity", "---")
    with col4:
        st.metric("Status", "📡 DROPOUT")
    with col5:
        st.metric("Readings", f"{len(st.session_state.readings)}")

st.divider()

# === CHARTS ===
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("📈 Live Sensor Readings")
    
    if len(st.session_state.readings) > 2:
        df = pd.DataFrame(st.session_state.readings)
        
        tab1, tab2, tab3 = st.tabs(["Temperature", "Pressure", "Humidity"])
        
        with tab1:
            st.line_chart(df.set_index('step')['temperature'], color='#EF4444')
        with tab2:
            st.line_chart(df.set_index('step')['pressure'], color='#3B82F6')
        with tab3:
            st.line_chart(df.set_index('step')['humidity'], color='#22C55E')
    else:
        st.info("Waiting for data...")

with right_col:
    st.subheader("🔴 Anomaly Alerts")
    
    if st.session_state.anomalies:
        for alert in reversed(st.session_state.anomalies[-8:]):
            st.markdown(f"""
<div class="alert-card">
    <strong>⚠️ {alert['type']}</strong> | {alert['timestamp']} | Confidence: {alert['confidence']}<br>
    <span style="color: #FCA5A5;">Sensor: {alert['sensor']}</span><br>
    <span style="color: #94A3B8; font-size: 12px;">{alert['details']}</span>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="normal-card">
    <strong>✅ All Clear</strong><br>
    <span style="color: #86EFAC;">No anomalies detected. All sensors operating normally.</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# === BOTTOM ROW ===
bot_left, bot_mid, bot_right = st.columns(3)

with bot_left:
    st.subheader("🏥 Sensor Health")
    
    health_data = {
        'Sensor': ['🌡️ Temperature (BMP280)', '🌊 Pressure (BMP280)', '💧 Humidity (DHT22)'],
        'Status': ['Healthy ✅', 'Healthy ✅', 'Healthy ✅'],
        'Confidence': ['98%', '97%', '95%'],
    }
    
    # Update based on fault mode
    if st.session_state.fault_mode == 'spike':
        health_data['Status'][0] = '⚠️ FAULT'
        health_data['Confidence'][0] = '23%'
    elif st.session_state.fault_mode == 'freeze':
        health_data['Status'] = ['🧊 FROZEN', '🧊 FROZEN', '🧊 FROZEN']
        health_data['Confidence'] = ['5%', '5%', '5%']
    elif st.session_state.fault_mode == 'drift':
        health_data['Status'][2] = '📈 DEGRADING'
        health_data['Confidence'][2] = f'{max(10, 95 - int(st.session_state.drift_acc * 5))}%'
    
    st.dataframe(pd.DataFrame(health_data), hide_index=True, use_container_width=True)

with bot_mid:
    st.subheader("🧠 Explainability")
    if st.session_state.anomalies:
        latest = st.session_state.anomalies[-1]
        st.markdown(f"""
**Anomaly Type:** {latest['type']}  
**Primary Offender:** {latest['sensor']}  
**Confidence:** {latest['confidence']}  
**Details:** {latest['details']}

**Physics Check:**  
Dew Point: {magnus_dewpoint(latest['reading']['temperature'], latest['reading']['humidity']):.1f} C  
Ambient: {latest['reading']['temperature']} C  
Result: {'❌ VIOLATED' if magnus_dewpoint(latest['reading']['temperature'], latest['reading']['humidity']) > latest['reading']['temperature'] + 0.5 else '✅ Consistent'}
""")
    else:
        st.info("No anomalies to explain")

with bot_right:
    st.subheader("📊 Detection Stats")
    total = len(st.session_state.readings)
    anomaly_count = len(st.session_state.anomalies)
    normal_count = total - anomaly_count
    
    st.metric("Total Readings", total)
    st.metric("Anomalies Detected", anomaly_count)
    st.metric("Normal Readings", max(0, normal_count))
    if total > 0:
        st.progress(max(0, normal_count) / max(total, 1), text=f"System Health: {max(0, normal_count)/max(total,1)*100:.0f}%")

# === AUTO REFRESH ===
st.caption("Dashboard auto-refreshes every 2 seconds")
time.sleep(2)
st.rerun()
