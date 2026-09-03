"""
SkyGuard AI — Telemetry Ingestion & Simulation Service
Fetches real-time observations from Open-Meteo IMD AWS network,
manages active fault injections, and supports ESP32 edge telemetry.
"""

import time
import math
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np

from backend.core.stations import STATIONS
from backend.core.engine import (
    detect_anomalies,
    compute_spatial_context,
    assess_data_quality,
    compute_risk_score,
    generate_explanation,
    magnus_dewpoint,
    STATUS_HEALTHY,
    STATUS_WARNING,
    STATUS_HIGH_RISK,
    STATUS_CRITICAL
)
from backend.core.ml_models import ml_engine


class IngestionService:
    def __init__(self):
        self.cached_stations: Dict[str, Dict[str, Any]] = {}
        self.last_fetch_time: float = 0.0
        self.cache_ttl_seconds: float = 300.0  # 5 minutes
        self.cached_processed_network: Dict[str, Any] = {}
        self.last_processed_time: float = 0.0
        self.active_faults: Dict[str, str] = {}  # {station_name: fault_type}
        self.hardware_state: Dict[str, Any] = {
            "device_id": "ESP32-WROOM-32D-AWS01",
            "station_id": "DEL01",
            "station_name": "Delhi (Safdarjung)",
            "firmware_version": "v2.4.1-sih",
            "uptime_seconds": 184520,
            "wifi_rssi_dbm": -58,
            "battery_mv": 3980,
            "i2c_bus_status": "OK",
            "bmp280_status": "OK",
            "dht22_status": "OK",
            "packet_drop_rate_pct": 0.0,
            "last_packet_timestamp": datetime.now().isoformat(),
            "hardware_fault": None
        }

    def fetch_station_data(self, station_name: str, station_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch real-time data from Open-Meteo IMD network for a station."""
        lat = station_info["lat"]
        lon = station_info["lon"]
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,weather_code",
            "hourly": "temperature_2m,relative_humidity_2m,surface_pressure",
            "past_days": 3,
            "forecast_days": 1,
            "timezone": "Asia/Kolkata",
        }

        try:
            resp = requests.get(url, params=params, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                cur = data.get("current", {})
                hourly = data.get("hourly", {})
                return {
                    "station": station_name,
                    "id": station_info["id"],
                    "state": station_info["state"],
                    "zone": station_info["zone"],
                    "lat": lat,
                    "lon": lon,
                    "elevation_m": station_info["elevation_m"],
                    "temperature": cur.get("temperature_2m"),
                    "pressure": cur.get("surface_pressure"),
                    "humidity": cur.get("relative_humidity_2m"),
                    "wind_speed": cur.get("wind_speed_10m"),
                    "weather_code": cur.get("weather_code"),
                    "timestamp": cur.get("time", datetime.now().isoformat()),
                    "hourly": hourly,
                    "source": "IMD / Open-Meteo AWS",
                    "status_code": "LIVE_FEED"
                }
        except Exception as e:
            print(f"Fetch failed for {station_name}: {e}")

        # Synthetic fallback if network is unreachable
        return self._generate_synthetic_station(station_name, station_info)

    def _generate_synthetic_station(self, station_name: str, station_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-fidelity synthetic data."""
        lat = station_info["lat"]
        lon = station_info["lon"]
        elev = station_info["elevation_m"]
        now = datetime.now()
        hour = now.hour + now.minute / 60.0

        base_t = 30.0 - (lat - 8.0) * 0.3 - (elev / 200.0)
        temp = base_t + 5.0 * math.sin(math.pi * (hour - 9) / 12) + np.random.uniform(-0.5, 0.5)
        pres = 1013.25 * math.exp(-elev / 8430.0) + np.random.uniform(-0.3, 0.3)
        hum = 60.0 - 15.0 * math.sin(math.pi * (hour - 9) / 12) + np.random.uniform(-1.0, 1.0)
        hum = max(10.0, min(95.0, hum))

        # Hourly buffer (past 72h + 24h)
        times = []
        temps = []
        pressures = []
        humidities = []
        start_t = now - timedelta(days=3)
        for h in range(96):
            t_pt = start_t + timedelta(hours=h)
            h_val = t_pt.hour
            times.append(t_pt.strftime("%Y-%m-%dT%H:00"))
            t_synth = base_t + 5.0 * math.sin(math.pi * (h_val - 9) / 12) + np.random.uniform(-0.4, 0.4)
            p_synth = 1013.25 * math.exp(-elev / 8430.0) + np.random.uniform(-0.2, 0.2)
            rh_synth = 60.0 - 15.0 * math.sin(math.pi * (h_val - 9) / 12) + np.random.uniform(-0.8, 0.8)
            temps.append(round(float(t_synth), 1))
            pressures.append(round(float(p_synth), 1))
            humidities.append(round(float(rh_synth), 1))

        return {
            "station": station_name,
            "id": station_info["id"],
            "state": station_info["state"],
            "zone": station_info["zone"],
            "lat": lat,
            "lon": lon,
            "elevation_m": elev,
            "temperature": round(float(temp), 1),
            "pressure": round(float(pres), 1),
            "humidity": round(float(hum), 1),
            "wind_speed": 3.5,
            "weather_code": 1,
            "timestamp": now.strftime("%Y-%m-%dT%H:%M"),
            "hourly": {"time": times, "temperature_2m": temps, "surface_pressure": pressures, "relative_humidity_2m": humidities},
            "source": "Synthetic Fallback",
            "status_code": "FALLBACK"
        }

    def fetch_all_stations(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Fetch all 32+ stations concurrently with caching."""
        now = time.time()
        if not force_refresh and self.cached_stations and (now - self.last_fetch_time) < self.cache_ttl_seconds:
            return self.cached_stations

        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_station = {
                executor.submit(self.fetch_station_data, name, info): name
                for name, info in STATIONS.items()
            }
            for future in future_to_station:
                name = future_to_station[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = self._generate_synthetic_station(name, STATIONS[name])

        self.cached_stations = results
        self.last_fetch_time = now
        return results

    def inject_fault(self, station_name: str, fault_type: str):
        """Inject a fault into a station."""
        self.active_faults[station_name] = fault_type
        self.last_processed_time = 0.0

    def clear_fault(self, station_name: Optional[str] = None):
        """Clear active fault for single station or all stations."""
        if station_name:
            self.active_faults.pop(station_name, None)
        else:
            self.active_faults.clear()
        self.last_processed_time = 0.0

    def inject_hardware_fault(self, fault_type: str):
        """Inject an edge hardware fault into ESP32 simulator."""
        self.hardware_state["hardware_fault"] = fault_type
        if fault_type == "i2c_bus_stall":
            self.hardware_state["i2c_bus_status"] = "BUS_LOCKED"
            self.hardware_state["bmp280_status"] = "COMM_TIMEOUT"
        elif fault_type == "dht22_crc_error":
            self.hardware_state["dht22_status"] = "CHECKSUM_FAILED"
        elif fault_type == "packet_loss":
            self.hardware_state["packet_drop_rate_pct"] = 85.0
            self.hardware_state["wifi_rssi_dbm"] = -89
        elif fault_type == "power_brownout":
            self.hardware_state["battery_mv"] = 2850
        self.last_processed_time = 0.0

    def clear_hardware_fault(self):
        """Restore edge hardware to healthy status."""
        self.hardware_state["hardware_fault"] = None
        self.hardware_state["i2c_bus_status"] = "OK"
        self.hardware_state["bmp280_status"] = "OK"
        self.hardware_state["dht22_status"] = "OK"
        self.hardware_state["packet_drop_rate_pct"] = 0.0
        self.hardware_state["wifi_rssi_dbm"] = -58
        self.hardware_state["battery_mv"] = 3980
        self.last_processed_time = 0.0

    def get_processed_network(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch all stations, apply active faults, run 4-layer engine, return complete state with caching."""
        now = time.time()
        if not force_refresh and self.cached_processed_network and (now - self.last_processed_time) < 4.0:
            return self.cached_processed_network

        raw_data = self.fetch_all_stations()
        processed_stations = {}
        all_alerts = []
        healthy_count = 0
        warning_count = 0
        critical_count = 0

        # Apply faults
        mutated_data = {}
        for name, data in raw_data.items():
            d = dict(data)
            fault = self.active_faults.get(name)
            if fault:
                d["source"] = "Simulation Mode"
                if fault == "spike":
                    d["temperature"] = round((d["temperature"] or 25.0) + 25.0, 1)
                elif fault == "freeze":
                    d["temperature"] = 0.0
                    d["pressure"] = 0.0
                    d["humidity"] = 0.0
                elif fault == "drift":
                    d["humidity"] = min(100.0, round((d["humidity"] or 50.0) + 35.0, 1))
                elif fault == "dropout":
                    d["temperature"] = None
                    d["pressure"] = None
                    d["humidity"] = None
            mutated_data[name] = d

        # Evaluate each station
        for name, station_data in mutated_data.items():
            reading = {
                "temperature": station_data.get("temperature"),
                "pressure": station_data.get("pressure"),
                "humidity": station_data.get("humidity"),
                "timestamp": station_data.get("timestamp", "")
            }
            hourly = station_data.get("hourly")
            detection_res = detect_anomalies(reading, hourly, name)
            alerts = detection_res["alerts"]
            dp = magnus_dewpoint(reading["temperature"], reading["humidity"])
            spatial = compute_spatial_context(name, mutated_data)
            quality = assess_data_quality(station_data)
            risk = compute_risk_score(alerts, spatial, quality)
            explanation = generate_explanation(
                name, reading, alerts, spatial,
                detection_res["lstm_result"], detection_res["iforest_result"]
            )

            status = risk["level"]
            if status == STATUS_HEALTHY:
                healthy_count += 1
            elif status in [STATUS_WARNING, STATUS_HIGH_RISK]:
                warning_count += 1
            elif status == STATUS_CRITICAL:
                critical_count += 1

            for a in alerts:
                if a.get("type") != "METEOROLOGICAL_EVENT":
                    all_alerts.append({
                        "station": name,
                        "station_id": station_data.get("id"),
                        "alert_id": f"{station_data.get('id')}_{a.get('type')}",
                        "timestamp": station_data.get("timestamp"),
                        **a
                    })

            processed_stations[name] = {
                **station_data,
                "dew_point": dp,
                "status": status,
                "risk": risk,
                "quality": quality,
                "spatial": spatial,
                "detection": {
                    "alerts": alerts,
                    "layer1": "FAIL" if detection_res["l1_alerts"] else "PASS",
                    "layer2_lstm": detection_res["lstm_result"],
                    "layer2_iforest": detection_res["iforest_result"],
                    "layer3": "FAIL" if [x for x in detection_res["l3_alerts"] if x.get("type") != "METEOROLOGICAL_EVENT"] else "PASS"
                },
                "explanation": explanation,
                "active_fault": self.active_faults.get(name)
            }

        result = {
            "timestamp": datetime.now().isoformat(),
            "total_stations": len(processed_stations),
            "healthy": healthy_count,
            "warning": warning_count,
            "critical": critical_count,
            "active_faults_count": len(self.active_faults),
            "stations": processed_stations,
            "alerts": all_alerts,
            "hardware": self.hardware_state
        }
        self.cached_processed_network = result
        self.last_processed_time = now
        return result


# Global Ingestion Service
ingestion_service = IngestionService()
