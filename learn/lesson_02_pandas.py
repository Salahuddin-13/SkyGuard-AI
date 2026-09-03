"""
=============================================================
  LESSON 2: Pandas — Loading and Exploring Real Weather Data
=============================================================

Pandas is how you load CSV files, filter data, and prepare
datasets for ML. Think of it as "Excel but in Python."

We'll download the ACTUAL Jena Climate Dataset — the same data
we'll use to train SkyGuard AI's anomaly detector.

RUN THIS:  python lesson_02_pandas.py
=============================================================
"""

import pandas as pd
import numpy as np
import os
import urllib.request
import zipfile

# ============================================================
# PART 1: Get the Jena Climate Dataset
# ============================================================

print("=== PART 1: Downloading Jena Climate Dataset ===")

data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(data_dir, exist_ok=True)
csv_path = os.path.join(data_dir, 'jena_climate.csv')

if not os.path.exists(csv_path):
    url = "https://storage.googleapis.com/tensorflow/tf-keras-datasets/jena_climate_2009_2016.csv.zip"
    zip_path = os.path.join(data_dir, 'jena_climate.zip')
    print(f"Downloading from {url}...")
    urllib.request.urlretrieve(url, zip_path)
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Extract and rename
        names = z.namelist()
        z.extractall(data_dir)
        extracted = os.path.join(data_dir, names[0])
        if extracted != csv_path:
            os.rename(extracted, csv_path)
    
    os.remove(zip_path)
    print("✅ Downloaded and extracted!")
else:
    print("✅ Already downloaded!")

# ============================================================
# PART 2: Load the CSV into a DataFrame
# ============================================================

print("\n=== PART 2: Loading Data ===")

df = pd.read_csv(csv_path)

print(f"Shape: {df.shape}")           # (rows, columns)
print(f"Columns: {list(df.columns)}")
print(f"\nFirst 3 rows:")
print(df.head(3))

# This dataset has 420,551 readings at 10-minute intervals
# from 2009 to 2016. It includes 14 weather parameters.

# ============================================================
# PART 3: Extract OUR three parameters
# ============================================================

print("\n=== PART 3: Our Three Sensors ===")

# SkyGuard AI only uses 3 parameters:
# - Temperature (°C)     → column "T (degC)"
# - Pressure (hPa)       → column "p (mbar)"   (mbar = hPa)
# - Humidity (%)          → column "rh (%)"

# Select only what we need:
weather = df[['Date Time', 'T (degC)', 'p (mbar)', 'rh (%)']].copy()
weather.columns = ['datetime', 'temperature', 'pressure', 'humidity']

# Parse dates:
weather['datetime'] = pd.to_datetime(weather['datetime'], format='%d.%m.%Y %H:%M:%S')

print(weather.head())
print(f"\nDate range: {weather['datetime'].min()} to {weather['datetime'].max()}")
print(f"Total readings: {len(weather):,}")

# ============================================================
# PART 4: Basic Statistics — Know Your Data
# ============================================================

print("\n=== PART 4: Statistics ===")
print(weather[['temperature', 'pressure', 'humidity']].describe())

# Key takeaways:
# - Temperature: -23°C to +37°C (Jena, Germany — gets cold!)
# - Pressure: 913 to 1046 hPa (wide range due to weather systems)
# - Humidity: 12% to 100%

# ============================================================
# PART 5: Filtering and Slicing — Pandas Power
# ============================================================

print("\n=== PART 5: Filtering ===")

# Get just one day of data:
one_day = weather[weather['datetime'].dt.date == pd.Timestamp('2015-07-01').date()]
print(f"Readings on July 1, 2015: {len(one_day)}")
print(f"  Temp range: {one_day['temperature'].min():.1f} to {one_day['temperature'].max():.1f}°C")

# Find extreme readings:
extreme_cold = weather[weather['temperature'] < -20]
print(f"\nReadings below -20°C: {len(extreme_cold)}")

extreme_humid = weather[weather['humidity'] > 99.5]
print(f"Readings above 99.5% humidity: {len(extreme_humid)}")

# ============================================================
# PART 6: Rolling Statistics — Catching Anomalies
# ============================================================

print("\n=== PART 6: Rolling Statistics ===")

# A "rolling window" computes statistics over a sliding window.
# This is how we track "what's normal right now."

# Rolling mean and std over the last 6 readings (1 hour at 10-min intervals):
weather['temp_rolling_mean'] = weather['temperature'].rolling(window=6).mean()
weather['temp_rolling_std']  = weather['temperature'].rolling(window=6).std()

# Z-score: how far is each reading from its rolling mean?
weather['temp_z_score'] = (
    (weather['temperature'] - weather['temp_rolling_mean']) 
    / weather['temp_rolling_std']
)

# Anything with |z-score| > 4 is suspicious:
suspicious = weather[weather['temp_z_score'].abs() > 4].dropna()
print(f"Suspicious temperature readings (|z| > 4): {len(suspicious)}")
if len(suspicious) > 0:
    print(suspicious[['datetime', 'temperature', 'temp_z_score']].head(5))

# ============================================================
# PART 7: Preparing Data for ML — The Final Step
# ============================================================

print("\n=== PART 7: ML-Ready Data ===")

# For our LSTM Autoencoder, we need:
# 1. Just the 3 numeric columns as a NumPy array
# 2. Normalized (mean=0, std=1)
# 3. Shaped into sliding windows

# Step 1: Extract values
values = weather[['temperature', 'pressure', 'humidity']].values
print(f"Raw array shape: {values.shape}")  # (420551, 3)

# Step 2: Normalize
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
values_normalized = scaler.fit_transform(values)

print(f"After normalization:")
print(f"  Temperature — mean: {values_normalized[:, 0].mean():.4f}, std: {values_normalized[:, 0].std():.4f}")
print(f"  Pressure    — mean: {values_normalized[:, 1].mean():.4f}, std: {values_normalized[:, 1].std():.4f}")
print(f"  Humidity    — mean: {values_normalized[:, 2].mean():.4f}, std: {values_normalized[:, 2].std():.4f}")
# All should be ~0.0 mean and ~1.0 std

# Step 3: Create sliding windows
window_size = 60  # 60 readings = 10 hours of data at 10-min intervals

# We'll create windows more efficiently:
def create_windows(data, window_size):
    windows = []
    for i in range(len(data) - window_size):
        windows.append(data[i : i + window_size])
    return np.array(windows)

# Just do a small sample for now (full dataset = 420k windows = a lot of RAM)
sample = values_normalized[:5000]
windows = create_windows(sample, window_size)

print(f"\nSliding windows shape: {windows.shape}")
# Should be (4940, 60, 3) — 4940 windows, each 60 timesteps, 3 features

print(f"  {windows.shape[0]} windows")
print(f"  Each window: {windows.shape[1]} timesteps × {windows.shape[2]} features")
print(f"  This is what we feed to the LSTM!")

# Save the scaler for later use
import pickle
scaler_path = os.path.join(data_dir, 'scaler.pkl')
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"\n✅ Scaler saved to {scaler_path}")

print("\n✅ Lesson 2 complete!")
print("You now know how to: load CSVs, explore data, filter, compute rolling")
print("statistics, normalize, and create sliding windows for ML.")
print("\n→ Next: lesson_03_visualize.py (SEE the data and anomalies)")
