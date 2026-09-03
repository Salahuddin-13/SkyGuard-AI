"""
SkyGuard AI — Core Engine
=========================
Environmental Intelligence & Early Warning Platform
SIH26073 | Ministry of Earth Sciences

Modules:
  1. Station metadata (12 Indian AWS locations)
  2. Open-Meteo data provider with source labeling
  3. LSTM Autoencoder inference (real model)
  4. 3-Layer detection engine (Rules → LSTM → Physics)
  5. Spatial validation (neighboring station comparison)
  6. Risk scoring (deterministic formula)
  7. Data quality assessment
  8. Alert explanation generator
  9. Fault injection
  10. Design system (CSS)
"""

import math
import copy
import json
import os
import time
import pickle
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import requests
import streamlit as st

# ==============================================================================
# 0. PATHS & CONSTANTS
# ==============================================================================

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # SIH root
_MODEL_DIR = os.path.join(_BASE_DIR, "ml", "models")
_REPORT_PATH = os.path.join(_MODEL_DIR, "training_report.json")

# Status vocabulary — consistent across the platform
STATUS_HEALTHY   = "HEALTHY"
STATUS_WARNING   = "WARNING"
STATUS_HIGH_RISK = "HIGH_RISK"
STATUS_CRITICAL  = "CRITICAL"
STATUS_OFFLINE   = "OFFLINE"

# Severity levels
SEV_CRITICAL = "CRITICAL"
SEV_HIGH     = "HIGH"
SEV_MEDIUM   = "MEDIUM"
SEV_LOW      = "LOW"
SEV_INFO     = "INFO"

# Data source labels — honesty rule
SOURCE_OPENMETEO   = "Open-Meteo"
SOURCE_HARDWARE    = "ESP32 / MQTT"
SOURCE_SIMULATION  = "Simulation"
SOURCE_CACHED      = "Cached"
SOURCE_FALLBACK    = "Synthetic Fallback"

# Status colors
COLOR_HEALTHY  = "#16A34A"
COLOR_WARNING  = "#D97706"
COLOR_HIGH     = "#EA580C"
COLOR_CRITICAL = "#DC2626"
COLOR_OFFLINE  = "#6B7280"
COLOR_INFO     = "#2563EB"
COLOR_ACTIVE   = "#0D9488"

# ==============================================================================
# 1. STATION METADATA
# ==============================================================================

STATIONS: Dict[str, Dict[str, Any]] = {
    "Delhi (Safdarjung)": {
        "id": "DEL", "name": "Delhi", "full_name": "Delhi (Safdarjung)",
        "lat": 28.5849, "lon": 77.2083, "state": "Delhi", "elevation_m": 216,
    },
    "Mumbai (Colaba)": {
        "id": "BOM", "name": "Mumbai", "full_name": "Mumbai (Colaba)",
        "lat": 18.9067, "lon": 72.8147, "state": "Maharashtra", "elevation_m": 14,
    },
    "Chennai (Nungambakkam)": {
        "id": "MAA", "name": "Chennai", "full_name": "Chennai (Nungambakkam)",
        "lat": 13.0660, "lon": 80.2399, "state": "Tamil Nadu", "elevation_m": 16,
    },
    "Kolkata (Alipore)": {
        "id": "CCU", "name": "Kolkata", "full_name": "Kolkata (Alipore)",
        "lat": 22.5354, "lon": 88.3358, "state": "West Bengal", "elevation_m": 9,
    },
    "Bengaluru (HAL)": {
        "id": "BLR", "name": "Bengaluru", "full_name": "Bengaluru (HAL)",
        "lat": 12.9499, "lon": 77.6681, "state": "Karnataka", "elevation_m": 920,
    },
    "Hyderabad (Begumpet)": {
        "id": "HYD", "name": "Hyderabad", "full_name": "Hyderabad (Begumpet)",
        "lat": 17.4531, "lon": 78.4677, "state": "Telangana", "elevation_m": 536,
    },
    "Jaipur (Sanganer)": {
        "id": "JAI", "name": "Jaipur", "full_name": "Jaipur (Sanganer)",
        "lat": 26.8240, "lon": 75.8120, "state": "Rajasthan", "elevation_m": 390,
    },
    "Ahmedabad": {
        "id": "AMD", "name": "Ahmedabad", "full_name": "Ahmedabad",
        "lat": 23.0666, "lon": 72.6323, "state": "Gujarat", "elevation_m": 55,
    },
    "Pune (Shivajinagar)": {
        "id": "PNQ", "name": "Pune", "full_name": "Pune (Shivajinagar)",
        "lat": 18.5314, "lon": 73.8446, "state": "Maharashtra", "elevation_m": 560,
    },
    "Lucknow (Amausi)": {
        "id": "LKO", "name": "Lucknow", "full_name": "Lucknow (Amausi)",
        "lat": 26.7606, "lon": 80.8893, "state": "Uttar Pradesh", "elevation_m": 128,
    },
    "Bhopal (Bairagarh)": {
        "id": "BHO", "name": "Bhopal", "full_name": "Bhopal (Bairagarh)",
        "lat": 23.2868, "lon": 77.3483, "state": "Madhya Pradesh", "elevation_m": 523,
    },
    "Thiruvananthapuram": {
        "id": "TRV", "name": "Thiruvananthapuram", "full_name": "Thiruvananthapuram",
        "lat": 8.4826, "lon": 76.9521, "state": "Kerala", "elevation_m": 64,
    },
}


