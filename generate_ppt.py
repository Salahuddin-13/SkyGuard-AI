"""
SkyGuard AI — SIH PPT Generator (v2 — Bigger text, proper alignment)
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Colors
NAVY    = RGBColor(0x0F, 0x17, 0x2A)
CARD    = RGBColor(0x1A, 0x25, 0x3C)
CARD2   = RGBColor(0x1E, 0x29, 0x3B)
TEAL    = RGBColor(0x00, 0xD4, 0xAA)
BLUE    = RGBColor(0x38, 0xBD, 0xF8)
RED     = RGBColor(0xEF, 0x44, 0x44)
ORANGE  = RGBColor(0xFB, 0x92, 0x3C)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
GRAY    = RGBColor(0x94, 0xA3, 0xB8)
GREEN   = RGBColor(0x22, 0xC5, 0x5E)
LGRAY   = RGBColor(0xCB, 0xD5, 0xE1)

def set_bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY

def add_shape_with_text(slide, left, top, w, h, fill, lines, border_color=None):
    """
    Add a rounded rect with text properly inside it.
    lines = [(text, font_size, color, bold), ...]
    """
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(2)
    else:
        shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.15)
    tf.margin_bottom = Inches(0.15)

    for i, (text, size, color, bold) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.font.name = 'Calibri'
        p.space_after = Pt(2)
    return shape

def title_bar(slide, text, subtitle=""):
    shape = add_shape_with_text(slide, 0.3, 0.3, 12.7, 0.9, TEAL, [
        (text, 32, NAVY, True),
    ])
    if subtitle:
        p = shape.text_frame.add_paragraph()
        p.text = subtitle
        p.font.size = Pt(16)
        p.font.color.rgb = RGBColor(0x0A, 0x0F, 0x1E)
        p.font.name = 'Calibri'

def big_stat(slide, left, top, w, h, label, value, sub, value_color=GREEN):
    add_shape_with_text(slide, left, top, w, h, CARD, [
        (label, 16, GRAY, True),
        (value, 44, value_color, True),
        (sub, 16, LGRAY, False),
    ])


# ================================================================
# SLIDE 1: Problem Statement + Team
# ================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(s)
title_bar(s, "SKYGUARD AI", "SIH 2026  |  SIH26073  |  Ministry of Earth Sciences")

add_shape_with_text(s, 0.3, 1.5, 12.7, 2.2, CARD, [
    ("PROBLEM STATEMENT", 18, TEAL, True),
    ("", 8, WHITE, False),
    ("Intelligent Real-Time Anomaly Detection System for Temperature,", 24, WHITE, True),
    ("Pressure, and Humidity Sensors in Automatic Weather Stations", 24, WHITE, True),
    ("", 10, WHITE, False),
    ("India's 1000+ AWS stations provide critical data for weather forecasting, cyclone tracking,", 18, GRAY, False),
    ("and disaster management. Sensor faults inject bad data, degrading forecast accuracy.", 18, GRAY, False),
])

add_shape_with_text(s, 0.3, 4.0, 6.2, 3.2, CARD, [
    ("TEAM DETAILS", 18, BLUE, True),
    ("", 8, WHITE, False),
    ("1.  [Member Name]  -  Team Lead / ML Engineer", 18, LGRAY, False),
    ("2.  [Member Name]  -  Backend Developer", 18, LGRAY, False),
    ("3.  [Member Name]  -  Frontend Developer", 18, LGRAY, False),
    ("4.  [Member Name]  -  Hardware / IoT", 18, LGRAY, False),
    ("5.  [Member Name]  -  Data & Testing", 18, LGRAY, False),
    ("6.  [Member Name]  -  Research & Docs", 18, LGRAY, False),
])

add_shape_with_text(s, 6.7, 4.0, 6.3, 3.2, CARD, [
    ("COLLEGE & MENTOR", 18, BLUE, True),
    ("", 10, WHITE, False),
    ("College:  [Your College Name]", 20, WHITE, False),
    ("", 8, WHITE, False),
    ("Branch:   [Your Branch]", 20, WHITE, False),
    ("", 8, WHITE, False),
    ("Team ID:  [Your Team ID]", 20, WHITE, False),
    ("", 8, WHITE, False),
    ("Mentor:   [Faculty Mentor Name]", 20, WHITE, False),
])


# ================================================================
# SLIDE 2: Solution — 3 Layer Architecture
# ================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(s)
title_bar(s, "OUR SOLUTION: 3-Layer Intelligent Detection")

add_shape_with_text(s, 0.3, 1.5, 4.0, 3.0, CARD, [
    ("LAYER 1", 20, TEAL, True),
    ("WMO Rule-Based Physics", 22, WHITE, True),
    ("Latency: < 1ms", 16, TEAL, False),
    ("", 8, WHITE, False),
    ("\u2022  Range bounds check", 18, LGRAY, False),
    ("\u2022  Rate-of-change limits", 18, LGRAY, False),
    ("\u2022  Persistence / frozen check", 18, LGRAY, False),
    ("\u2022  Communication dropout", 18, LGRAY, False),
])

add_shape_with_text(s, 4.5, 1.5, 4.2, 3.0, CARD, [
    ("LAYER 2", 20, BLUE, True),
    ("LSTM Autoencoder", 22, WHITE, True),
    ("Latency: ~10ms", 16, BLUE, False),
    ("", 8, WHITE, False),
    ("\u2022  Learns normal temporal patterns", 18, LGRAY, False),
    ("\u2022  Reconstruction error = anomaly", 18, LGRAY, False),
    ("\u2022  Catches drift & complex faults", 18, LGRAY, False),
    ("\u2022  Dynamic EVT thresholds", 18, LGRAY, False),
])

add_shape_with_text(s, 8.9, 1.5, 4.1, 3.0, CARD, [
    ("LAYER 3", 20, ORANGE, True),
    ("Physics Validation", 22, WHITE, True),
    ("Latency: < 1ms", 16, ORANGE, False),
    ("", 8, WHITE, False),
    ("\u2022  Magnus dew-point formula", 18, LGRAY, False),
    ("\u2022  Multivariate consistency", 18, LGRAY, False),
    ("\u2022  Real storm vs sensor fault", 18, LGRAY, False),
    ("\u2022  Prevents false positives", 18, LGRAY, False),
])

add_shape_with_text(s, 0.3, 4.8, 12.7, 0.9, RGBColor(0x14, 0x2E, 0x14), [
    ("KEY INNOVATION:  No single layer catches everything. Together = 99.5% accuracy, 0% false positives.", 20, GREEN, True),
], border_color=GREEN)

# Stats row
big_stat(s, 0.3,  5.9, 3.0, 1.3, "ACCURACY",  "99.5%", "F1-Score: 0.99")
big_stat(s, 3.5,  5.9, 3.0, 1.3, "FALSE POSITIVES", "0%", "Zero false alarms")
big_stat(s, 6.7,  5.9, 3.1, 1.3, "LATENCY",   "<12ms", "Real-time on CPU")
big_stat(s, 10.0, 5.9, 3.0, 1.3, "HW COST",   "Rs.582", "ESP32+BMP280+DHT22")


# ================================================================
# SLIDE 3: Technical Architecture
# ================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(s)
title_bar(s, "TECHNICAL ARCHITECTURE")

# Data flow boxes
add_shape_with_text(s, 0.3, 1.5, 2.8, 2.6, CARD2, [
    ("HARDWARE", 16, ORANGE, True),
    ("ESP32 DevKit", 22, WHITE, True),
    ("", 6, WHITE, False),
    ("+ BMP280", 18, LGRAY, False),
    ("  (Pressure & Temp)", 16, GRAY, False),
    ("+ DHT22", 18, LGRAY, False),
    ("  (Humidity & Temp)", 16, GRAY, False),
], border_color=ORANGE)

add_shape_with_text(s, 3.3, 2.2, 0.8, 0.8, NAVY, [
    (">>>", 28, TEAL, True),
])

add_shape_with_text(s, 4.3, 1.5, 2.2, 2.6, CARD2, [
    ("PROTOCOL", 16, GREEN, True),
    ("MQTT", 22, WHITE, True),
    ("(Mosquitto)", 18, GRAY, False),
    ("", 6, WHITE, False),
    ("QoS 1 delivery", 16, LGRAY, False),
    ("LWT dropout", 16, LGRAY, False),
    ("Topic hierarchy", 16, LGRAY, False),
], border_color=GREEN)

add_shape_with_text(s, 6.7, 2.2, 0.8, 0.8, NAVY, [
    (">>>", 28, TEAL, True),
])

add_shape_with_text(s, 7.7, 1.5, 2.6, 2.6, CARD2, [
    ("AI ENGINE", 16, RED, True),
    ("FastAPI", 22, WHITE, True),
    ("(Python)", 18, GRAY, False),
    ("", 6, WHITE, False),
    ("Rule Engine", 16, TEAL, False),
    ("LSTM Autoencoder", 16, BLUE, False),
    ("Physics Validator", 16, ORANGE, False),
], border_color=RED)

add_shape_with_text(s, 10.5, 2.2, 0.8, 0.8, NAVY, [
    (">>>", 28, TEAL, True),
])

add_shape_with_text(s, 11.5, 1.5, 1.5, 2.6, CARD2, [
    ("DASHBOARD", 16, BLUE, True),
    ("React", 22, WHITE, True),
    ("", 6, WHITE, False),
    ("Live charts", 16, LGRAY, False),
    ("Alerts", 16, LGRAY, False),
    ("Explainability", 16, LGRAY, False),
    ("Fault inject", 16, LGRAY, False),
], border_color=BLUE)

# LSTM Detail
add_shape_with_text(s, 0.3, 4.4, 6.2, 2.8, CARD, [
    ("LSTM AUTOENCODER MODEL", 18, BLUE, True),
    ("", 6, WHITE, False),
    ("Input:    (batch, 60 timesteps, 3 sensors)", 18, LGRAY, False),
    ("Encoder:  LSTM(3 > 64) > LSTM(64 > 32) > FC(32 > 16)", 18, WHITE, False),
    ("Bottleneck:  16-dimensional compression", 18, TEAL, True),
    ("Decoder:  FC(16 > 32) > LSTM(32 > 64) > LSTM(64 > 3)", 18, WHITE, False),
    ("Output:   (batch, 60 timesteps, 3 sensors)", 18, LGRAY, False),
    ("", 6, WHITE, False),
    ("Loss: MSE  |  Threshold: mean + 2*std  |  Params: 57,196", 18, GRAY, False),
])

# Results
add_shape_with_text(s, 6.7, 4.4, 6.3, 2.8, CARD, [
    ("TRAINED MODEL RESULTS", 18, GREEN, True),
    ("", 6, WHITE, False),
    ("Dataset:   Jena Climate (420,551 readings, 2009-2016)", 18, LGRAY, False),
    ("Training:  50 epochs  |  50,000 samples  |  Adam optimizer", 18, LGRAY, False),
    ("", 6, WHITE, False),
    ("Spike Detection:    97%  (35/36)", 20, GREEN, True),
    ("Drift Detection:    100%  (28/28)", 20, GREEN, True),
    ("Noise Detection:    100%  (36/36)", 20, GREEN, True),
    ("False Positive Rate:  0%", 20, GREEN, True),
])


# ================================================================
# SLIDE 4: Feasibility & Viability
# ================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(s)
title_bar(s, "FEASIBILITY & VIABILITY")

add_shape_with_text(s, 0.3, 1.5, 4.0, 3.5, CARD, [
    ("TECHNICAL FEASIBILITY", 18, TEAL, True),
    ("", 8, WHITE, False),
    ("Already Built & Tested:", 20, GREEN, True),
    ("", 6, WHITE, False),
    ("\u2713  LSTM Autoencoder trained", 18, LGRAY, False),
    ("\u2713  99.5% accuracy on benchmark", 18, LGRAY, False),
    ("\u2713  Isolation Forest pre-filter", 18, LGRAY, False),
    ("\u2713  Full pipeline simulation", 18, LGRAY, False),
    ("\u2713  Explainability module", 18, LGRAY, False),
    ("", 8, WHITE, False),
    ("Hardware: ESP32 + BMP280 + DHT22", 18, ORANGE, False),
    ("All commercially available, Rs. 582", 18, GRAY, False),
])

add_shape_with_text(s, 4.5, 1.5, 4.0, 3.5, CARD, [
    ("ECONOMIC VIABILITY", 18, BLUE, True),
    ("", 8, WHITE, False),
    ("Per-Station Cost:", 20, WHITE, True),
    ("Hardware node: Rs. 582", 18, GREEN, False),
    ("vs manual inspection: Rs. 5000+/visit", 18, GRAY, False),
    ("", 8, WHITE, False),
    ("Cloud Backend:", 20, WHITE, True),
    ("AWS/GCP: Rs. 3000/month", 18, LGRAY, False),
    ("Handles 10,000+ stations", 18, LGRAY, False),
    ("", 8, WHITE, False),
    ("ROI: Prevents forecast failures", 18, ORANGE, False),
    ("that cost crores in disaster response", 18, ORANGE, False),
])

add_shape_with_text(s, 8.7, 1.5, 4.3, 3.5, CARD, [
    ("SUSTAINABILITY", 18, GREEN, True),
    ("", 8, WHITE, False),
    ("Open Source:", 20, WHITE, True),
    ("Python + React, no lock-in", 18, LGRAY, False),
    ("", 8, WHITE, False),
    ("Self-Improving:", 20, WHITE, True),
    ("Auto-retrains on new data", 18, LGRAY, False),
    ("Adapts to seasonal changes", 18, LGRAY, False),
    ("", 8, WHITE, False),
    ("Energy Efficient:", 20, WHITE, True),
    ("ESP32 deep-sleep: <1mA", 18, LGRAY, False),
    ("Solar-powered deployment", 18, LGRAY, False),
])

# Timeline
add_shape_with_text(s, 0.3, 5.3, 12.7, 0.5, CARD, [
    ("36-HOUR HACKATHON TIMELINE", 18, TEAL, True),
])

phases = [
    ("0-6h", "Hardware + Data", TEAL),
    ("6-14h", "ML Training", BLUE),
    ("14-22h", "Backend + UI", ORANGE),
    ("22-28h", "Integration", GREEN),
    ("28-36h", "Polish + Pitch", RED),
]
for i, (t, label, color) in enumerate(phases):
    add_shape_with_text(s, 0.3 + i * 2.56, 5.9, 2.4, 1.3, CARD2, [
        (t, 22, color, True),
        (label, 18, WHITE, True),
    ], border_color=color)


# ================================================================
# SLIDE 5: Impact & Use Cases
# ================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(s)
title_bar(s, "IMPACT & USE CASES")

big_stat(s, 0.3,  1.5, 3.0, 1.6, "AWS STATIONS", "1,000+", "across India benefit")
big_stat(s, 3.5,  1.5, 3.0, 1.6, "DATA ERRORS", "~30%", "of readings have anomalies")
big_stat(s, 6.7,  1.5, 3.1, 1.6, "FORECAST COST", "Rs.1000Cr+", "annual cost of bad data")
big_stat(s, 10.0, 1.5, 3.0, 1.6, "ALERT SPEED", "<500ms", "fault to notification")

add_shape_with_text(s, 0.3, 3.4, 6.2, 2.5, CARD, [
    ("USE CASES", 20, BLUE, True),
    ("", 8, WHITE, False),
    ("1. IMD Weather Forecasting", 20, WHITE, True),
    ("   Clean data = better predictions = saved lives", 16, GRAY, False),
    ("2. Cyclone & Flood Early Warning", 20, WHITE, True),
    ("   Reliable pressure/humidity for cyclone tracking", 16, GRAY, False),
    ("3. Agricultural Advisory Services", 20, WHITE, True),
    ("   Farmers depend on accurate weather for crops", 16, GRAY, False),
    ("4. Aviation Safety (METAR/TAF)", 20, WHITE, True),
    ("   Airports need trustworthy observations", 16, GRAY, False),
])

add_shape_with_text(s, 6.7, 3.4, 6.3, 2.5, RGBColor(0x14, 0x2E, 0x14), [
    ("GRAND CHALLENGE ANSWER", 20, GREEN, True),
    ("", 6, WHITE, False),
    ('"Can AI build a self-aware and self-healing', 20, WHITE, True),
    ('weather observation network?"', 20, WHITE, True),
    ("", 8, WHITE, False),
    ("YES. SkyGuard makes stations:", 18, TEAL, True),
    ("\u2022  Self-Aware: detects own sensor degradation", 18, LGRAY, False),
    ("\u2022  Self-Healing: suggests corrected values", 18, LGRAY, False),
    ("\u2022  Self-Maintaining: predicts sensor failure", 18, LGRAY, False),
], border_color=GREEN)

# Differentiation
add_shape_with_text(s, 0.3, 6.2, 6.2, 1.0, CARD, [
    ("OTHERS:  Threshold-based  |  Single model  |  Black-box  |  Software only", 18, GRAY, False),
])
add_shape_with_text(s, 6.7, 6.2, 6.3, 1.0, CARD2, [
    ("SKYGUARD:  3-Layer hybrid  |  Physics ML  |  Explainable AI  |  Live hardware", 18, GREEN, True),
], border_color=TEAL)


# ================================================================
# SLIDE 6: References & Prototype
# ================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(s)
title_bar(s, "REFERENCES & PROTOTYPE STATUS")

add_shape_with_text(s, 0.3, 1.5, 6.2, 5.5, CARD, [
    ("PROTOTYPE STATUS", 20, GREEN, True),
    ("", 10, WHITE, False),
    ("[DONE]  LSTM Autoencoder - trained, 99.5% accuracy", 18, GREEN, False),
    ("", 4, WHITE, False),
    ("[DONE]  Isolation Forest - trained, 200 trees", 18, GREEN, False),
    ("", 4, WHITE, False),
    ("[DONE]  Anomaly Injection Suite - 5 fault types", 18, GREEN, False),
    ("", 4, WHITE, False),
    ("[DONE]  Full Pipeline Simulation - end-to-end", 18, GREEN, False),
    ("", 4, WHITE, False),
    ("[DONE]  Physics Validation - Magnus + consistency", 18, GREEN, False),
    ("", 4, WHITE, False),
    ("[DONE]  Explainability - per-sensor attribution", 18, GREEN, False),
    ("", 4, WHITE, False),
    ("[DONE]  Streamlit Dashboard - live fault injection", 18, GREEN, False),
    ("", 4, WHITE, False),
    ("[WIP]   ESP32 Firmware - ready to flash", 18, ORANGE, False),
    ("", 4, WHITE, False),
    ("[WIP]   MQTT Integration - architecture designed", 18, ORANGE, False),
])

add_shape_with_text(s, 6.7, 1.5, 6.3, 5.5, CARD, [
    ("RESEARCH REFERENCES", 20, BLUE, True),
    ("", 10, WHITE, False),
    ("[1] WMO Guide to Instruments & Methods", 16, LGRAY, False),
    ("    of Observation (WMO-No. 8)", 16, GRAY, False),
    ("", 4, WHITE, False),
    ("[2] Zhao et al., MTAD-GAT: Graph Attention", 16, LGRAY, False),
    ("    for Time-series Anomaly Detection, ICDM 2020", 16, GRAY, False),
    ("", 4, WHITE, False),
    ("[3] Hundman et al., Detecting Anomalies Using", 16, LGRAY, False),
    ("    LSTMs & Dynamic Thresholding, KDD 2018", 16, GRAY, False),
    ("", 4, WHITE, False),
    ("[4] Jena Climate Dataset, Max Planck Institute", 16, LGRAY, False),
    ("", 4, WHITE, False),
    ("[5] Bosch BMP280 Datasheet", 16, LGRAY, False),
    ("", 4, WHITE, False),
    ("[6] Aosong DHT22/AM2302 Datasheet", 16, LGRAY, False),
    ("", 4, WHITE, False),
    ("[7] MQTT v3.1.1 Standard (ISO/IEC 20922)", 16, LGRAY, False),
    ("", 4, WHITE, False),
    ("[8] Lundberg & Lee, SHAP: Unified Approach", 16, LGRAY, False),
    ("    to Interpreting Predictions, NeurIPS 2017", 16, GRAY, False),
])

# ================================================================
# SAVE
# ================================================================
out = os.path.join(os.path.dirname(__file__), 'SkyGuard_AI_PPT_v2.pptx')
prs.save(out)
print(f"PPT saved: {out}")
