import pandas as pd
import numpy as np
import joblib
import json
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DATA_PATH = os.path.join("data", "jena_climate.csv")
MODELS_DIR = os.path.join("ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

print("Loading dataset from:", DATA_PATH)
df = pd.read_csv(DATA_PATH)

# Columns: T (degC), p (mbar), rh (%)
temp = df["T (degC)"].values[:120000]
pres = df["p (mbar)"].values[:120000]
hum = df["rh (%)"].values[:120000]

print(f"Extracting 15 rolling statistical features across {len(temp)} readings...")
window = 10
features_list = []

for i in range(window, len(temp), 2):  # stride 2 for 60,000 samples
    t_hist = temp[i-window:i]
    p_hist = pres[i-window:i]
    h_hist = hum[i-window:i]
    
    t_cur = temp[i]
    p_cur = pres[i]
    h_cur = hum[i]
    
    vec = [
        float(t_cur), float(np.mean(t_hist)), float(np.std(t_hist)), float(t_cur - np.mean(t_hist)), float(abs(t_cur - t_hist[-1])),
        float(p_cur), float(np.mean(p_hist)), float(np.std(p_hist)), float(p_cur - np.mean(p_hist)), float(abs(p_cur - p_hist[-1])),
        float(h_cur), float(np.mean(h_hist)), float(np.std(h_hist)), float(h_cur - np.mean(h_hist)), float(abs(h_cur - h_hist[-1]))
    ]
    features_list.append(vec)

X = np.array(features_list, dtype=np.float32)
print("Feature matrix shape:", X.shape)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Training IsolationForest(n_estimators=200, contamination=0.005)...")
model = IsolationForest(
    n_estimators=200,
    contamination=0.005,
    random_state=42,
    n_jobs=-1
)
model.fit(X_scaled)

# Test scores
scores = model.decision_function(X_scaled)
print(f"Decision function range on train: min={scores.min():.4f}, mean={scores.mean():.4f}, max={scores.max():.4f}")
print(f"Threshold (5th percentile): {np.percentile(scores, 0.5):.4f}")

# Save artifacts
joblib.dump(model, os.path.join(MODELS_DIR, "isolation_forest.joblib"))
joblib.dump(scaler, os.path.join(MODELS_DIR, "iforest_scaler.joblib"))

report_path = os.path.join(MODELS_DIR, "training_report.json")
if os.path.exists(report_path):
    with open(report_path, "r") as f:
        report = json.load(f)
else:
    report = {}

report["isolation_forest"] = {
    "n_estimators": 200,
    "contamination": 0.005,
    "threshold": float(np.percentile(scores, 0.5)),
    "n_features": 15,
    "training_samples": len(X),
    "status": "trained"
}

with open(report_path, "w") as f:
    json.dump(report, f, indent=2)

print("Saved calibrated Isolation Forest & 15-Feature StandardScaler!")
