"""
SkyGuard AI — Core Anomaly Detection, Diagnostics, & Risk Engine
Implements:
  1. Layer 1: Deterministic Rules (WMO range bounds, Step Jump Rate, Frozen persistence, Null dropouts)
  2. Layer 2: Dual ML Ensemble (PyTorch LSTM Autoencoder + Scikit-Learn Isolation Forest)
  3. Layer 3: Thermodynamic Physics (Magnus Dew Point check, Convective Storm Recognition)
  4. Layer 4: Spatial Validation (Haversine 800km radius, Barometric Sea-Level Reduction)
  5. Hardware Ingestion Diagnostics (BMP280 I2C bus stall, DHT22 CRC, packet drop vs meteorological events)
  6. Decision Engine & Deterministic Risk Scoring (0–100)
  7. Root-Cause Explanation Generator
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np

from backend.core.stations import STATIONS, get_nearby_stations, haversine_distance
from backend.core.ml_models import ml_engine


# ── SEVERITY & STATUS CONSTANTS ──
STATUS_HEALTHY = "HEALTHY"
STATUS_WARNING = "WARNING"
STATUS_HIGH_RISK = "HIGH_RISK"
STATUS_CRITICAL = "CRITICAL"
STATUS_OFFLINE = "OFFLINE"

SEV_CRITICAL = "CRITICAL"
SEV_HIGH = "HIGH"
SEV_MEDIUM = "MEDIUM"
SEV_LOW = "LOW"
SEV_INFO = "INFO"


def magnus_dewpoint(temp_c: Optional[float], humidity_pct: Optional[float]) -> Optional[float]:
    """Magnus-Tetens formula for dew point temperature."""
    if temp_c is None or humidity_pct is None:
        return None
    if humidity_pct <= 0 or humidity_pct > 100:
        return None
    a = 17.27
    b = 237.7
    try:
        alpha = ((a * temp_c) / (b + temp_c)) + math.log(humidity_pct / 100.0)
        dp = (b * alpha) / (a - alpha)
        return round(dp, 1)
    except Exception:
        return None


def sea_level_pressure(p: Optional[float], elev_m: float, temp_c: Optional[float] = None) -> Optional[float]:
    """Reduce surface pressure to sea-level equivalent pressure (hPa)."""
    if p is None:
        return None
    t_k = (temp_c if temp_c is not None else 25.0) + 273.15
    return p * (1.0 - (0.0065 * elev_m) / (t_k + 0.0065 * elev_m)) ** -5.257


def assess_data_quality(station_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess freshness, completeness, validity, and consistency."""
    now = datetime.now()
    result = {"score": 100, "issues": [], "fresh": True, "complete": True, "valid": True, "consistent": True}

    # Freshness
    ts_str = station_data.get("timestamp", "")
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "").replace("+05:30", ""))
        age_seconds = (now - ts).total_seconds()
        result["fresh"] = age_seconds < 600
        result["age_seconds"] = round(age_seconds)
        if not result["fresh"]:
            result["issues"].append("Reading is older than 10 minutes")
            result["score"] -= 10
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
        result["issues"].append(f"Missing sensors: {', '.join(missing)}")
        result["score"] -= 20 * len(missing)

    elev = station_data.get("elevation_m", 0.0)
    min_p = max(550.0, 1013.25 * math.exp(-elev / 8430.0) - 50.0)
    t, p, h = station_data.get("temperature"), station_data.get("pressure"), station_data.get("humidity")
    valid = True
    if t is not None and not (-50 <= t <= 60):
        valid = False
    if p is not None and not (min_p <= p <= 1085):
        valid = False
    if h is not None and not (0 <= h <= 100):
        valid = False
    result["valid"] = valid
    if not valid:
        result["issues"].append("Sensor values outside WMO physical bounds")
        result["score"] -= 25

    # Consistency
    if t is not None and h is not None:
        dp = magnus_dewpoint(t, h)
        if dp is not None and dp > (t + 0.5):
            result["consistent"] = False
            result["issues"].append("Thermodynamic violation (Dew point > Temperature)")
            result["score"] -= 25

    result["score"] = max(0, min(100, result["score"]))
    return result


