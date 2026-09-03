"""
=============================================================
  LESSON 6: The Full Pipeline — From Sensor to Alert
=============================================================

This lesson simulates the ENTIRE SkyGuard AI flow:
  Fake sensor → Anomaly injection → Detection → Explanation

No hardware needed. No MQTT. Just pure Python.
This is a self-contained demo of everything working together.

RUN THIS:  python lesson_06_full_pipeline.py
=============================================================
"""

import torch
import torch.nn as nn
import numpy as np
import os
import time
import math

# ============================================================
# Reuse our LSTM Autoencoder from Lesson 5
# ============================================================

class LSTMAutoencoder(nn.Module):
    def __init__(self, n_features=3, hidden_dim=64, bottleneck_dim=16, seq_len=60):
        super().__init__()
        self.seq_len = seq_len
        self.encoder_lstm1 = nn.LSTM(n_features, hidden_dim, 1, batch_first=True)
        self.encoder_lstm2 = nn.LSTM(hidden_dim, hidden_dim//2, 1, batch_first=True)
        self.encoder_fc = nn.Linear(hidden_dim//2, bottleneck_dim)
        self.decoder_fc = nn.Linear(bottleneck_dim, hidden_dim//2)
        self.decoder_lstm1 = nn.LSTM(hidden_dim//2, hidden_dim, 1, batch_first=True)
        self.decoder_lstm2 = nn.LSTM(hidden_dim, n_features, 1, batch_first=True)

    def forward(self, x):
        enc, _ = self.encoder_lstm1(x)
        enc, (h, _) = self.encoder_lstm2(enc)
        b = self.encoder_fc(h.squeeze(0))
        d = self.decoder_fc(b).unsqueeze(1).repeat(1, self.seq_len, 1)
        d, _ = self.decoder_lstm1(d)
        d, _ = self.decoder_lstm2(d)
        return d


# ============================================================
# LAYER 1: Rule-Based WMO Physics Checks
# ============================================================

class RuleEngine:
    """
    First line of defense. Catches obvious problems instantly.
    Based on WMO guidelines for weather station QC.
    """
    
    # Physical bounds (anything outside is IMPOSSIBLE):
    TEMP_MIN, TEMP_MAX = -50.0, 60.0      # °C
    PRES_MIN, PRES_MAX = 870.0, 1084.0    # hPa
    HUM_MIN,  HUM_MAX  = 0.0, 100.0       # %
    
    # Maximum change per reading (5-second interval):
    MAX_TEMP_RATE = 3.0   # °C per reading
    MAX_PRES_RATE = 2.0   # hPa per reading
    MAX_HUM_RATE  = 8.0   # % per reading
    
    def __init__(self):
        self.prev_reading = None
        self.frozen_counter = {'temperature': 0, 'pressure': 0, 'humidity': 0}
        self.frozen_values = {'temperature': None, 'pressure': None, 'humidity': None}
    
    def check(self, temp, pressure, humidity):
        """Returns list of (anomaly_type, severity, message) tuples."""
        alerts = []
        
        # --- Range check ---
        if not (self.TEMP_MIN <= temp <= self.TEMP_MAX):
            alerts.append(('OUT_OF_RANGE', 'CRITICAL', 
                f'Temperature {temp:.1f}°C outside physical bounds [{self.TEMP_MIN}, {self.TEMP_MAX}]'))
        if not (self.PRES_MIN <= pressure <= self.PRES_MAX):
            alerts.append(('OUT_OF_RANGE', 'CRITICAL',
                f'Pressure {pressure:.1f} hPa outside bounds [{self.PRES_MIN}, {self.PRES_MAX}]'))
        if not (self.HUM_MIN <= humidity <= self.HUM_MAX):
            alerts.append(('OUT_OF_RANGE', 'CRITICAL',
                f'Humidity {humidity:.1f}% outside bounds [{self.HUM_MIN}, {self.HUM_MAX}]'))
        
        # --- Rate of change check (spike detection) ---
        if self.prev_reading is not None:
            dt = abs(temp - self.prev_reading[0])
            dp = abs(pressure - self.prev_reading[1])
            dh = abs(humidity - self.prev_reading[2])
            
            if dt > self.MAX_TEMP_RATE:
                alerts.append(('SPIKE', 'HIGH',
                    f'Temperature changed {dt:.1f}°C in one reading (limit: {self.MAX_TEMP_RATE})'))
            if dp > self.MAX_PRES_RATE:
                alerts.append(('SPIKE', 'HIGH',
                    f'Pressure changed {dp:.1f} hPa in one reading (limit: {self.MAX_PRES_RATE})'))
            if dh > self.MAX_HUM_RATE:
                alerts.append(('SPIKE', 'MEDIUM',
                    f'Humidity changed {dh:.1f}% in one reading (limit: {self.MAX_HUM_RATE})'))
        
        # --- Frozen value check ---
        for name, val, idx in [('temperature', temp, 0), ('pressure', pressure, 1), ('humidity', humidity, 2)]:
            if self.frozen_values[name] is not None and abs(val - self.frozen_values[name]) < 0.01:
                self.frozen_counter[name] += 1
                if self.frozen_counter[name] >= 6:  # 30+ seconds frozen
                    alerts.append(('FROZEN', 'HIGH',
                        f'{name.title()} stuck at {val:.1f} for {self.frozen_counter[name]*5}s'))
            else:
                self.frozen_counter[name] = 0
                self.frozen_values[name] = val
        
        self.prev_reading = (temp, pressure, humidity)
        return alerts


# ============================================================
# LAYER 3: Physics-Informed Validation
# ============================================================

class PhysicsValidator:
    """
    Uses atmospheric physics to validate readings.
    Catches things the ML model might miss.
    """
    
    @staticmethod
    def check_dewpoint(temp, humidity):
        """
        Magnus-Tetens formula:
        If computed dew point > ambient temperature, 
        it's physically impossible → sensor fault.
        """
        if humidity <= 0:
            return ('PHYSICS_VIOLATION', 'CRITICAL', 
                    'Humidity is 0% or negative — sensor disconnected?')
        
        gamma = (17.27 * temp) / (237.7 + temp) + math.log(humidity / 100.0)
        dew_point = (237.7 * gamma) / (17.27 - gamma)
        
        if dew_point > temp + 0.5:
            return ('PHYSICS_VIOLATION', 'CRITICAL',
                f'Dew point ({dew_point:.1f}°C) > ambient temp ({temp:.1f}°C) — '
                f'physically impossible! DHT22 humidity sensor fault.')
        return None
    
    @staticmethod
    def check_multivariate_consistency(temp_delta, pressure_delta, humidity_delta):
        """
        Thunderstorm check: T↓ + P↑ + RH↑ simultaneously = real weather.
        Only one changing dramatically while others stable = sensor fault.
        """
        large_changes = sum([
            abs(temp_delta) > 3,
            abs(pressure_delta) > 2,
            abs(humidity_delta) > 10
        ])
        
        if large_changes == 1:
            return ('ISOLATED_CHANGE', 'MEDIUM',
                'Only ONE sensor showing dramatic change — likely sensor fault, not weather.')
        elif large_changes >= 2:
            return None  # Multiple sensors changing = probably real weather
        return None


# ============================================================
# EXPLAINER: Natural Language Diagnostics
# ============================================================

class Explainer:
    """Generates human-readable diagnostic cards."""
    
    @staticmethod
    def explain(reading, recon_error, per_feature_error, rule_alerts, physics_alerts, 
                threshold, confidence):
        """Generate a diagnostic card."""
        
        # Determine primary offender:
        features = ['Temperature', 'Pressure', 'Humidity']
        total_err = sum(per_feature_error)
        contributions = [e/total_err*100 if total_err > 0 else 0 for e in per_feature_error]
        primary = features[np.argmax(contributions)]
        
        # Classify anomaly type:
        anomaly_types = set()
        for alert in rule_alerts:
            anomaly_types.add(alert[0])
        for alert in (physics_alerts or []):
            anomaly_types.add(alert[0])
        
        if not anomaly_types and recon_error > threshold:
            anomaly_types.add('PATTERN_DEVIATION')
        
        # Build the card:
        lines = []
        lines.append("┌" + "─" * 68 + "┐")
        
        if recon_error > threshold or rule_alerts:
            status = f"🔴 ANOMALY DETECTED (Confidence: {confidence:.1f}%)"
        else:
            status = "✅ NORMAL"
        
        lines.append(f"│ {status:<67s}│")
        lines.append("├" + "─" * 68 + "┤")
        lines.append(f"│ Readings: T={reading[0]:.1f}°C  P={reading[1]:.1f}hPa  RH={reading[2]:.1f}%{' '*16}│")
        lines.append(f"│ Reconstruction Error: {recon_error:.6f} (threshold: {threshold:.6f}){' '*5}│")
        
        if anomaly_types:
            types_str = ', '.join(anomaly_types)
            lines.append(f"│ Classification: {types_str:<51s}│")
            lines.append(f"│ Primary Offender: {primary} ({contributions[np.argmax(contributions)]:.0f}% contribution){' '*13}│")
        
        for alert in rule_alerts:
            msg = alert[2][:62]
            lines.append(f"│  ⚠ {msg:<64s}│")
        
        for alert in (physics_alerts or []):
            if alert:
                msg = alert[2][:62]
                lines.append(f"│  🔬 {msg:<63s}│")
        
        lines.append("└" + "─" * 68 + "┘")
        return "\n".join(lines)


# ============================================================
# SIMULATOR: Fake Weather Station
# ============================================================

class WeatherSimulator:
    """Generates realistic weather data with optional fault injection."""
    
    def __init__(self):
        self.time_step = 0
        self.fault_mode = 'normal'
        self.drift_accumulator = 0
        self.frozen_value = None
    
    def inject_fault(self, mode):
        """mode: 'normal', 'spike', 'freeze', 'drift', 'dropout'"""
        self.fault_mode = mode
        if mode == 'freeze':
            self.frozen_value = None  # Will capture next reading
        if mode == 'drift':
            self.drift_accumulator = 0
        print(f"\n{'='*50}")
        print(f"  🎮 FAULT INJECTED: {mode.upper()}")
        print(f"{'='*50}\n")
    
    def generate(self):
        """Generate one reading."""
        self.time_step += 1
        
        # Base pattern: sinusoidal daily cycle
        hour = (self.time_step * 5 / 3600) % 24  # 5 seconds per reading
        
        temp = 25 + 8 * math.sin((hour - 6) * math.pi / 12) + np.random.randn() * 0.3
        pressure = 1013 + 3 * math.sin(hour * math.pi / 24) + np.random.randn() * 0.2
        humidity = 60 - 15 * math.sin((hour - 6) * math.pi / 12) + np.random.randn() * 1.0
        
        # Apply faults:
        if self.fault_mode == 'spike':
            temp += 25  # +25°C spike!
            self.fault_mode = 'normal'  # One-time spike
        
        elif self.fault_mode == 'freeze':
            if self.frozen_value is None:
                self.frozen_value = (temp, pressure, humidity)
            temp, pressure, humidity = self.frozen_value
        
        elif self.fault_mode == 'drift':
            self.drift_accumulator += 0.3
            humidity += self.drift_accumulator
        
        elif self.fault_mode == 'dropout':
            return None  # No data!
        
        return (round(temp, 1), round(pressure, 1), round(humidity, 1))


# ============================================================
# MAIN: Run the full pipeline!
# ============================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          SKYGUARD AI — FULL PIPELINE SIMULATION             ║
║                                                             ║
║  Simulating a weather station with live anomaly detection.  ║
║  Watch as faults are injected and caught in real-time.      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize components:
    simulator = WeatherSimulator()
    rule_engine = RuleEngine()
    physics = PhysicsValidator()
    explainer = Explainer()
    
    # We won't load the trained LSTM here (to keep this lesson self-contained),
    # instead we'll use a simple rolling-stats anomaly detector as a stand-in.
    # The REAL SkyGuard uses the LSTM from Lesson 5.
    
    readings_buffer = []
    threshold = 2.0  # Simplified threshold
    
    print("Starting weather simulation...\n")
    print(f"{'Step':>4s} | {'Temp':>6s} | {'Press':>7s} | {'Humid':>6s} | {'Error':>8s} | Status")
    print("-" * 72)
    
    # Schedule of events:
    events = {
        15: ('spike', "💥 Injecting SPIKE on temperature sensor"),
        25: ('freeze', "🧊 Injecting FREEZE on all sensors"),
        40: ('normal', "✅ Resuming normal operation"),
        50: ('drift', "📈 Injecting gradual DRIFT on humidity"),
        70: ('normal', "✅ Resuming normal operation"),
        75: ('dropout', "📡 Injecting COMMUNICATION DROPOUT"),
        80: ('normal', "✅ Resuming normal operation"),
    }
    
    for step in range(1, 91):
        # Check for scheduled events:
        if step in events:
            mode, msg = events[step]
            print(f"\n  >>> {msg}")
            simulator.inject_fault(mode)
            if mode == 'normal':
                rule_engine = RuleEngine()  # Reset frozen counters
            print()
        
        # Generate reading:
        reading = simulator.generate()
        
        if reading is None:
            print(f"{step:4d} | {'---':>6s} | {'---':>7s} | {'---':>6s} | {'---':>8s} | 📡 DROPOUT — No data received!")
            continue
        
        temp, pressure, humidity = reading
        
        # Layer 1: Rule checks
        rule_alerts = rule_engine.check(temp, pressure, humidity)
        
        # Layer 3: Physics checks
        physics_alerts = []
        dp_check = physics.check_dewpoint(temp, humidity)
        if dp_check:
            physics_alerts.append(dp_check)
        
        # Simplified anomaly score (stand-in for LSTM):
        readings_buffer.append(reading)
        if len(readings_buffer) > 20:
            readings_buffer.pop(0)
        
        if len(readings_buffer) >= 5:
            recent = np.array(readings_buffer)
            mean = recent.mean(axis=0)
            std = recent.std(axis=0) + 0.01  # avoid division by zero
            z_scores = np.abs((np.array(reading) - mean) / std)
            error = z_scores.mean()
            per_feature = z_scores.tolist()
        else:
            error = 0
            per_feature = [0, 0, 0]
        
        # Determine status:
        is_anomaly = error > threshold or len(rule_alerts) > 0
        confidence = min(error / threshold * 100, 99.9) if threshold > 0 else 0
        
        status_icon = "🔴" if is_anomaly else "✅"
        status_text = f"ANOMALY ({confidence:.0f}%)" if is_anomaly else "Normal"
        
        print(f"{step:4d} | {temp:6.1f} | {pressure:7.1f} | {humidity:6.1f} | {error:8.4f} | {status_icon} {status_text}")
        
        # Print diagnostic card for anomalies:
        if is_anomaly and (len(rule_alerts) > 0 or error > threshold * 1.5):
            card = explainer.explain(
                reading, error, per_feature, rule_alerts, physics_alerts,
                threshold, confidence
            )
            print(card)
        
        time.sleep(0.1)  # Small delay for readability
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  SIMULATION COMPLETE                                        ║
║                                                             ║
║  You just watched the full SkyGuard AI pipeline:            ║
║    1. Sensor generates data (simulated ESP32)               ║
║    2. Rule engine catches obvious violations                ║
║    3. ML model scores reconstruction error                  ║
║    4. Physics validator confirms with atmospheric formulas   ║
║    5. Explainer generates human-readable diagnostic cards    ║
║                                                             ║
║  In the real system:                                        ║
║    • ESP32 hardware replaces the simulator                  ║
║    • MQTT replaces direct function calls                    ║
║    • React dashboard replaces terminal output               ║
║    • LSTM Autoencoder replaces z-score detection            ║
║                                                             ║
║  But the LOGIC is identical.                                ║
╚══════════════════════════════════════════════════════════════╝
    """)

if __name__ == '__main__':
    main()
