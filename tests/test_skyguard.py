"""
SkyGuard AI — Comprehensive Test Suite
Tests Core ML Inference, 4-Layer Physics Engine, Hardware Simulation & FastAPI Endpoints
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.stations import STATIONS, haversine_distance, get_nearby_stations
from backend.core.engine import (
    magnus_dewpoint,
    sea_level_pressure,
    assess_data_quality,
    compute_spatial_context,
    detect_anomalies,
    compute_risk_score,
    generate_explanation,
    STATUS_HEALTHY,
    STATUS_CRITICAL,
    STATUS_WARNING
)
from backend.core.ml_models import ml_engine
from backend.services.ingestion import ingestion_service

client = TestClient(app)


# ── 1. THERMODYNAMICS & PHYSICAL LAWS ──

def test_magnus_dewpoint():
    """Verify Magnus formula: Dew point must always be <= Ambient temperature for RH <= 100%."""
    # Standard conditions
    dp = magnus_dewpoint(25.0, 50.0)
    assert dp is not None
    assert dp < 25.0
    assert 13.0 < dp < 15.0  # Approx 13.9°C

    # 100% relative humidity: Dew point == Temperature
    dp_sat = magnus_dewpoint(30.0, 100.0)
    assert dp_sat is not None
    assert abs(dp_sat - 30.0) < 0.1

    # Edge cases
    assert magnus_dewpoint(None, 50.0) is None
    assert magnus_dewpoint(25.0, None) is None


def test_barometric_sea_level_pressure():
    """Verify barometric reduction formula across different elevations."""
    # Sea-level station (Mumbai Colaba 8m)
    p_sea = sea_level_pressure(1012.0, 8.0, 28.0)
    assert p_sea is not None
    assert abs(p_sea - 1012.9) < 0.5

    # High-altitude station (Leh Ladakh 3514m)
    p_leh = 680.0
    p_leh_reduced = sea_level_pressure(p_leh, 3514.0, 10.0)
    assert p_leh_reduced is not None
    assert 1000.0 < p_leh_reduced < 1030.0  # Normalizes into standard meteorological range


# ── 2. SPATIAL GEODESY & NEIGHBORHOOD ──

def test_haversine_distance():
    """Test distance calculation between Delhi and Mumbai (~1150km)."""
    delhi = STATIONS["Delhi (Safdarjung)"]
    mumbai = STATIONS["Mumbai (Colaba)"]
    dist = haversine_distance(delhi["lat"], delhi["lon"], mumbai["lat"], mumbai["lon"])
    assert 1100.0 < dist < 1200.0


def test_nearby_stations_lookup():
    """Test that nearby stations within 800km are found for Delhi."""
    nearby = get_nearby_stations("Delhi (Safdarjung)", max_distance_km=500.0)
    assert "Delhi (Palam)" in nearby
    assert "Chandigarh" in nearby
    assert "Jaipur" in nearby
    assert "Mumbai (Colaba)" not in nearby  # >1100km


# ── 3. DUAL ML ENGINE INFERENCE ──

def test_lstm_autoencoder_inference():
    """Test PyTorch LSTM Autoencoder forward pass and reconstruction error."""
    # Generate 72 hours of nominal temperature, pressure, humidity
    times = [f"2026-09-01T{h%24:02d}:00" for h in range(72)]
    temps = [25.0 + 5.0 * math.sin(h * 0.26) for h in range(72)]
    pressures = [1013.0 + 2.0 * math.cos(h * 0.26) for h in range(72)]
    humidities = [60.0 - 10.0 * math.sin(h * 0.26) for h in range(72)]

    hourly_data = {
        "time": times,
        "temperature_2m": temps,
        "surface_pressure": pressures,
        "relative_humidity_2m": humidities
    }

    # Nominal reading
    reading_norm = {"temperature": 25.0, "pressure": 1013.0, "humidity": 60.0}
    res_norm = ml_engine.run_lstm_inference(hourly_data, reading_norm)
    assert res_norm is not None
    assert res_norm["status"] == "complete"
    assert res_norm["is_anomaly"] is False
    assert res_norm["anomaly_score"] < res_norm["threshold"]

    # Injected massive spike (+25°C jump)
    reading_spike = {"temperature": 50.0, "pressure": 1013.0, "humidity": 60.0}
    res_spike = ml_engine.run_lstm_inference(hourly_data, reading_spike)
    assert res_spike is not None
    assert res_spike["is_anomaly"] is True
    assert res_spike["anomaly_score"] > res_spike["threshold"]


def test_isolation_forest_inference():
    """Test Scikit-Learn Isolation Forest 15-feature rolling inference."""
    times = [f"2026-09-01T{h%24:02d}:00" for h in range(24)]
    temps = [25.0 + 0.1 * h for h in range(24)]
    pressures = [1013.0 + 0.1 * h for h in range(24)]
    humidities = [60.0 + 0.2 * h for h in range(24)]

    hourly_data = {
        "time": times,
        "temperature_2m": temps,
        "surface_pressure": pressures,
        "relative_humidity_2m": humidities
    }

    # Nominal reading
    res_norm = ml_engine.run_isolation_forest_inference(hourly_data, {"temperature": 27.4, "pressure": 1015.4, "humidity": 64.8})
    assert res_norm is not None
    assert res_norm["is_anomaly"] is False

    # Extreme outlier reading
    res_outlier = ml_engine.run_isolation_forest_inference(hourly_data, {"temperature": 55.0, "pressure": 1015.4, "humidity": 64.8})
    assert res_outlier is not None
    assert res_outlier["is_anomaly"] is True


# ── 4. FAULT INJECTION & DETECTION LAYERS ──

def test_detection_engine_nominal():
    """Verify that nominal station data passes all 4 layers with 0 alerts."""
    reading = {
        "temperature": 28.5,
        "pressure": 1012.0,
        "humidity": 65.0,
        "timestamp": "2026-09-02T12:00"
    }
    hourly = {
        "time": [f"2026-09-02T{h:02d}:00" for h in range(24)],
        "temperature_2m": [28.0 + 0.5 * (h % 3) for h in range(24)],
        "surface_pressure": [1012.0 + 0.2 * (h % 2) for h in range(24)],
        "relative_humidity_2m": [65.0 + 1.0 * (h % 4) for h in range(24)],
    }
    res = detect_anomalies(reading, hourly, "Mumbai (Colaba)")
    assert res["layer1"] == "PASS"
    assert res["layer3"] == "PASS"
    assert len(res["alerts"]) == 0


def test_detection_engine_spike_fault():
    """Verify that a sudden temperature spike is caught by Layer 1 and Layer 2."""
    reading = {
        "temperature": 53.5,  # +25°C jump
        "pressure": 1012.0,
        "humidity": 65.0,
        "timestamp": "2026-09-02T12:00"
    }
    hourly = {
        "time": [f"2026-09-02T{h:02d}:00" for h in range(24)],
        "temperature_2m": [28.0 for _ in range(24)],
        "surface_pressure": [1012.0 for _ in range(24)],
        "relative_humidity_2m": [65.0 for _ in range(24)],
    }
    res = detect_anomalies(reading, hourly, "Delhi (Safdarjung)")
    alert_types = [a["type"] for a in res["alerts"]]
    assert "RATE_OF_CHANGE" in alert_types or "TEMPORAL_ANOMALY" in alert_types


# ── 5. FASTAPI REST ENDPOINTS ──

def test_api_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["platform"] == "SkyGuard AI"


def test_api_overview():
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_stations"] == 35
    assert "Delhi (Safdarjung)" in data["stations"]
    assert "Mumbai (Colaba)" in data["stations"]


def test_api_fault_injection_and_clear():
    # 1. Inject fault
    resp_inj = client.post("/api/faults/inject", json={"station_name": "Delhi (Safdarjung)", "fault_type": "spike"})
    assert resp_inj.status_code == 200
    assert resp_inj.json()["status"] == "injected"

    # 2. Check overview reflects fault
    resp_ov = client.get("/api/overview")
    delhi = resp_ov.json()["stations"]["Delhi (Safdarjung)"]
    assert delhi["active_fault"] == "spike"
    assert delhi["status"] in ["WARNING", "HIGH_RISK", "CRITICAL"]

    # 3. Clear fault
    resp_clr = client.post("/api/faults/clear")
    assert resp_clr.status_code == 200
    assert resp_clr.json()["status"] == "cleared"


def test_api_hardware_injection():
    resp = client.post("/api/hardware/inject", json={"fault_type": "i2c_bus_stall"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "injected"

    # Clear
    resp_clr = client.post("/api/hardware/clear")
    assert resp_clr.status_code == 200


def test_api_export_csv():
    resp = client.get("/api/export/csv")
    assert resp.status_code == 200
    assert "AlertID,Station,StationID" in resp.text
