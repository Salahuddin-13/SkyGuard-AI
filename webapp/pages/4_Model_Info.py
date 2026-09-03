"""
SkyGuard AI — Model Intelligence
Real model metrics, architecture, and honest limitations.
"""
import sys, os
import streamlit as st
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import (
    apply_styling, load_lstm_model, load_training_report,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_INFO,
)

st.set_page_config(page_title="Model Intelligence — SkyGuard AI", page_icon="🧠", layout="wide")
apply_styling()

model_info = load_lstm_model()
report = load_training_report()

st.markdown("""
<div style="margin-bottom:12px;">
    <span style="font-size:1.4rem;font-weight:700;color:#111827;">Model Intelligence</span><br>
    <span style="font-size:0.8rem;color:#6B7280;">Architecture, real metrics, and transparent limitations</span>
</div>
""", unsafe_allow_html=True)

tab_arch, tab_logic, tab_metrics, tab_limits = st.tabs(["Architecture", "Detection Logic", "Model Metrics", "Limitations"])

# === ARCHITECTURE ===
with tab_arch:
    st.markdown("##### System Architecture")
    st.code("""
    DATA SOURCES                    DETECTION ENGINE                 OUTPUT
    ────────────                    ────────────────                 ──────
    ┌──────────────┐
    │  Open-Meteo   │──┐
    │  (Weather API)│  │           ┌──────────────────┐
    └──────────────┘  │           │  Layer 1          │
                      ├──► API ──►│  Rule Engine      │──┐
    ┌──────────────┐  │           │  (WMO bounds,     │  │
    │  ESP32 +     │──┘           │   rate, frozen)   │  │
    │  BMP280/DHT22│              └──────────────────┘  │     ┌──────────┐
    │  (Hardware)  │──► MQTT                             ├────►│ Decision │
    └──────────────┘              ┌──────────────────┐  │     │ Engine   │──► Alert
                                  │  Layer 2          │  │     │          │    + Risk
    ┌──────────────┐              │  LSTM Autoencoder │──┤     │ + Spatial│    + Explanation
    │  Simulation  │──► Inject    │  (57,196 params)  │  │     │ Validator│
    │  (Fault Lab) │              └──────────────────┘  │     └──────────┘
    └──────────────┘              ┌──────────────────┐  │          │
                                  │  Layer 3          │  │          ▼
                                  │  Physics Validator│──┘     Dashboard
                                  │  (Magnus, multi-  │        Map, Alerts
                                  │   variate)        │        Analytics
                                  └──────────────────┘
    """, language=None)

    st.markdown("##### Data Pipeline")
    st.markdown("""
    | Stage | Component | Status |
    |---|---|---|
    | Ingestion | Open-Meteo REST API (5-min cache) | ✓ Active |
    | Ingestion | ESP32 + MQTT | ○ Prototype — not connected |
    | Normalization | StandardScaler (fitted on Jena Climate) | ✓ Loaded |
    | Detection | Layer 1 — Rule Engine | ✓ Active |
    | Detection | Layer 2 — LSTM Autoencoder | """ + ("✓ Model loaded" if model_info and model_info.get("status") == "loaded" else "! Using Z-score fallback") + """ |
    | Detection | Layer 3 — Physics Validator | ✓ Active |
    | Spatial | Neighboring station comparison | ✓ Active (12 stations) |
    | Risk | Deterministic risk scoring | ✓ Active |
    | Explanation | Alert reasoning generator | ✓ Active |
    """)

# === DETECTION LOGIC ===
with tab_logic:
    st.markdown("##### 3-Layer Detection Engine")

    l1, l2, l3 = st.columns(3)

    with l1:
        st.markdown(f"""
<div style="background:#FFFFFF;border-top:3px solid {COLOR_HEALTHY};border:1px solid #E5E7EB;border-radius:6px;padding:16px;">
    <div style="font-weight:600;color:#111827;">Layer 1 — Rule Engine</div>
    <div style="color:#6B7280;font-size:0.8rem;margin-top:8px;">
        Deterministic checks based on WMO standards. No ML.<br><br>
        <b>Checks:</b><br>
        • Range: -50°C < T < 60°C, 870 < P < 1084 hPa<br>
        • Rate of change: |ΔT| < 5°C per step<br>
        • Frozen: σ(last 6 readings) > 0.01<br>
        • Dropout: non-null values required<br><br>
        <b>Catches:</b> Spikes, out-of-range, frozen, dropout<br>
        <b>Misses:</b> Gradual drift, complex patterns
    </div>
</div>""", unsafe_allow_html=True)

    with l2:
        st.markdown(f"""
<div style="background:#FFFFFF;border-top:3px solid {COLOR_INFO};border:1px solid #E5E7EB;border-radius:6px;padding:16px;">
    <div style="font-weight:600;color:#111827;">Layer 2 — LSTM Autoencoder</div>
    <div style="color:#6B7280;font-size:0.8rem;margin-top:8px;">
        Learns normal temporal patterns and flags deviations.<br><br>
        <b>Architecture:</b><br>
        • Encoder: LSTM(3→64) → LSTM(64→32) → FC(32→16)<br>
        • Decoder: FC(16→32) → LSTM(32→64) → LSTM(64→3)<br>
        • Bottleneck: 16-dim latent vector<br><br>
        <b>How it works:</b><br>
        1. Trained on normal weather only<br>
        2. Reconstructs input sequence<br>
        3. High reconstruction error = anomaly<br><br>
        <b>Catches:</b> Drift, complex temporal anomalies<br>
        <b>Misses:</b> Frozen values (reconstructs them well)
    </div>
</div>""", unsafe_allow_html=True)

    with l3:
        st.markdown(f"""
<div style="background:#FFFFFF;border-top:3px solid {COLOR_WARNING};border:1px solid #E5E7EB;border-radius:6px;padding:16px;">
    <div style="font-weight:600;color:#111827;">Layer 3 — Physics Validator</div>
    <div style="color:#6B7280;font-size:0.8rem;margin-top:8px;">
        Atmospheric physics to validate consistency.<br><br>
        <b>Checks:</b><br>
        • Magnus dew-point: T_dp ≤ T_ambient<br>
        • Multivariate: T↓ + P↑ + RH↑ = storm, not fault<br>
        • Cross-variable consistency<br><br>
        <b>Key value:</b><br>
        Prevents false positives during real weather events.
        If T drops, P rises, and RH rises simultaneously,
        the system recognizes a convective storm pattern
        rather than flagging a sensor fault.<br><br>
        <b>Catches:</b> False positives, impossible states<br>
        <b>Misses:</b> Subtle correlated sensor drift
    </div>
</div>""", unsafe_allow_html=True)

    st.markdown("##### Why No Single Layer Is Enough")
    st.markdown("""
    | Anomaly | Layer 1 (Rules) | Layer 2 (LSTM) | Layer 3 (Physics) |
    |---|---|---|---|
    | Spike | ✓ Range/rate | ✓ High recon error | ✓ Confirms inconsistency |
    | Frozen | ✓ Persistence | ✗ Misses it | ✓ Dew-point check |
    | Drift | ✗ Too gradual | ✓ Temporal deviation | ✓ Physics bounds |
    | Storm (false pos.) | ✗ Flags it | ✗ Flags it | ✓ Recognizes as real |
    | Dropout | ✓ Missing data | N/A | N/A |
    """)

