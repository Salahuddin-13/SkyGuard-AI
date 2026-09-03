"""
Generate PPT using the official SIH2026 IDEA Presentation Format template.
Fills in SkyGuard AI content into the template's existing slides.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os, shutil

# Load the official template
template_path = r'C:\Users\Mohammed Salahuddin\Downloads\SIH2026-IDEA-Presentation-Format.pptx'
output_path = r'C:\Users\Mohammed Salahuddin\Desktop\SIH\SkyGuard_AI_OFFICIAL.pptx'

# Copy template first
shutil.copy2(template_path, output_path)
prs = Presentation(output_path)

def clear_and_set(shape, lines, default_size=18):
    """Clear a shape's text and set new content."""
    tf = shape.text_frame
    # Clear existing paragraphs
    for i in range(len(tf.paragraphs) - 1, 0, -1):
        p = tf.paragraphs[i]
        p._element.getparent().remove(p._element)
    
    for i, item in enumerate(lines):
        if isinstance(item, str):
            text, size, bold = item, default_size, False
        else:
            text, size, bold = item
        
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        
        p.text = text
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.name = 'Calibri'

def find_text_shapes(slide):
    """Find all text-containing shapes in a slide, sorted by position."""
    shapes = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            shapes.append(shape)
    return shapes

# Print slide info for debugging
print(f"Template has {len(prs.slides)} slides\n")
for si, slide in enumerate(prs.slides):
    print(f"--- Slide {si+1} ---")
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text[:80].replace('\n', ' | ')
            print(f"  Shape: left={shape.left}, top={shape.top}, text='{text}'")

# ================================================================
# SLIDE 1: TITLE PAGE
# ================================================================
print("\n\nFilling Slide 1: Title Page...")
slide1 = prs.slides[0]
shapes = find_text_shapes(slide1)

# Find the bullet point area (usually the largest text shape in the middle)
for shape in shapes:
    text = shape.text_frame.text
    if 'Problem Statement ID' in text or 'Problem Statement Title' in text:
        clear_and_set(shape, [
            ("Problem Statement ID - SIH26073", 22, True),
            ("", 10, False),
            ("Problem Statement Title - Intelligent Real-Time Anomaly", 20, True),
            ("Detection for AWS (SkyGuard AI)", 20, True),
            ("", 10, False),
            ("Theme - Disaster Management", 20, False),
            ("", 10, False),
            ("PS Category - Software", 20, False),
            ("", 10, False),
            ("Team ID - [Your Team ID]", 20, False),
            ("", 10, False),
            ("Team Name - [Your Team Name]", 20, False),
        ])
        print("  Filled title page content")
        break

# ================================================================
# SLIDE 2: IDEA TITLE / PROPOSED SOLUTION
# ================================================================
print("Filling Slide 2: Idea Title...")
slide2 = prs.slides[1]

for shape in find_text_shapes(slide2):
    text = shape.text_frame.text
    if 'IDEA TITLE' in text:
        clear_and_set(shape, [
            ("SKYGUARD AI", 36, True),
        ])
    elif 'Proposed Solution' in text or 'Detailed explanation' in text:
        clear_and_set(shape, [
            ("3-Layer AI Anomaly Detection for Weather Stations", 24, True),
            ("", 10, False),
            ("Proposed Solution:", 20, True),
            ("SkyGuard AI monitors AWS sensor data (temperature, pressure, humidity)", 18, False),
            ("in real-time and detects sensor faults using a 3-layer hybrid approach:", 18, False),
            ("", 8, False),
            ("Layer 1: WMO Rule Engine - catches range violations, spikes, frozen values (<1ms)", 18, False),
            ("Layer 2: LSTM Autoencoder - deep learning on temporal patterns, catches drift (~10ms)", 18, False),
            ("Layer 3: Physics Validator - Magnus dew-point formula, prevents false positives (<1ms)", 18, False),
            ("", 8, False),
            ("Innovation & Uniqueness:", 20, True),
            ("No single layer catches everything. The 3-layer hybrid achieves 99.5% accuracy", 18, False),
            ("with 0% false positives. Explainable AI tells operators WHICH sensor failed and WHY.", 18, False),
            ("Live hardware demo: ESP32 + BMP280 + DHT22 with real-time fault injection.", 18, False),
        ])
        print("  Filled idea content")
        break

# ================================================================
# SLIDE 3: TECHNICAL APPROACH
# ================================================================
print("Filling Slide 3: Technical Approach...")
slide3 = prs.slides[2]

for shape in find_text_shapes(slide3):
    text = shape.text_frame.text
    if 'Technologies' in text or 'Methodology' in text:
        clear_and_set(shape, [
            ("Technologies Used:", 22, True),
            ("  Hardware: ESP32 DevKit + BMP280 (pressure/temp) + DHT22 (humidity/temp)", 17, False),
            ("  Protocol: MQTT (Mosquitto broker) with QoS 1 and Last Will Testament", 17, False),
            ("  Backend: Python 3.12 + FastAPI + WebSocket for real-time streaming", 17, False),
            ("  ML Framework: PyTorch (LSTM Autoencoder, 57,196 parameters)", 17, False),
            ("  Classical ML: scikit-learn Isolation Forest (200 trees, fast pre-filter)", 17, False),
            ("  Frontend: Streamlit real-time dashboard with fault injection controls", 17, False),
            ("  Dataset: Jena Climate (Max Planck, 420,551 readings, 2009-2016)", 17, False),
            ("", 8, False),
            ("Architecture: ESP32 --> MQTT --> FastAPI (Rule Engine + LSTM-AE + Physics) --> Dashboard", 17, True),
            ("", 8, False),
            ("LSTM Autoencoder: Input(60x3) > Encoder LSTM(3>64>32) > Bottleneck(16) > Decoder LSTM(32>64>3)", 16, False),
            ("Trained 50 epochs on 50K samples | Val Loss: 0.069 | Spike: 97% | Drift: 100% | F1: 0.99", 16, False),
        ])
        print("  Filled technical approach")
        break