def get_nearby_stations(station_name: str, max_distance_km: float = 800.0) -> List[str]:
    """Return names of stations within max_distance_km of the given station."""
    if station_name not in STATIONS:
        return []
    ref = STATIONS[station_name]
    nearby = []
    for name, info in STATIONS.items():
        if name == station_name:
            continue
        dist = _haversine(ref["lat"], ref["lon"], info["lat"], info["lon"])
        if dist <= max_distance_km:
            nearby.append(name)
    return nearby


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ==============================================================================
# 2. OPEN-METEO DATA PROVIDER (with source labeling)
# ==============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def fetch_weather_data(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Fetch from Open-Meteo API. Returns raw JSON or None."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m",
        "past_days": 3, "forecast_days": 1, "timezone": "Asia/Kolkata",
    }
    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def fetch_all_stations() -> Dict[str, Dict[str, Any]]:
    """
    Fetch data for all 12 stations. Each result includes a 'source' field.
    Returns dict keyed by station full_name.
    """
    results: Dict[str, Dict[str, Any]] = {}
    now = datetime.now()

    for name, info in STATIONS.items():
        data = fetch_weather_data(info["lat"], info["lon"])
        if data and "current" in data:
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            results[name] = {
                "id": info["id"],
                "name": info["name"],
                "full_name": name,
                "lat": info["lat"],
                "lon": info["lon"],
                "state": info.get("state", ""),
                "elevation_m": info.get("elevation_m", 0),
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("surface_pressure"),
                "wind_speed": current.get("wind_speed_10m", 0.0),
                "timestamp": current.get("time", now.isoformat()),
                "fetched_at": now.isoformat(),
                "hourly": hourly,
                "source": SOURCE_OPENMETEO,
                "status": "online",
            }
        else:
            # Deterministic synthetic fallback (65 hourly steps for full sequence length)
            base_temp = 28.0 + (info["lat"] % 5) - 2.0
            base_pres = 1012.0 - (info.get("elevation_m", 100) / 10.0)
            base_hum = 65.0 - (info["lat"] % 10)

            mock_times = [(now - timedelta(hours=64 - i)).strftime("%Y-%m-%dT%H:%M") for i in range(65)]
            mock_temps = [round(base_temp + 4.0 * math.sin((i - 6) * math.pi / 12), 1) for i in range(65)]
            mock_pres = [round(base_pres + 1.5 * math.cos(i * math.pi / 12), 1) for i in range(65)]
            mock_hum = [round(max(20.0, min(95.0, base_hum - 10.0 * math.sin((i - 6) * math.pi / 12))), 1) for i in range(65)]

            results[name] = {
                "id": info["id"],
                "name": info["name"],
                "full_name": name,
                "lat": info["lat"],
                "lon": info["lon"],
                "state": info.get("state", ""),
                "elevation_m": info.get("elevation_m", 0),
                "temperature": mock_temps[-1],
                "humidity": mock_hum[-1],
                "pressure": mock_pres[-1],
                "wind_speed": 10.5,
                "timestamp": now.isoformat(),
                "fetched_at": now.isoformat(),
                "hourly": {
                    "time": mock_times,
                    "temperature_2m": mock_temps,
                    "relative_humidity_2m": mock_hum,
                    "surface_pressure": mock_pres,
                },
                "source": SOURCE_FALLBACK,
                "status": "simulated",
            }

    return results