# === MODEL METRICS (real only) ===
with tab_metrics:
    st.markdown("##### LSTM Autoencoder — Training Metrics")
    st.info("All metrics below are from the actual training run. No fabricated values.")

    if report:
        lstm = report.get("lstm_ae", {})
        data_info = report.get("data", {})

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Parameters", f"{lstm.get('total_params', 'N/A'):,}")
        m2.metric("Epochs", lstm.get("epochs", "N/A"))
        m3.metric("Best Val Loss", f"{lstm.get('best_val_loss', 0):.5f}")
        m4.metric("Threshold", f"{lstm.get('threshold', 0):.5f}")

        st.markdown("##### Training Configuration")
        st.markdown(f"""
        | Parameter | Value |
        |---|---|
        | Dataset | {data_info.get('dataset', 'N/A')} |
        | Total readings | {data_info.get('total_readings', 'N/A'):,} |
        | Training samples | {data_info.get('train_samples', 'N/A'):,} |
        | Sequence length | {data_info.get('seq_len', 'N/A')} |
        | Features | {', '.join(data_info.get('features', []))} |
        | Input shape | (batch, {data_info.get('seq_len', 60)}, {len(data_info.get('features', []))}) |
        """)

        # Training curve from real data
        history = report.get("training_history", [])
        if history:
            st.markdown("##### Training Loss Curve")
            import pandas as pd
            df = pd.DataFrame(history)
            st.line_chart(df.set_index("epoch")[["train_loss", "val_loss"]], height=300)

        # Isolation Forest
        iso = report.get("isolation_forest", {})
        if iso:
            st.markdown("##### Isolation Forest")
            st.markdown(f"""
            | Parameter | Value |
            |---|---|
            | Estimators | {iso.get('n_estimators', 'N/A')} |
            | Contamination | {iso.get('contamination', 'N/A')} |
            """)

        st.markdown("##### Metrics NOT Available")
        st.warning("""
        The following metrics have not been computed on a held-out test set and are therefore not displayed:
        - Precision, Recall, F1-score
        - ROC-AUC
        - Confusion matrix on production data
        - Real-time inference latency benchmark

        These would require a labeled test dataset with known anomalies, which is not yet available.
        """)
    else:
        st.warning("Training report not found at ml/models/training_report.json")

    # Model file status
    st.markdown("##### Model Status")
    if model_info:
        if model_info.get("status") == "loaded":
            st.success(f"LSTM model loaded successfully. Threshold: {model_info.get('threshold', 'N/A')}")
        else:
            st.error(f"Model error: {model_info.get('error', 'Unknown')}")
    else:
        st.warning("Model not loaded — running in Z-score fallback mode")

# === LIMITATIONS ===
with tab_limits:
    st.markdown("##### Known Limitations")

    st.markdown("""
<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:6px;padding:16px;">

**Data dependency**
- Currently relies on Open-Meteo API for environmental data. If the provider is unavailable, the system falls back to synthetic data (clearly labeled).
- Open-Meteo data is NOT direct IMD AWS telemetry. In production, SkyGuard would connect to IMD data feeds.

**Model limitations**
- LSTM trained on Jena Climate dataset (Germany, 2009-2016). Indian weather patterns may differ.
- The model has not been validated on labeled Indian anomaly datasets.
- Frozen sensor values are poorly detected by the LSTM — this is why Layer 1 (Rule Engine) is essential.
- Distribution shift over time may degrade model performance without retraining.

**System scope**
- 12 demonstration stations (real Indian coordinates, Open-Meteo data).
- ESP32 hardware integration is designed but not connected in this prototype.
- MQTT broker and FastAPI backend are architectural targets, not implemented.
- Alert lifecycle (acknowledge/resolve) uses session state — not persisted across sessions.

**Operational caveat**

> SkyGuard is a decision-support system. Alerts require human verification and should not replace official meteorological warnings from the India Meteorological Department (IMD).

</div>
""", unsafe_allow_html=True)

st.caption("SkyGuard AI · SIH26073 · Ministry of Earth Sciences")