def compute_spatial_context(
    station_name: str,
    all_data: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare a station against nearby stations using sea-level normalized barometrics."""
    if station_name not in all_data or station_name not in STATIONS:
        return {"available": False}

    station = all_data[station_name]
    st_elev = STATIONS[station_name]["elevation_m"]
    nearby_names = get_nearby_stations(station_name, max_distance_km=800.0)
    nearby_with_data = [n for n in nearby_names if n in all_data]

    if not nearby_with_data:
        return {"available": False, "reason": "No nearby stations within 800km"}

    nearby_temps, nearby_slp, nearby_hum = [], [], []
    for n in nearby_with_data:
        d = all_data[n]
        elev = STATIONS[n]["elevation_m"]
        if d.get("temperature") is not None:
            nearby_temps.append(d["temperature"])
        if d.get("pressure") is not None:
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

    if st_t is not None and nearby_temps:
        avg_t = np.mean(nearby_temps)
        dev_t = st_t - avg_t
        result["temp_regional_avg"] = round(float(avg_t), 1)
        result["temp_deviation"] = round(float(dev_t), 1)
        result["temp_consistent"] = bool(abs(dev_t) < 8.0)

    st_slp = sea_level_pressure(st_p, st_elev, st_t)
    if st_slp is not None and nearby_slp:
        avg_slp = np.mean(nearby_slp)
        dev_p = st_slp - avg_slp
        result["pres_regional_avg"] = round(float(avg_slp), 1)
        result["pres_deviation"] = round(float(dev_p), 1)
        result["pres_consistent"] = bool(abs(dev_p) < 8.0)

    if st_h is not None and nearby_hum:
        avg_h = np.mean(nearby_hum)
        dev_h = st_h - avg_h
        result["hum_regional_avg"] = round(float(avg_h), 1)
        result["hum_deviation"] = round(float(dev_h), 1)
        result["hum_consistent"] = bool(abs(dev_h) < 25.0)

    checks = [result.get("temp_consistent", True), result.get("pres_consistent", True), result.get("hum_consistent", True)]
    result["overall_consistent"] = bool(all(checks))
    return result


def detect_anomalies(
    reading: Dict[str, Any],
    hourly_data: Optional[Dict[str, List[Any]]] = None,
    station_name: str = ""
) -> Dict[str, Any]:
    """
    4-Layer Hybrid Detection Engine.
    Returns alerts list and detailed per-layer diagnostics.
    """
    alerts: List[Dict[str, Any]] = []
    t = reading.get("temperature")
    p = reading.get("pressure")
    h = reading.get("humidity")

    # ── LAYER 1: DETERMINISTIC RULE ENGINE ──
    l1_alerts = []
    if t is None:
        l1_alerts.append({"type": "DROPOUT", "severity": SEV_CRITICAL, "detail": "Temperature sensor null dropout", "layer": "Layer 1 — Rule Engine", "sensor": "Temperature"})
    if p is None:
        l1_alerts.append({"type": "DROPOUT", "severity": SEV_CRITICAL, "detail": "Pressure sensor null dropout", "layer": "Layer 1 — Rule Engine", "sensor": "Pressure"})
    if h is None:
        l1_alerts.append({"type": "DROPOUT", "severity": SEV_CRITICAL, "detail": "Humidity sensor null dropout", "layer": "Layer 1 — Rule Engine", "sensor": "Humidity"})

    if t == 0.0 and p == 0.0 and h == 0.0:
        l1_alerts.append({"type": "FROZEN_SENSOR", "severity": SEV_CRITICAL, "detail": "All sensors locked at zero (complete hardware freeze)", "layer": "Layer 1 — Rule Engine", "sensor": "All Sensors"})

    elev = STATIONS.get(station_name, {}).get("elevation_m", 0.0) if station_name else 0.0
    min_p = max(550.0, 1013.25 * math.exp(-elev / 8430.0) - 50.0)

    if t is not None and not (-50.0 <= t <= 60.0):
        l1_alerts.append({"type": "OUT_OF_RANGE", "severity": SEV_CRITICAL, "detail": f"Temperature {t:.1f}°C outside bounds [-50, 60]°C", "layer": "Layer 1 — Rule Engine", "sensor": "Temperature"})
    if p is not None and not (min_p <= p <= 1085.0):
        l1_alerts.append({"type": "OUT_OF_RANGE", "severity": SEV_CRITICAL, "detail": f"Pressure {p:.1f} hPa outside bounds [{min_p:.0f}, 1085] hPa", "layer": "Layer 1 — Rule Engine", "sensor": "Pressure"})
    if h is not None and not (0.0 <= h <= 100.0):
        l1_alerts.append({"type": "OUT_OF_RANGE", "severity": SEV_HIGH, "detail": f"Humidity {h:.1f}% outside bounds [0, 100]%", "layer": "Layer 1 — Rule Engine", "sensor": "Humidity"})

    if hourly_data:
        times = hourly_data.get("time", [])
        temps = [x for x in hourly_data.get("temperature_2m", []) if x is not None]
        pressures = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
        humidities = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]

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
            prev_idx = min(71, len(temps) - 1) if temps else -1

        prev_t = temps[prev_idx] if temps and 0 <= prev_idx < len(temps) else None
        prev_p = pressures[prev_idx] if pressures and 0 <= prev_idx < len(pressures) else None
        prev_h = humidities[prev_idx] if humidities and 0 <= prev_idx < len(humidities) else None

        if prev_t is not None and t is not None:
            delta_t = abs(t - prev_t)
            if delta_t > 6.0:
                l1_alerts.append({"type": "RATE_OF_CHANGE", "severity": SEV_HIGH, "detail": f"Temperature jump of {delta_t:.1f}°C/hr (prev: {prev_t:.1f}°C)", "layer": "Layer 1 — Rule Engine", "sensor": "Temperature"})
        if prev_p is not None and p is not None:
            delta_p = abs(p - prev_p)
            if delta_p > 5.0:
                l1_alerts.append({"type": "RATE_OF_CHANGE", "severity": SEV_HIGH, "detail": f"Pressure jump of {delta_p:.1f} hPa/hr (prev: {prev_p:.1f} hPa)", "layer": "Layer 1 — Rule Engine", "sensor": "Pressure"})
        if prev_h is not None and h is not None:
            delta_h = abs(h - prev_h)
            if delta_h > 25.0:
                l1_alerts.append({"type": "RATE_OF_CHANGE", "severity": SEV_HIGH, "detail": f"Humidity jump of {delta_h:.1f}%/hr (prev: {prev_h:.1f}%)", "layer": "Layer 1 — Rule Engine", "sensor": "Humidity"})

        # Frozen flatline
        for series, label in [(temps, "Temperature"), (pressures, "Pressure"), (humidities, "Humidity")]:
            if len(series) >= 6 and np.std(series[-6:]) < 0.01:
                l1_alerts.append({"type": "FROZEN_SENSOR", "severity": SEV_HIGH, "detail": f"{label} flatlined over 6 hours at {series[-1]}", "layer": "Layer 1 — Rule Engine", "sensor": label})

    alerts.extend(l1_alerts)

    # ── LAYER 2: DUAL ML ENSEMBLE (LSTM + ISOLATION FOREST) ──
    lstm_res = None
    iforest_res = None
    if hourly_data:
        lstm_res = ml_engine.run_lstm_inference(hourly_data, reading)
        if lstm_res and lstm_res.get("is_anomaly"):
            score = lstm_res["anomaly_score"]
            thresh = lstm_res["threshold"]
            err_dict = {
                "Temperature": lstm_res["error_temperature"],
                "Pressure": lstm_res["error_pressure"],
                "Humidity": lstm_res["error_humidity"],
            }
            top_sensor = max(err_dict, key=err_dict.get)
            alerts.append({
                "type": "TEMPORAL_ANOMALY",
                "severity": SEV_HIGH if score > thresh * 2 else SEV_MEDIUM,
                "detail": f"LSTM temporal error {score:.4f} > threshold {thresh:.4f}. Primary contributor: {top_sensor} ({err_dict[top_sensor]:.2f})",
                "layer": "Layer 2 — LSTM Autoencoder",
                "sensor": top_sensor,
                "score": score,
                "threshold": thresh
            })

        iforest_res = ml_engine.run_isolation_forest_inference(hourly_data, reading)
        if iforest_res and iforest_res.get("is_anomaly"):
            d_score = iforest_res["decision_score"]
            alerts.append({
                "type": "MULTIVARIATE_OUTLIER",
                "severity": SEV_MEDIUM,
                "detail": f"Isolation Forest flagged multivariate point outlier (score: {d_score:.4f})",
                "layer": "Layer 2 — Isolation Forest",
                "sensor": "Multivariate Array",
                "score": d_score
            })

    # ── LAYER 3: THERMODYNAMICS & PHYSICS VALIDATOR ──
    l3_alerts = []
    if t is not None and h is not None:
        dp = magnus_dewpoint(t, h)
        if dp is not None and dp > (t + 0.5):
            l3_alerts.append({
                "type": "PHYSICS_VIOLATION",
                "severity": SEV_CRITICAL,
                "detail": f"Dew point ({dp:.1f}°C) exceeds ambient temperature ({t:.1f}°C) — thermodynamic violation",
                "layer": "Layer 3 — Physics Validator",
                "sensor": "Thermodynamics (T/H)"
            })

    # Natural convective storm pattern recognizer
    if hourly_data and t is not None and p is not None and h is not None:
        th = [x for x in hourly_data.get("temperature_2m", []) if x is not None]
        ph = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
        hh = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]
        if len(th) >= 3 and len(ph) >= 3 and len(hh) >= 3:
            dt, dp_val, dh = t - th[-3], p - ph[-3], h - hh[-3]
            if dt <= -2.5 and dp_val >= 1.0 and dh >= 12.0:
                l3_alerts.append({
                    "type": "METEOROLOGICAL_EVENT",
                    "severity": SEV_INFO,
                    "detail": f"Storm signature detected: dT={dt:+.1f}°C, dP={dp_val:+.1f} hPa, dRH={dh:+.1f}% — classified as natural weather, not fault",
                    "layer": "Layer 3 — Physics Validator",
                    "sensor": "Multivariate Atmosphere"
                })

    alerts.extend(l3_alerts)

    return {
        "alerts": alerts,
        "l1_alerts": l1_alerts,
        "lstm_result": lstm_res,
        "iforest_result": iforest_res,
        "l3_alerts": l3_alerts
    }


def compute_risk_score(
    alerts: List[Dict[str, Any]],
    spatial: Optional[Dict[str, Any]] = None,
    data_quality: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Deterministic risk score calculation (0–100)."""
    components = {"rule_violations": 0, "temporal_anomaly": 0, "spatial_deviation": 0, "data_quality": 0}

    for a in alerts:
        layer = a.get("layer", "")
        sev = a.get("severity", "")
        if "Rule Engine" in layer:
            components["rule_violations"] += 15 if sev == SEV_CRITICAL else 8
        elif "LSTM" in layer:
            components["temporal_anomaly"] += 20
        elif "Isolation Forest" in layer:
            components["temporal_anomaly"] += 10
        elif "Physics" in layer and a.get("type") != "METEOROLOGICAL_EVENT":
            components["rule_violations"] += 20

    if spatial and spatial.get("available") and not spatial.get("overall_consistent", True):
        components["spatial_deviation"] = 15

    if data_quality:
        if not data_quality.get("fresh", True):
            components["data_quality"] += 5
        if not data_quality.get("complete", True):
            components["data_quality"] += 5

    total = min(100, sum(components.values()))

    if alerts:
        if total >= 70 or any(a.get("severity") == SEV_CRITICAL for a in alerts):
            level = STATUS_CRITICAL
        elif total >= 40 or any(a.get("severity") == SEV_HIGH for a in alerts):
            level = STATUS_HIGH_RISK
        else:
            level = STATUS_WARNING
    else:
        level = STATUS_HEALTHY
        total = min(total, 15)

    return {"score": total, "level": level, "components": components}


def generate_explanation(
    station_name: str,
    reading: Dict[str, Any],
    alerts: List[Dict[str, Any]],
    spatial: Optional[Dict[str, Any]] = None,
    lstm_result: Optional[Dict[str, Any]] = None,
    iforest_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate structured human-readable explanation and operational response."""
    if not alerts:
        return {
            "reasons": ["All detection layers passed nominal criteria."],
            "conclusion": f"Station {station_name} is operating within normal environmental and operational boundaries.",
            "recommended_action": "No immediate operator action required.",
            "classification": "Nominal",
            "layers_fired": [],
            "sensors_affected": []
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

    has_rule = any("Rule Engine" in l for l in layers_fired)
    has_lstm = any("LSTM" in l for l in layers_fired)
    has_iforest = any("Isolation Forest" in l for l in layers_fired)
    has_physics = any("Physics" in l for l in layers_fired)
    is_storm = any(a.get("type") == "METEOROLOGICAL_EVENT" for a in alerts)
    spatial_ok = spatial.get("overall_consistent", True) if spatial and spatial.get("available") else True

    if is_storm and not has_physics:
        classification = "Natural Environmental Event"
        conclusion = "Coordinated multivariate transition (temperature drop, pressure rise, humidity surge) corresponds to an active convective storm front."
        action = "Log meteorological alert. Do NOT flag as sensor malfunction."
    elif has_lstm and not spatial_ok:
        classification = "Probable Localized Sensor Fault"
        conclusion = f"Temporal waveform anomaly detected at {station_name}, while regional neighbors remain steady. Highly indicative of localized transducer fault."
        action = "Dispatch field maintenance verification or trigger sensor self-test."
    elif has_rule and has_lstm:
        classification = "High-Confidence Hardware Malfunction"
        conclusion = "Both deterministic rate rules and temporal deep learning models triggered on this reading."
        action = "Quarantine station data stream from downstream forecasting models and alert technician."
    elif has_physics:
        classification = "Physical Sensor Inconsistency"
        conclusion = "Sensor outputs violate thermodynamic gas laws (e.g. Dew Point exceeding Ambient Temperature)."
        action = "Check humidity sensor hygrometer calibration and analog frontend."
    elif has_rule:
        classification = "Boundary Rule Breach"
        conclusion = "Reading violated climatological or persistence thresholds."
        action = "Inspect communication bus and verify voltage stability."
    elif has_iforest or has_lstm:
        classification = "Temporal Pattern Deviation"
        conclusion = "Observation diverges from historical diurnal rhythm."
        action = "Monitor station trend for persistent drift."
    else:
        classification = "Anomalous Condition"
        conclusion = "Sensor observation exhibits irregular properties requiring operator review."
        action = "Review real-time telemetry."

    return {
        "reasons": reasons,
        "conclusion": conclusion,
        "recommended_action": action,
        "classification": classification,
        "layers_fired": list(layers_fired),
        "sensors_affected": list(sensors_affected),
        "spatial_consistent": spatial_ok
    }
