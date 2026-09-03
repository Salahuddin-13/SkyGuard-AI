"""
=============================================================
  LESSON 3: Visualization — See the Data, See the Anomalies
=============================================================

You can't detect anomalies if you don't know what "normal" 
looks like. Let's VISUALIZE our weather data.

RUN THIS:  python lesson_03_visualize.py
(This will open chart windows — close each to see the next)
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load the data (from lesson 2)
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
csv_path = os.path.join(data_dir, 'jena_climate.csv')

if not os.path.exists(csv_path):
    print("❌ Run lesson_02_pandas.py first to download the dataset!")
    exit()

df = pd.read_csv(csv_path)
weather = df[['Date Time', 'T (degC)', 'p (mbar)', 'rh (%)']].copy()
weather.columns = ['datetime', 'temperature', 'pressure', 'humidity']
weather['datetime'] = pd.to_datetime(weather['datetime'], format='%d.%m.%Y %H:%M:%S')

# ============================================================
# CHART 1: One week of temperature — See the daily cycle
# ============================================================

print("=== Chart 1: Daily Temperature Cycle ===")

week = weather[(weather['datetime'] >= '2015-07-01') & 
               (weather['datetime'] < '2015-07-08')]

fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(week['datetime'], week['temperature'], color='#e74c3c', linewidth=0.8)
ax.set_title('Temperature — One Week (July 2015)', fontsize=14, fontweight='bold')
ax.set_ylabel('Temperature (°C)')
ax.set_xlabel('Date')
ax.grid(True, alpha=0.3)
ax.axhline(y=week['temperature'].mean(), color='gray', linestyle='--', alpha=0.5, label='Mean')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(data_dir, 'chart_1_daily_cycle.png'), dpi=150)
plt.show()

print("See the daily cycle? Temperature goes up during the day, down at night.")
print("This is the PATTERN the LSTM will learn as 'normal'.")
print("A sudden 55°C spike would look OBVIOUSLY wrong here.\n")

# ============================================================
# CHART 2: All three sensors together — Correlations
# ============================================================

print("=== Chart 2: Three Sensors Together ===")

fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)

for ax, col, color, label in zip(
    axes,
    ['temperature', 'pressure', 'humidity'],
    ['#e74c3c', '#3498db', '#2ecc71'],
    ['Temperature (°C)', 'Pressure (hPa)', 'Humidity (%)']
):
    ax.plot(week['datetime'], week[col], color=color, linewidth=0.8)
    ax.set_ylabel(label, fontsize=10)
    ax.grid(True, alpha=0.3)

axes[0].set_title('Three Sensors — One Week', fontsize=14, fontweight='bold')
axes[2].set_xlabel('Date')
plt.tight_layout()
plt.savefig(os.path.join(data_dir, 'chart_2_three_sensors.png'), dpi=150)
plt.show()

print("Notice: when temperature goes UP, humidity often goes DOWN.")
print("And pressure has its own slower rhythm.")
print("SkyGuard uses these CORRELATIONS — if temp spikes but humidity")
print("stays flat, that's suspicious (a real heatwave would lower humidity).\n")

# ============================================================
# CHART 3: Injecting anomalies — What we need to detect
# ============================================================

print("=== Chart 3: Simulated Anomalies ===")

# Take a clean day and inject different anomaly types:
day = weather[(weather['datetime'] >= '2015-07-03') & 
              (weather['datetime'] < '2015-07-04')].copy()
day = day.reset_index(drop=True)

clean_temp = day['temperature'].values.copy()
anomaly_temp = clean_temp.copy()

# Inject anomalies:
anomaly_temp[30] = 55.0        # SPIKE at index 30
anomaly_temp[60:80] = clean_temp[59]  # FROZEN from index 60-80
drift = np.linspace(0, 8, 25)  # DRIFT from index 100-125
anomaly_temp[100:125] += drift

fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

# Clean
axes[0].plot(clean_temp, color='#2ecc71', linewidth=1)
axes[0].set_title('Clean Temperature Signal', fontsize=12, fontweight='bold')
axes[0].set_ylabel('°C')
axes[0].grid(True, alpha=0.3)

# With anomalies
axes[1].plot(anomaly_temp, color='#e74c3c', linewidth=1)
axes[1].set_title('Temperature WITH Injected Anomalies', fontsize=12, fontweight='bold')
axes[1].set_ylabel('°C')
axes[1].grid(True, alpha=0.3)

# Highlight anomaly regions
axes[1].axvspan(28, 32, alpha=0.3, color='red', label='Spike')
axes[1].axvspan(58, 82, alpha=0.3, color='orange', label='Frozen')
axes[1].axvspan(98, 127, alpha=0.3, color='purple', label='Drift')
axes[1].legend(loc='upper left')

plt.tight_layout()
plt.savefig(os.path.join(data_dir, 'chart_3_anomalies.png'), dpi=150)
plt.show()

print("Three types of anomalies our system catches:")
print("  🔴 SPIKE — sudden impossible jump (sensor glitch)")
print("  🟠 FROZEN — flat line (sensor locked up)")
print("  🟣 DRIFT — slowly creeping away from truth (sensor degrading)")
print()

# ============================================================
# CHART 4: What the LSTM Autoencoder "sees"
# ============================================================

print("=== Chart 4: Reconstruction Error (the ML magic) ===")

# Simulate what the autoencoder does:
# It tries to RECONSTRUCT each reading from the pattern it learned.
# Error = |actual - reconstructed|
# High error = anomaly!

# Fake "reconstructed" values (in reality the LSTM does this):
reconstructed = clean_temp + np.random.randn(len(clean_temp)) * 0.3  # small noise

# Compute reconstruction error for both:
error_clean = np.abs(anomaly_temp - reconstructed)

fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

axes[0].plot(anomaly_temp, color='#e74c3c', linewidth=1, label='Actual (with faults)')
axes[0].plot(reconstructed, color='#3498db', linewidth=1, alpha=0.7, label='Expected (model)')
axes[0].set_title('Actual vs Expected', fontsize=12, fontweight='bold')
axes[0].set_ylabel('°C')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].fill_between(range(len(error_clean)), error_clean, alpha=0.7, color='#e74c3c')
axes[1].axhline(y=3.0, color='black', linestyle='--', label='Anomaly Threshold')
axes[1].set_title('Reconstruction Error', fontsize=12, fontweight='bold')
axes[1].set_ylabel('|Error|')
axes[1].set_xlabel('Reading Index')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(data_dir, 'chart_4_reconstruction_error.png'), dpi=150)
plt.show()

print("THIS is how the LSTM Autoencoder detects anomalies:")
print("  1. It learns what normal weather LOOKS like")
print("  2. For each new reading, it tries to 'reconstruct' it")
print("  3. If the error is HIGH → the reading doesn't match the pattern → ANOMALY")
print("  4. The SIZE of the error = confidence score")

print("\n✅ Lesson 3 complete!")
print("You can now SEE what anomalies look like and HOW reconstruction error works.")
print("\n→ Next: lesson_04_pytorch.py (building neural networks)")
