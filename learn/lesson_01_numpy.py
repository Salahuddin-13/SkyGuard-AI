"""
=============================================================
  LESSON 1: Python + NumPy — The Foundation Under All ML
=============================================================

Everything in ML is just MATH ON ARRAYS.
- An image? Array of pixel values.
- A sensor reading? Array of numbers.
- A neural network? Arrays multiplied together.

NumPy is the library that makes array math fast.
Let's learn it by working with WEATHER DATA — exactly what
SkyGuard AI processes.

RUN THIS FILE:  python lesson_01_numpy.py
=============================================================
"""

import numpy as np

# ============================================================
# PART 1: What is an array?
# ============================================================

# A Python list:
temps_list = [32.4, 33.1, 31.8, 34.2, 30.5]

# A NumPy array (same data, but FAST for math):
temps = np.array([32.4, 33.1, 31.8, 34.2, 30.5])

print("=== PART 1: Arrays ===")
print(f"Temperatures: {temps}")
print(f"Shape: {temps.shape}")        # (5,) — 5 elements, 1 dimension
print(f"Mean temp: {temps.mean():.1f}°C")
print(f"Std dev:   {temps.std():.1f}°C")
print(f"Min:       {temps.min():.1f}°C")
print(f"Max:       {temps.max():.1f}°C")

# WHY this matters for SkyGuard:
# When we check "is this sensor reading abnormal?", we compare
# it against the mean and standard deviation of recent readings.
# If a reading is more than 3 standard deviations from the mean,
# it's probably a spike anomaly.

threshold = temps.mean() + 3 * temps.std()
print(f"\nAnomaly threshold (mean + 3*std): {threshold:.1f} C")
print(f"Is 55°C an anomaly? {55.0 > threshold}")  # True!

# ============================================================
# PART 2: 2D Arrays (Matrices) — Multiple sensors at once
# ============================================================

print("\n=== PART 2: 2D Arrays (our sensor data) ===")

# In SkyGuard, each reading has 3 values: [temp, pressure, humidity]
# Multiple readings over time = a 2D array (matrix)

# 5 readings × 3 sensors:
#              Temp(°C)  Pressure(hPa)  Humidity(%)
readings = np.array([
    [32.4,    1008.2,        68.5],   # t=0
    [32.8,    1008.0,        67.2],   # t=5s
    [33.1,    1007.8,        66.8],   # t=10s
    [32.6,    1008.1,        68.0],   # t=15s
    [55.0,    1008.0,        67.5],   # t=20s  ← SPIKE! Sensor glitch!
])

print(f"Shape: {readings.shape}")     # (5, 3) — 5 rows, 3 columns
print(f"Row 0 (first reading):  {readings[0]}")
print(f"Column 0 (all temps):   {readings[:, 0]}")  # The : means "all rows"

# Mean and std PER COLUMN (per sensor):
means = readings.mean(axis=0)   # axis=0 = "collapse rows, keep columns"
stds  = readings.std(axis=0)
print(f"\nMeans per sensor:  T={means[0]:.1f}, P={means[1]:.1f}, RH={means[2]:.1f}")
print(f"Stds per sensor:   T={stds[0]:.1f},  P={stds[1]:.1f},  RH={stds[2]:.1f}")

# Notice: temperature std is HIGH because of the 55°C spike!

# ============================================================
# PART 3: Normalization — Making sensors comparable
# ============================================================

print("\n=== PART 3: Normalization ===")

# Problem: temp is ~32, pressure is ~1008, humidity is ~68.
# They're on completely different scales!
# If we feed these to a neural network, it'll think pressure is 
# 30x more important than temperature just because the numbers are bigger.

# Solution: NORMALIZE each column to mean=0, std=1
# This is called "StandardScaler" or "z-score normalization"
# Formula: z = (x - mean) / std

# Let's use readings WITHOUT the spike for our "normal" baseline:
clean = readings[:4]  # first 4 readings
clean_mean = clean.mean(axis=0)
clean_std  = clean.std(axis=0)

# Normalize ALL readings using the clean baseline:
normalized = (readings - clean_mean) / clean_std

print("Original readings:")
print(readings)
print("\nNormalized readings:")
print(np.round(normalized, 2))
print("\nNotice: the spike at row 4 now shows as temp = "
      f"{normalized[4, 0]:.1f} (way above 0!)")
print("Values near 0 = normal. Values far from 0 = suspicious.")

# THIS is exactly what we do before feeding data to our LSTM.

# ============================================================
# PART 4: Sliding Windows — How ML sees time-series
# ============================================================

print("\n=== PART 4: Sliding Windows ===")

# A neural network can't "see" all your data at once.
# We feed it WINDOWS of recent data and ask:
# "Given the last 60 readings, what should the next one look like?"

# Simple example with a 1D temperature series:
temp_series = np.array([30, 31, 32, 33, 34, 35, 36, 37, 38, 39])
window_size = 4

# Create sliding windows:
windows = []
for i in range(len(temp_series) - window_size):
    window = temp_series[i : i + window_size]
    target = temp_series[i + window_size]
    windows.append((window, target))
    print(f"  Window: {window} → Next value: {target}")

print(f"\nTotal windows created: {len(windows)}")
print("The model learns: 'if I see [30,31,32,33], next should be ~34'")
print("If it sees [30,31,32,33] but actual next is 55 → ANOMALY!")

# ============================================================
# PART 5: Your first anomaly detector (no ML needed!)
# ============================================================

print("\n=== PART 5: Simple Anomaly Detector ===")

# 100 fake temperature readings: normal pattern + injected spike
np.random.seed(42)
normal_temps = 30 + 5 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.randn(100) * 0.5

# Inject a spike at index 50
normal_temps[50] = 55.0
# Inject a frozen value from index 70-80
normal_temps[70:80] = normal_temps[69]

# Z-score anomaly detection:
rolling_mean = np.convolve(normal_temps, np.ones(10)/10, mode='same')
residuals = normal_temps - rolling_mean
z_scores = (residuals - residuals.mean()) / residuals.std()

# Flag anything with |z-score| > 3:
anomalies = np.abs(z_scores) > 3
anomaly_indices = np.where(anomalies)[0]

print(f"Total readings: {len(normal_temps)}")
print(f"Anomalies detected at indices: {anomaly_indices}")
print(f"Values at those indices: {normal_temps[anomaly_indices]}")

print("\n✅ Lesson 1 complete!")
print("You now understand: arrays, 2D data, normalization, sliding windows,")
print("and z-score anomaly detection. These are the EXACT building blocks")
print("of SkyGuard AI.")
print("\n→ Next: lesson_02_pandas.py (loading real weather data)")
