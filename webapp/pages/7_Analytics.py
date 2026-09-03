import sys
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Analytics | SkyGuard AI", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import (
    apply_styling, STATIONS, fetch_all_stations, inject_fault, get_station_status, 
    load_lstm_model, load_training_report, assess_data_quality, compute_spatial_context, 
    STATUS_HEALTHY, STATUS_WARNING, STATUS_HIGH_RISK, STATUS_CRITICAL, 
    COLOR_HEALTHY, COLOR_WARNING, COLOR_HIGH, COLOR_CRITICAL
)

apply_styling()

st.title("Analytics & Insights")
st.markdown("##### Network performance, station reliability, and dataset statistics")

if 'faults' not in st.session_state:
    st.session_state.faults = {}

# Fetch and Process Data
all_data = fetch_all_stations()
model_info = load_lstm_model()

processed_stations = {}
for name, data in all_data.items():
    if name in st.session_state.faults:
        data = inject_fault(data, st.session_state.faults[name])
    
    stat = get_station_status(name, data, all_data, model_info)
    processed_stations[name] = stat

# Network Overview
st.markdown("### Network Overview")

statuses = [stat['status'] for stat in processed_stations.values()]
status_counts = pd.Series(statuses).value_counts().to_dict()

valid_temps = [stat['temperature'] for stat in processed_stations.values() if stat['temperature'] is not None]
valid_press = [stat['pressure'] for stat in processed_stations.values() if stat['pressure'] is not None]
valid_humid = [stat['humidity'] for stat in processed_stations.values() if stat['humidity'] is not None]

avg_t = sum(valid_temps)/len(valid_temps) if valid_temps else 0
avg_p = sum(valid_press)/len(valid_press) if valid_press else 0
avg_h = sum(valid_humid)/len(valid_humid) if valid_humid else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stations", len(STATIONS))
col2.metric("Avg Temperature", f"{avg_t:.1f} °C")
col3.metric("Avg Pressure", f"{avg_p:.1f} hPa")
col4.metric("Avg Humidity", f"{avg_h:.1f} %")

st.markdown("#### Status Breakdown")
st.bar_chart(status_counts)

# Station Comparison table
st.markdown("### Station Comparison")
table_data = []
for name, stat in processed_stations.items():
    table_data.append({
        "Name": name,
        "Status": stat['status'],
        "Temp": stat['temperature'],
        "Press": stat['pressure'],
        "RH": stat['humidity'],
        "Risk Score": stat['risk']['score'],
        "Data Quality Score": stat['quality']['score'],
        "Source": stat['source']
    })
df_stations = pd.DataFrame(table_data)
st.dataframe(df_stations, use_container_width=True)

# Risk Distribution
st.markdown("### Risk Distribution")
risk_data = pd.DataFrame({
    'Station': [row['Name'] for row in table_data],
    'Risk Score': [row['Risk Score'] for row in table_data]
}).set_index('Station')
st.bar_chart(risk_data)

# Data Quality Summary
st.markdown("### Data Quality Summary")
avg_quality = sum(row['Data Quality Score'] for row in table_data) / len(table_data) if table_data else 0
st.metric("Average Quality Score", f"{avg_quality:.1f} / 100")

issues_flat = []
for stat in processed_stations.values():
    issues_flat.extend(stat['quality'].get('issues', []))
issues_counts = pd.Series(issues_flat).value_counts() if issues_flat else pd.Series(dtype=int)

if not issues_counts.empty:
    st.write("Current Issues Types:")
    st.dataframe(issues_counts, use_container_width=True)
else:
    st.write("No active data quality issues.")

# Training Dataset Statistics
st.markdown("### Training Dataset Statistics")
report = load_training_report()
if report:
    data_info = report.get('data', {})
    lstm_info = report.get('lstm_ae', {})
    dataset = data_info.get('dataset', 'N/A')
    total_readings = data_info.get('total_readings', 'N/A')
    training_samples = data_info.get('train_samples', 'N/A')
    features = ", ".join(data_info.get('features', []))
    seq_len = data_info.get('seq_len', 'N/A')
    params = f"{lstm_info.get('total_params', 0):,}" if 'total_params' in lstm_info else 'N/A'
    epochs = lstm_info.get('epochs', 'N/A')
    val_loss = f"{lstm_info.get('best_val_loss', 0):.5f}" if 'best_val_loss' in lstm_info else 'N/A'
    
    st.markdown(f"""
    - **Dataset:** {dataset}
    - **Total readings:** {total_readings:,}
    - **Training samples:** {training_samples:,}
    - **Features:** {features}
    - **Sequence length:** {seq_len}
    - **Model parameters:** {params}
    - **Epochs:** {epochs}
    - **Best validation loss:** {val_loss}
    """)
else:
    st.write("Training report not found.")

# Station Reliability concept
st.markdown("### Station Reliability")
st.markdown("*Prototype — reliability scoring pending full implementation*")
rel_data = []
for name, stat in processed_stations.items():
    alert_count = stat['alert_count']
    qual = stat['quality']['score']
    data_avail = "Yes" if stat['temperature'] is not None else "No"
    rel_data.append({
        "Station": name,
        "Data Flowing?": data_avail,
        "Quality Score": qual,
        "Active Alerts": alert_count
    })
st.table(pd.DataFrame(rel_data))

# Simulation Statistics
st.markdown("### Simulation Statistics")
num_faults = len(st.session_state.faults)
fault_types = list(set(st.session_state.faults.values()))
st.write(f"**Number of active injected faults:** {num_faults}")
st.write(f"**Types of active faults:** {', '.join(fault_types) if fault_types else 'None'}")