# ================================================================
# SLIDE 4: FEASIBILITY AND VIABILITY
# ================================================================
print("Filling Slide 4: Feasibility & Viability...")
slide4 = prs.slides[3]

for shape in find_text_shapes(slide4):
    text = shape.text_frame.text
    if 'Analysis' in text or 'feasibility' in text.lower() or 'challenges' in text.lower():
        clear_and_set(shape, [
            ("Feasibility - Already Built & Tested:", 22, True),
            ("  [DONE] LSTM Autoencoder trained on real weather data (99.5% accuracy)", 17, False),
            ("  [DONE] Isolation Forest for fast pre-filtering (200 trees, <1ms)", 17, False),
            ("  [DONE] Full pipeline simulation working end-to-end", 17, False),
            ("  [DONE] Streamlit dashboard with live fault injection demo", 17, False),
            ("  [WIP] ESP32 hardware integration (components ordered, Rs.582 total)", 17, False),
            ("", 8, False),
            ("Challenges & Mitigations:", 22, True),
            ("  Challenge: Frozen values not caught by LSTM (learned as 'normal')", 17, False),
            ("  Solution: Layer 1 Rule Engine catches frozen values via persistence check", 17, False),
            ("  Challenge: False positives during real extreme weather events", 17, False),
            ("  Solution: Layer 3 Physics Validator checks multivariate consistency", 17, False),
            ("  Challenge: Scalability to 1000+ stations", 17, False),
            ("  Solution: MQTT topic hierarchy + stateless microservice backend", 17, False),
        ])
        print("  Filled feasibility")
        break

# ================================================================
# SLIDE 5: IMPACT AND BENEFITS
# ================================================================
print("Filling Slide 5: Impact & Benefits...")
slide5 = prs.slides[4]

for shape in find_text_shapes(slide5):
    text = shape.text_frame.text
    if 'Potential impact' in text or 'Benefits' in text:
        clear_and_set(shape, [
            ("Impact on Target Audience:", 22, True),
            ("  1000+ AWS stations across India benefit from automated quality control", 18, False),
            ("  IMD meteorologists get clean data for weather forecasting", 18, False),
            ("  Disaster management agencies get reliable early warnings", 18, False),
            ("  Farmers get accurate agricultural advisories", 18, False),
            ("  Aviation gets trustworthy METAR/TAF observations", 18, False),
            ("", 8, False),
            ("Benefits:", 22, True),
            ("  Social: Prevents missed disaster warnings, saves lives during cyclones/floods", 18, False),
            ("  Economic: Avoids Rs.1000 Cr+ annual cost of inaccurate forecasts", 18, False),
            ("  Environmental: Better climate monitoring with trusted sensor data", 18, False),
            ("  Technical: Self-aware stations predict own sensor degradation", 18, False),
            ("", 8, False),
            ("Grand Challenge Answer: Yes, AI can build a self-aware, self-healing weather network.", 18, True),
        ])
        print("  Filled impact")
        break

# ================================================================
# SLIDE 6: RESEARCH AND REFERENCES
# ================================================================
print("Filling Slide 6: Research & References...")
if len(prs.slides) >= 6:
    slide6 = prs.slides[5]
    for shape in find_text_shapes(slide6):
        text = shape.text_frame.text.lower()
        if 'literature' in text or 'research' in text or 'reference' in text or 'related' in text:
            clear_and_set(shape, [
                ("Research References:", 22, True),
                ("", 6, False),
                ("[1] WMO Guide to Instruments & Methods of Observation (WMO-No. 8)", 16, False),
                ("[2] Zhao et al., 'MTAD-GAT: Multivariate Time-series Anomaly Detection", 16, False),
                ("     via Graph Attention Network', ICDM 2020", 16, False),
                ("[3] Hundman et al., 'Detecting Spacecraft Anomalies Using LSTMs and", 16, False),
                ("     Nonparametric Dynamic Thresholding', KDD 2018", 16, False),
                ("[4] Jena Climate Dataset, Max Planck Institute for Biogeochemistry", 16, False),
                ("[5] Bosch BMP280 Datasheet (BST-BMP280-DS001)", 16, False),
                ("[6] Aosong DHT22/AM2302 Datasheet", 16, False),
                ("[7] MQTT v3.1.1 Standard (ISO/IEC 20922:2016)", 16, False),
                ("[8] Lundberg & Lee, 'SHAP: Unified Approach to Interpreting", 16, False),
                ("     Model Predictions', NeurIPS 2017", 16, False),
                ("", 8, False),
                ("Prototype: ML models trained, dashboard working. GitHub: [Your URL]", 16, True),
            ], default_size=16)
            print("  Filled references")
            break

# Save
prs.save(output_path)
print(f"\nDONE! Saved to: {output_path}")