# ==============================================================================
# 3. REAL LSTM AUTOENCODER INFERENCE
# ==============================================================================

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class LSTMAutoencoder(nn.Module):
    """Mirror of train_models.py LSTMAutoencoder for loading weights."""
    def __init__(self, n_features=3, hidden_dim=64, bottleneck_dim=16, seq_len=60):
        super().__init__()
        self.seq_len = seq_len
        self.n_features = n_features
        self.enc_lstm1 = nn.LSTM(n_features, hidden_dim, batch_first=True)
        self.enc_lstm2 = nn.LSTM(hidden_dim, hidden_dim // 2, batch_first=True)
        self.enc_fc = nn.Linear(hidden_dim // 2, bottleneck_dim)
        self.dec_fc = nn.Linear(bottleneck_dim, hidden_dim // 2)
        self.dec_lstm1 = nn.LSTM(hidden_dim // 2, hidden_dim, batch_first=True)
        self.dec_lstm2 = nn.LSTM(hidden_dim, n_features, batch_first=True)

    def forward(self, x):
        out, _ = self.enc_lstm1(x)
        out, (h, _) = self.enc_lstm2(out)
        bottleneck = self.enc_fc(h.squeeze(0))
        dec = self.dec_fc(bottleneck)
        dec = dec.unsqueeze(1).repeat(1, self.seq_len, 1)
        dec, _ = self.dec_lstm1(dec)
        dec, _ = self.dec_lstm2(dec)
        return dec


@st.cache_resource(show_spinner=False)
def load_lstm_model() -> Optional[Dict[str, Any]]:
    """Load the production LSTM model and scaler."""
    if not TORCH_AVAILABLE:
        return {"status": "error", "error": "PyTorch not available"}
    prod_path = os.path.join(_MODEL_DIR, "lstm_ae_production.pt")
    if not os.path.exists(prod_path):
        alt = os.path.abspath(os.path.join(os.getcwd(), "ml", "models", "lstm_ae_production.pt"))
        if os.path.exists(alt):
            prod_path = alt
        else:
            return {"status": "error", "error": f"Model file not found at {prod_path}"}
    try:
        checkpoint = torch.load(prod_path, map_location="cpu", weights_only=False)
        model = LSTMAutoencoder(
            n_features=int(checkpoint.get("n_features", 3)),
            hidden_dim=int(checkpoint.get("hidden_dim", 64)),
            bottleneck_dim=int(checkpoint.get("bottleneck_dim", 16)),
            seq_len=int(checkpoint.get("seq_len", 60)),
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        return {
            "model": model,
            "threshold": float(checkpoint.get("threshold", 0.507435)),
            "scaler_mean": np.array(checkpoint.get("scaler_mean", [0, 0, 0])),
            "scaler_scale": np.array(checkpoint.get("scaler_scale", [1, 1, 1])),
            "seq_len": int(checkpoint.get("seq_len", 60)),
            "val_loss": float(checkpoint.get("val_loss", 0.06888)),
            "epochs_trained": int(checkpoint.get("epochs_trained", 50)),
            "status": "loaded",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_lstm_inference(
    hourly_data: Dict[str, List],
    model_info: Dict[str, Any],
    current_reading: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Run the real LSTM Autoencoder on hourly sequence data with station-relative baseline standardization.
    Returns dict with anomaly_score, threshold, is_anomaly, reconstruction_error per feature.
    """
    if not model_info or model_info.get("status") != "loaded":
        return None
    if not TORCH_AVAILABLE:
        return None

    temps = [x for x in hourly_data.get("temperature_2m", []) if x is not None]
    pres = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
    hum = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]

    min_len = min(len(temps), len(pres), len(hum))
    if min_len == 0:
        return None

    seq_len = int(model_info.get("seq_len", 60))
    if min_len < seq_len:
        pad = seq_len - min_len
        temps = [temps[0]] * pad + temps
        pres = [pres[0]] * pad + pres
        hum = [hum[0]] * pad + hum

    t_hist = np.array(temps[-seq_len:-1], dtype=np.float32)
    p_hist = np.array(pres[-seq_len:-1], dtype=np.float32)
    h_hist = np.array(hum[-seq_len:-1], dtype=np.float32)

    # Station-relative baseline statistics
    t_mean, t_std = float(np.mean(t_hist)), max(float(np.std(t_hist)), 0.8)
    p_mean, p_std = float(np.mean(p_hist)), max(float(np.std(p_hist)), 0.5)
    h_mean, h_std = float(np.mean(h_hist)), max(float(np.std(h_hist)), 2.0)

    cur_t = current_reading.get("temperature") if current_reading and current_reading.get("temperature") is not None else temps[-1]
    cur_p = current_reading.get("pressure") if current_reading and current_reading.get("pressure") is not None else pres[-1]
    cur_h = current_reading.get("humidity") if current_reading and current_reading.get("humidity") is not None else hum[-1]

    t_seq = np.append(t_hist, cur_t)
    p_seq = np.append(p_hist, cur_p)
    h_seq = np.append(h_hist, cur_h)

    # Standardized temporal dynamics sequence
    t_norm = (t_seq - t_mean) / t_std
    p_norm = (p_seq - p_mean) / p_std
    h_norm = (h_seq - h_mean) / h_std

    inp = np.stack([t_norm, p_norm, h_norm], axis=1)  # shape: (seq_len, 3)

    # Run inference through PyTorch LSTM Autoencoder
    model = model_info["model"]
    with torch.no_grad():
        x = torch.tensor(inp, dtype=torch.float32).unsqueeze(0)  # (1, seq_len, 3)
        reconstructed = model(x).squeeze(0).numpy()  # (seq_len, 3)

    # Pointwise reconstruction error at current reading
    step_errors = (inp[-1] - reconstructed[-1]) ** 2
    step_error = float(np.mean(step_errors))

    # Overall sequence MSE
    seq_errors = np.mean((inp - reconstructed) ** 2, axis=0)  # (3,)
    seq_error = float(np.mean(seq_errors))

    threshold = 2.50
    is_anom = step_error > threshold or seq_error > threshold

    return {
        "anomaly_score": round(step_error, 4),
        "threshold": round(threshold, 4),
        "is_anomaly": is_anom,
        "error_temperature": round(float(step_errors[0]), 4),
        "error_pressure": round(float(step_errors[1]), 4),
        "error_humidity": round(float(step_errors[2]), 4),
        "input_length": seq_len,
        "model_status": "inference_complete",
    }


# ==============================================================================
# 4. TRAINING REPORT (real metrics only)
# ==============================================================================

@st.cache_data(show_spinner=False)
def load_training_report() -> Optional[Dict[str, Any]]:
    """Load training_report.json for real model metrics."""
    target = _REPORT_PATH
    if not os.path.exists(target):
        alt = os.path.abspath(os.path.join(os.getcwd(), "ml", "models", "training_report.json"))
        if os.path.exists(alt):
            target = alt
        else:
            return None
    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ==============================================================================
# 5. MAGNUS DEW POINT
# ==============================================================================

def magnus_dewpoint(temp: Optional[float], humidity: Optional[float]) -> Optional[float]:
    """Dew point via Magnus-Tetens formula."""
    if temp is None or humidity is None:
        return None
    if humidity <= 0:
        return -999.0
    a, b = 17.27, 237.7
    clamped_rh = max(0.01, min(100.0, float(humidity)))
    try:
        gamma = (a * temp) / (b + temp) + math.log(clamped_rh / 100.0)
        if (a - gamma) == 0:
            return temp
        return round((b * gamma) / (a - gamma), 2)
    except (ValueError, ZeroDivisionError):
        return None


# ==============================================================================
# 6. 3-LAYER DETECTION ENGINE
# ==============================================================================

def detect_anomalies(
    reading: Dict[str, Any],
    hourly_data: Optional[Dict[str, List[Any]]] = None,
    model_info: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """
    3-Layer anomaly detection.
    Layer 1: Deterministic rules (WMO bounds, rate, frozen, dropout)
    Layer 2: LSTM Autoencoder (real model if available, Z-score fallback)
    Layer 3: Physics validator (Magnus dew-point, multivariate consistency)
    """
    alerts: List[Dict[str, str]] = []
    t = reading.get("temperature")
    p = reading.get("pressure")
    h = reading.get("humidity")

    # ------ LAYER 1: RULES ------
    if t is None:
        alerts.append({"type": "DROPOUT", "severity": SEV_CRITICAL,
            "detail": "Temperature sensor reading missing (null)",
            "layer": "Layer 1 — Rule Engine", "sensor": "Temperature"})
    if p is None:
        alerts.append({"type": "DROPOUT", "severity": SEV_CRITICAL,
            "detail": "Pressure sensor reading missing (null)",
            "layer": "Layer 1 — Rule Engine", "sensor": "Pressure"})
    if h is None:
        alerts.append({"type": "DROPOUT", "severity": SEV_CRITICAL,
            "detail": "Humidity sensor reading missing (null)",
            "layer": "Layer 1 — Rule Engine", "sensor": "Humidity"})

    if t == 0.0 and p == 0.0 and h == 0.0:
        alerts.append({"type": "FROZEN_SENSOR", "severity": SEV_CRITICAL,
            "detail": "All sensors locked at zero — complete hardware freeze",
            "layer": "Layer 1 — Rule Engine", "sensor": "All Sensors"})

    if t is not None and not (-50.0 <= t <= 60.0):
        alerts.append({"type": "OUT_OF_RANGE", "severity": SEV_CRITICAL,
            "detail": f"Temperature {t:.1f} C outside valid range [-50, 60] C",
            "layer": "Layer 1 — Rule Engine", "sensor": "Temperature"})
    if p is not None and not (870.0 <= p <= 1084.0):
        alerts.append({"type": "OUT_OF_RANGE", "severity": SEV_CRITICAL,
            "detail": f"Pressure {p:.1f} hPa outside valid range [870, 1084] hPa",
            "layer": "Layer 1 — Rule Engine", "sensor": "Pressure"})
    if h is not None and not (0.0 <= h <= 100.0):
        alerts.append({"type": "OUT_OF_RANGE", "severity": SEV_HIGH,
            "detail": f"Humidity {h:.1f}% outside physical limits [0, 100]%",
            "layer": "Layer 1 — Rule Engine", "sensor": "Humidity"})

    if hourly_data:
        times = hourly_data.get("time", [])
        temps = [x for x in hourly_data.get("temperature_2m", []) if x is not None]
        pressures = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
        humidities = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]

        # Find the reading for the previous hour relative to current timestamp
        prev_idx = -1
        cur_ts = reading.get("timestamp", "")
        if cur_ts and times:
            try:
                cur_dt = datetime.fromisoformat(cur_ts.replace("Z", ""))
                prev_hour_str = (cur_dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:00")
                if prev_hour_str in times:
                    prev_idx = times.index(prev_hour_str)
            except Exception:
                pass

        if prev_idx == -1 or prev_idx >= len(temps):
            # Fallback to the past data boundary (past 72h)
            prev_idx = min(71, len(temps) - 1) if temps else -1

        prev_t = temps[prev_idx] if temps and prev_idx >= 0 and prev_idx < len(temps) else None
        prev_p = pressures[prev_idx] if pressures and prev_idx >= 0 and prev_idx < len(pressures) else None
        prev_h = humidities[prev_idx] if humidities and prev_idx >= 0 and prev_idx < len(humidities) else None

        if prev_t is not None and t is not None:
            delta = abs(t - prev_t)
            if delta > 6.0:
                alerts.append({"type": "RATE_OF_CHANGE", "severity": SEV_HIGH,
                    "detail": f"Temperature step jump of {delta:.1f} C (previous hour: {prev_t:.1f} C)",
                    "layer": "Layer 1 — Rule Engine", "sensor": "Temperature"})
        if prev_p is not None and p is not None:
            delta = abs(p - prev_p)
            if delta > 5.0:
                alerts.append({"type": "RATE_OF_CHANGE", "severity": SEV_HIGH,
                    "detail": f"Pressure jump of {delta:.1f} hPa (previous hour: {prev_p:.1f} hPa)",
                    "layer": "Layer 1 — Rule Engine", "sensor": "Pressure"})
        if prev_h is not None and h is not None:
            delta = abs(h - prev_h)
            if delta > 25.0:
                alerts.append({"type": "RATE_OF_CHANGE", "severity": SEV_HIGH,
                    "detail": f"Humidity step jump of {delta:.1f}% (previous hour: {prev_h:.1f}%)",
                    "layer": "Layer 1 — Rule Engine", "sensor": "Humidity"})

        # Frozen detection (last 6 completed historical readings)
        for series, label in [(temps, "Temperature"), (pressures, "Pressure"), (humidities, "Humidity")]:
            if len(series) >= 6 and np.std(series[-6:]) < 0.01:
                alerts.append({"type": "FROZEN_SENSOR", "severity": SEV_HIGH,
                    "detail": f"{label} flatlined (std < 0.01 over last 6 readings at {series[-1]})",
                    "layer": "Layer 1 — Rule Engine", "sensor": label})

    # ------ LAYER 2: LSTM AUTOENCODER / Z-SCORE FALLBACK ------
    lstm_result = None
    if hourly_data and model_info and model_info.get("status") == "loaded":
        lstm_result = run_lstm_inference(hourly_data, model_info, reading)
        if lstm_result and lstm_result["is_anomaly"]:
            score = lstm_result["anomaly_score"]
            thresh = lstm_result["threshold"]
            # Find which feature contributes most
            errors = {
                "Temperature": lstm_result["error_temperature"],
                "Pressure": lstm_result["error_pressure"],
                "Humidity": lstm_result["error_humidity"],
            }
            top_sensor = max(errors, key=errors.get)
            alerts.append({"type": "TEMPORAL_ANOMALY", "severity": SEV_HIGH if score > thresh * 2 else SEV_MEDIUM,
                "detail": f"LSTM reconstruction error {score:.4f} exceeds threshold {thresh:.4f}. Primary contributor: {top_sensor} (error: {errors[top_sensor]:.4f})",
                "layer": "Layer 2 — LSTM Autoencoder", "sensor": top_sensor})
    elif hourly_data:
        # Z-score fallback when LSTM model is unavailable
        for vals_key, current_val, label in [
            ("temperature_2m", t, "Temperature"),
            ("surface_pressure", p, "Pressure"),
            ("relative_humidity_2m", h, "Humidity"),
        ]:
            vals = [x for x in hourly_data.get(vals_key, [])[-24:] if x is not None]
            if current_val is not None and len(vals) >= 6:
                mean_v = float(np.mean(vals))
                std_v = max(float(np.std(vals)), 0.1)
                z = abs(current_val - mean_v) / std_v
                if z > 3.0:
                    alerts.append({"type": "STATISTICAL_ANOMALY", "severity": SEV_HIGH if z > 4.5 else SEV_MEDIUM,
                        "detail": f"{label} z-score={z:.2f} (value: {current_val}, 24h mean: {mean_v:.1f}, std: {std_v:.2f}). Note: Z-score proxy — LSTM model not loaded.",
                        "layer": "Layer 2 — Statistical Proxy", "sensor": label})

    # ------ LAYER 3: PHYSICS ------
    if t is not None and h is not None:
        dp = magnus_dewpoint(t, h)
        if dp is not None and dp > (t + 0.5):
            alerts.append({"type": "PHYSICS_VIOLATION", "severity": SEV_CRITICAL,
                "detail": f"Dew point ({dp:.1f} C) exceeds ambient temperature ({t:.1f} C) — thermodynamic violation",
                "layer": "Layer 3 — Physics Validator", "sensor": "Temperature / Humidity"})

    if hourly_data and t is not None and p is not None and h is not None:
        th = [x for x in hourly_data.get("temperature_2m", []) if x is not None]
        ph = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
        hh = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]
        if len(th) >= 3 and len(ph) >= 3 and len(hh) >= 3:
            dt, dp_val, dh = t - th[-3], p - ph[-3], h - hh[-3]
            if dt <= -2.5 and dp_val >= 1.0 and dh >= 12.0:
                alerts.append({"type": "METEOROLOGICAL_EVENT", "severity": SEV_INFO,
                    "detail": f"Storm signature: dT={dt:+.1f} C, dP={dp_val:+.1f} hPa, dRH={dh:+.1f}% — classified as natural event, NOT sensor fault",
                    "layer": "Layer 3 — Physics Validator", "sensor": "Multivariate"})

    return alerts


# ==============================================================================
# 7. SPATIAL VALIDATION
# ==============================================================================

def sea_level_pressure(p: Optional[float], elev_m: float, temp_c: Optional[float] = None) -> Optional[float]:
    """Reduce surface pressure to sea-level equivalent using standard barometric formula."""
    if p is None:
        return None
    t_k = (temp_c if temp_c is not None else 25.0) + 273.15
    return p * (1.0 - (0.0065 * elev_m) / (t_k + 0.0065 * elev_m)) ** -5.257


def compute_spatial_context(
    station_name: str,
    all_data: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare a station's readings against nearby stations with sea-level pressure normalization.
    Returns spatial deviation and consistency assessment.
    """
    if station_name not in all_data:
        return {"available": False}

    station = all_data[station_name]
    nearby_names = get_nearby_stations(station_name)
    nearby_with_data = [n for n in nearby_names if n in all_data]

    if not nearby_with_data:
        return {"available": False, "reason": "No nearby stations with data"}

    nearby_temps, nearby_slp, nearby_hum = [], [], []
    for n in nearby_with_data:
        d = all_data[n]
        if d.get("temperature") is not None:
            nearby_temps.append(d["temperature"])
        if d.get("pressure") is not None:
            elev = STATIONS.get(n, {}).get("elevation_m", 0)
            slp = sea_level_pressure(d["pressure"], elev, d.get("temperature"))
            if slp is not None:
                nearby_slp.append(slp)
        if d.get("humidity") is not None:
            nearby_hum.append(d["humidity"])

    result: Dict[str, Any] = {
        "available": True,
        "nearby_count": len(nearby_with_data),
        "nearby_stations": [STATIONS[n]["name"] for n in nearby_with_data],
    }

    st_t = station.get("temperature")
    st_p = station.get("pressure")
    st_h = station.get("humidity")
    st_elev = STATIONS.get(station_name, {}).get("elevation_m", 0)

    if st_t is not None and nearby_temps:
        avg_t = np.mean(nearby_temps)
        dev_t = st_t - avg_t
        result["temp_regional_avg"] = round(float(avg_t), 1)
        result["temp_deviation"] = round(float(dev_t), 1)
        result["temp_consistent"] = abs(dev_t) < 8.0  # 8 C threshold for spatial anomaly

    st_slp = sea_level_pressure(st_p, st_elev, st_t)
    if st_slp is not None and nearby_slp:
        avg_slp = np.mean(nearby_slp)
        dev_p = st_slp - avg_slp
        result["pres_regional_avg"] = round(float(avg_slp), 1)
        result["pres_deviation"] = round(float(dev_p), 1)
        result["pres_consistent"] = abs(dev_p) < 8.0  # 8 hPa sea-level deviation threshold

    if st_h is not None and nearby_hum:
        avg_h = np.mean(nearby_hum)
        dev_h = st_h - avg_h
        result["hum_regional_avg"] = round(float(avg_h), 1)
        result["hum_deviation"] = round(float(dev_h), 1)
        result["hum_consistent"] = abs(dev_h) < 25.0

    # Overall spatial consistency
    checks = [result.get("temp_consistent", True), result.get("pres_consistent", True), result.get("hum_consistent", True)]
    result["overall_consistent"] = all(checks)

    return result


# ==============================================================================
# 8. RISK SCORING (deterministic, documented formula)
# ==============================================================================

def compute_risk_score(
    alerts: List[Dict[str, str]],
    spatial: Optional[Dict[str, Any]] = None,
    data_quality: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic risk score from 0-100.
    """
    components = {"rule_violations": 0, "temporal_anomaly": 0, "spatial_deviation": 0, "data_quality": 0}

    for a in alerts:
        layer = a.get("layer", "")
        sev = a.get("severity", "")
        if "Rule Engine" in layer:
            components["rule_violations"] += 15 if sev == SEV_CRITICAL else 8
        elif "LSTM" in layer:
            components["temporal_anomaly"] += 20
        elif "Statistical" in layer:
            components["temporal_anomaly"] += 12
        elif "Physics" in layer and a.get("type") != "METEOROLOGICAL_EVENT":
            components["rule_violations"] += 15

    if spatial and spatial.get("available") and not spatial.get("overall_consistent", True):
        components["spatial_deviation"] = 15

    if data_quality:
        if not data_quality.get("fresh", True):
            components["data_quality"] += 5
        if not data_quality.get("complete", True):
            components["data_quality"] += 5

    total = min(100, sum(components.values()))

    # Map status level from active alerts and risk score
    if alerts:
        if total >= 70 or any(a.get("severity") == SEV_CRITICAL for a in alerts):
            level = STATUS_CRITICAL
        elif total >= 40 or any(a.get("severity") == SEV_HIGH for a in alerts):
            level = STATUS_HIGH_RISK
        else:
            level = STATUS_WARNING
    else:
        # If no active detection alerts fired, the station is Healthy
        level = STATUS_HEALTHY
        total = min(total, 15)  # Cap baseline background score

    return {"score": total, "level": level, "components": components}


# ==============================================================================
# 9. DATA QUALITY
# ==============================================================================

def assess_data_quality(station_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess freshness, completeness, validity, and consistency of a station reading."""
    now = datetime.now()
    result = {"score": 100, "issues": []}

    # Freshness
    ts_str = station_data.get("timestamp", "")
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00").replace("+05:30", ""))
        age_seconds = (now - ts).total_seconds()
        result["fresh"] = age_seconds < 600  # 10 min
        result["age_seconds"] = round(age_seconds)
        if not result["fresh"]:
            result["issues"].append("Data is stale")
            result["score"] -= 15
    except Exception:
        result["fresh"] = True
        result["age_seconds"] = 0

    # Completeness
    missing = []
    for k in ["temperature", "pressure", "humidity"]:
        if station_data.get(k) is None:
            missing.append(k)
    result["complete"] = len(missing) == 0
    if missing:
        result["issues"].append(f"Missing: {', '.join(missing)}")
        result["score"] -= 20 * len(missing)

    # Validity
    t, p, h = station_data.get("temperature"), station_data.get("pressure"), station_data.get("humidity")
    valid = True
    if t is not None and not (-50 <= t <= 60):
        valid = False
    if p is not None and not (870 <= p <= 1084):
        valid = False
    if h is not None and not (0 <= h <= 100):
        valid = False
    result["valid"] = valid
    if not valid:
        result["issues"].append("Values outside valid range")
        result["score"] -= 20

    # Consistency
    if t is not None and h is not None:
        dp = magnus_dewpoint(t, h)
        result["consistent"] = dp is None or dp <= t + 0.5
        if not result["consistent"]:
            result["issues"].append("Physics inconsistency (dew point > ambient)")
            result["score"] -= 10
    else:
        result["consistent"] = True

    result["score"] = max(0, result["score"])
    result["source"] = station_data.get("source", "Unknown")
    return result


# ==============================================================================
# 10. ALERT EXPLANATION GENERATOR
# ==============================================================================

def generate_explanation(
    station_name: str,
    reading: Dict[str, Any],
    alerts: List[Dict[str, str]],
    spatial: Optional[Dict[str, Any]] = None,
    lstm_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a human-readable explanation of why an alert fired.
    Returns dict with reasons, conclusion, and recommended_action.
    """
    if not alerts:
        return {
            "reasons": ["All detection layers passed"],
            "conclusion": "Station readings are normal",
            "recommended_action": "No action required",
            "classification": "Normal",
        }

    reasons = []
    layers_fired = set()
    sensors_affected = set()

    for a in alerts:
        if a.get("type") == "METEOROLOGICAL_EVENT":
            continue
        reasons.append(a.get("detail", ""))
        layers_fired.add(a.get("layer", ""))
        sensors_affected.add(a.get("sensor", ""))

    # Determine classification
    has_rule = any("Rule Engine" in l for l in layers_fired)
    has_ml = any("LSTM" in l or "Statistical" in l for l in layers_fired)
    has_physics = any("Physics" in l for l in layers_fired)
    is_storm = any(a.get("type") == "METEOROLOGICAL_EVENT" for a in alerts)
    spatial_ok = spatial.get("overall_consistent", True) if spatial and spatial.get("available") else True

    if is_storm and not has_physics:
        classification = "Probable environmental event"
        conclusion = "Multivariate pattern consistent with a natural meteorological event. Neighboring stations may show similar trends."
        action = "Monitor — likely genuine weather change, not a sensor fault."
    elif has_ml and not spatial_ok:
        classification = "Probable sensor fault"
        conclusion = f"Temporal deviation detected by ML, and neighboring stations do NOT show similar values. Likely a localized sensor issue at {station_name}."
        action = "Investigate sensor hardware. Compare with field readings. Consider recalibration."
    elif has_rule and has_ml:
        classification = "Suspicious — multiple layers triggered"
        conclusion = "Both rule-based and temporal analysis flagged this reading. High confidence of anomaly."
        action = "Immediate investigation required. Check sensor connections and environmental conditions."
    elif has_rule:
        classification = "Rule violation"
        conclusion = "Reading violates physical/operational bounds."
        action = "Verify sensor and data path integrity."
    elif has_ml:
        classification = "Temporal deviation"
        conclusion = "Reading deviates from the learned temporal profile."
        action = "Monitor trend. If persistent, investigate sensor calibration."
    else:
        classification = "Anomaly detected"
        conclusion = "An issue was detected but requires further analysis."
        action = "Review station data and recent trends."

    return {
        "reasons": reasons,
        "conclusion": conclusion,
        "recommended_action": action,
        "classification": classification,
        "layers_fired": list(layers_fired),
        "sensors_affected": list(sensors_affected),
        "spatial_consistent": spatial_ok,
    }


# ==============================================================================
# 11. LAYER STATUS SUMMARY
# ==============================================================================

def get_layer_status(alerts: List[Dict[str, str]], lstm_result: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, str]]:
    """Return pass/fail status for each detection layer."""
    l1_alerts = [a for a in alerts if "Rule Engine" in a.get("layer", "")]
    l2_alerts = [a for a in alerts if "LSTM" in a.get("layer", "") or "Statistical" in a.get("layer", "")]
    l3_alerts = [a for a in alerts if "Physics" in a.get("layer", "")]

    l1 = {"status": "FAIL" if l1_alerts else "PASS",
          "detail": f"{len(l1_alerts)} rule violation(s)" if l1_alerts else "All rules passed",
          "color": COLOR_CRITICAL if l1_alerts else COLOR_HEALTHY}

    if lstm_result and lstm_result.get("model_status") == "inference_complete":
        l2_label = "LSTM Autoencoder"
        if lstm_result["is_anomaly"]:
            l2 = {"status": "ANOMALY", "detail": f"Score: {lstm_result['anomaly_score']:.4f} > {lstm_result['threshold']:.4f}",
                  "color": COLOR_CRITICAL, "method": l2_label}
        else:
            l2 = {"status": "PASS", "detail": f"Score: {lstm_result['anomaly_score']:.4f} < {lstm_result['threshold']:.4f}",
                  "color": COLOR_HEALTHY, "method": l2_label}
    elif l2_alerts:
        l2 = {"status": "ANOMALY", "detail": f"{len(l2_alerts)} statistical anomaly(s)",
              "color": COLOR_WARNING, "method": "Z-score Proxy"}
    else:
        l2 = {"status": "PASS", "detail": "No temporal anomaly",
              "color": COLOR_HEALTHY, "method": "Z-score Proxy" if not lstm_result else "LSTM Autoencoder"}

    l3_non_storm = [a for a in l3_alerts if a.get("type") != "METEOROLOGICAL_EVENT"]
    l3 = {"status": "FAIL" if l3_non_storm else "PASS",
          "detail": f"{len(l3_non_storm)} physics violation(s)" if l3_non_storm else "Physically consistent",
          "color": COLOR_CRITICAL if l3_non_storm else COLOR_HEALTHY}

    return {"layer1": l1, "layer2": l2, "layer3": l3}


# ==============================================================================
# 12. STATION STATUS SUMMARY (full)
# ==============================================================================

def get_station_status(
    station_name: str,
    station_data: Dict[str, Any],
    all_data: Optional[Dict[str, Dict[str, Any]]] = None,
    model_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Comprehensive station status with all layers, spatial context, risk, quality."""
    reading = {
        "temperature": station_data.get("temperature"),
        "pressure": station_data.get("pressure"),
        "humidity": station_data.get("humidity"),
    }
    hourly = station_data.get("hourly")

    alerts = detect_anomalies(reading, hourly, model_info)
    dp = magnus_dewpoint(reading["temperature"], reading["humidity"])
    spatial = compute_spatial_context(station_name, all_data) if all_data else {"available": False}
    quality = assess_data_quality(station_data)

    lstm_result = None
    if hourly and model_info and model_info.get("status") == "loaded":
        lstm_result = run_lstm_inference(hourly, model_info, reading)

    risk = compute_risk_score(alerts, spatial, quality)
    layer_status = get_layer_status(alerts, lstm_result)
    explanation = generate_explanation(station_name, reading, alerts, spatial, lstm_result)

    return {
        "station": station_name,
        "id": station_data.get("id", "N/A"),
        "status": risk["level"],
        "color": {STATUS_HEALTHY: COLOR_HEALTHY, STATUS_WARNING: COLOR_WARNING,
                  STATUS_HIGH_RISK: COLOR_HIGH, STATUS_CRITICAL: COLOR_CRITICAL,
                  STATUS_OFFLINE: COLOR_OFFLINE}.get(risk["level"], COLOR_OFFLINE),
        "temperature": reading["temperature"],
        "pressure": reading["pressure"],
        "humidity": reading["humidity"],
        "dew_point": dp,
        "source": station_data.get("source", "Unknown"),
        "timestamp": station_data.get("timestamp", ""),
        "alerts": alerts,
        "alert_count": len([a for a in alerts if a.get("type") != "METEOROLOGICAL_EVENT"]),
        "risk": risk,
        "quality": quality,
        "spatial": spatial,
        "layer_status": layer_status,
        "lstm_result": lstm_result,
        "explanation": explanation,
    }


# ==============================================================================
# 13. FAULT INJECTION
# ==============================================================================

def inject_fault(reading: Dict[str, Any], fault_type: str) -> Dict[str, Any]:
    """Inject synthetic sensor fault. Deep copies to avoid mutation."""
    r = copy.deepcopy(reading)
    f = (fault_type or "").strip().lower()

    if f == "spike":
        curr = r.get("temperature") or 28.0
        r["temperature"] = curr + 25.0
    elif f == "freeze":
        r["temperature"] = 0.0
        r["pressure"] = 0.0
        r["humidity"] = 0.0
    elif f == "drift":
        curr = r.get("humidity") or 50.0
        r["humidity"] = min(100.0, curr + 30.0)
    elif f == "dropout":
        r["temperature"] = None
        r["pressure"] = None
        r["humidity"] = None
    elif f == "storm":
        r["temperature"] = round((r.get("temperature") or 32.0) - 7.0, 1)
        r["pressure"] = round((r.get("pressure") or 1008.0) + 3.5, 1)
        r["humidity"] = round(min(100.0, (r.get("humidity") or 55.0) + 35.0), 1)

    r["source"] = SOURCE_SIMULATION
    return r


# ==============================================================================
# 14. DESIGN SYSTEM (CSS)
# ==============================================================================

CUSTOM_CSS = """
/* SkyGuard AI — Professional Operational Design System */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Reduce Streamlit default padding */
.block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
header[data-testid="stHeader"] { height: 0; }

/* Metric cards */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
div[data-testid="stMetric"] label {
    color: #6B7280 !important;
    font-weight: 500 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
div[data-testid="stMetricValue"] {
    color: #111827 !important;
    font-weight: 600 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1F2937;
    border-right: 1px solid #374151;
}
section[data-testid="stSidebar"] * {
    color: #D1D5DB !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label {
    color: #9CA3AF !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Buttons */
.stButton > button {
    background: #111827;
    color: #FFFFFF;
    font-weight: 600;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 0.85rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #1F2937;
    border-color: #4B5563;
}
.stButton > button[kind="primary"] {
    background: #059669;
    border-color: #059669;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background-color: #F3F4F6;
    border-radius: 6px;
    padding: 2px;
    border: 1px solid #E5E7EB;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 4px;
    color: #6B7280;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 6px 14px;
}
.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #111827 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}
"""


def apply_styling() -> None:
    """Inject the design system CSS."""
    st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)


# ==============================================================================
# 15. UI HELPER COMPONENTS
# ==============================================================================

def status_badge(status: str, size: str = "sm") -> str:
    """Return HTML for a status badge."""
    colors = {
        STATUS_HEALTHY: (COLOR_HEALTHY, "#F0FDF4", "#166534"),
        STATUS_WARNING: (COLOR_WARNING, "#FFFBEB", "#92400E"),
        STATUS_HIGH_RISK: (COLOR_HIGH, "#FFF7ED", "#9A3412"),
        STATUS_CRITICAL: (COLOR_CRITICAL, "#FEF2F2", "#991B1B"),
        STATUS_OFFLINE: (COLOR_OFFLINE, "#F3F4F6", "#374151"),
    }
    border, bg, text = colors.get(status, (COLOR_OFFLINE, "#F3F4F6", "#374151"))
    icons = {STATUS_HEALTHY: "checkmark", STATUS_WARNING: "!", STATUS_HIGH_RISK: "!!", STATUS_CRITICAL: "!!!", STATUS_OFFLINE: "o"}
    icon = {"HEALTHY": "✓", "WARNING": "!", "HIGH_RISK": "!!", "CRITICAL": "!!!", "OFFLINE": "○"}.get(status, "?")
    label = status.replace("_", " ").title()
    pad = "3px 10px" if size == "sm" else "5px 14px"
    fs = "0.7rem" if size == "sm" else "0.8rem"
    return f'<span style="display:inline-flex;align-items:center;gap:4px;background:{bg};color:{text};border:1px solid {border};border-radius:4px;padding:{pad};font-size:{fs};font-weight:600;letter-spacing:0.02em;">{icon} {label}</span>'


def source_badge(source: str) -> str:
    """Return HTML for a data source badge."""
    colors = {
        SOURCE_OPENMETEO: ("#2563EB", "#EFF6FF", "#1E40AF"),
        SOURCE_HARDWARE: ("#059669", "#F0FDF4", "#065F46"),
        SOURCE_SIMULATION: ("#D97706", "#FFFBEB", "#92400E"),
        SOURCE_CACHED: ("#6B7280", "#F3F4F6", "#374151"),
        SOURCE_FALLBACK: ("#9333EA", "#FAF5FF", "#6B21A8"),
    }
    border, bg, text = colors.get(source, ("#6B7280", "#F3F4F6", "#374151"))
    return f'<span style="display:inline-flex;align-items:center;background:{bg};color:{text};border:1px solid {border};border-radius:4px;padding:2px 8px;font-size:0.7rem;font-weight:500;">{source}</span>'


def layer_badge(layer: str) -> str:
    """Return HTML for a detection layer badge."""
    return f'<span style="display:inline-flex;background:#F3F4F6;color:#374151;border:1px solid #D1D5DB;border-radius:4px;padding:2px 8px;font-size:0.68rem;font-weight:500;font-family:\'JetBrains Mono\',monospace;">{layer}</span>'


def severity_icon(severity: str) -> str:
    """Return icon for severity level."""
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "ℹ️"}.get(severity, "⚪")


def card_html(title: str, content: str, border_color: str = "#E5E7EB", icon: str = "") -> str:
    """Generic white card HTML."""
    icon_html = f'<span style="margin-right:6px;">{icon}</span>' if icon else ""
    return f'''<div style="background:#FFFFFF;border:1px solid {border_color};border-radius:8px;padding:16px 20px;box-shadow:0 1px 2px rgba(0,0,0,0.04);margin-bottom:12px;">
    <div style="font-weight:600;font-size:0.9rem;color:#111827;margin-bottom:8px;">{icon_html}{title}</div>
    <div style="color:#374151;font-size:0.85rem;line-height:1.5;">{content}</div>
</div>'''
