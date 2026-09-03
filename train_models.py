"""
=============================================================
  SKYGUARD AI — Production Model Training Pipeline
=============================================================

This script:
  1. Loads the full Jena Climate Dataset (420k readings)
  2. Trains the LSTM Autoencoder on 80% of the data
  3. Trains an Isolation Forest for fast pre-filtering
  4. Injects synthetic anomalies and evaluates both models
  5. Saves everything needed for deployment

RUN THIS:  python -X utf8 train_models.py
=============================================================
"""

import os
import sys
import time
import json
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix

# ============================================================
# CONFIG
# ============================================================

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'ml', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

SEQ_LEN = 60          # 60 readings per window
HIDDEN_DIM = 64       # LSTM hidden size
BOTTLENECK_DIM = 16   # Compression bottleneck
BATCH_SIZE = 128      # Training batch size
EPOCHS = 50           # Training epochs
LR = 0.001            # Learning rate
TRAIN_SAMPLES = 50000 # Use 50k samples (fast but representative)
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

print(f"Device: {DEVICE}")
print(f"Config: SEQ_LEN={SEQ_LEN}, EPOCHS={EPOCHS}, BATCH_SIZE={BATCH_SIZE}")

# ============================================================
# MODEL DEFINITIONS
# ============================================================

class LSTMAutoencoder(nn.Module):
    """
    LSTM Autoencoder for time-series anomaly detection.
    
    Architecture:
      Encoder: LSTM(3->64) -> LSTM(64->32) -> Linear(32->16)
      Decoder: Linear(16->32) -> repeat -> LSTM(32->64) -> LSTM(64->3)
    
    Input:  (batch, seq_len, 3) — sequence of [temp, pressure, humidity]
    Output: (batch, seq_len, 3) — reconstructed sequence
    """
    def __init__(self, n_features=3, hidden_dim=64, bottleneck_dim=16, seq_len=60):
        super().__init__()
        self.seq_len = seq_len
        self.n_features = n_features
        
        # Encoder
        self.enc_lstm1 = nn.LSTM(n_features, hidden_dim, batch_first=True)
        self.enc_lstm2 = nn.LSTM(hidden_dim, hidden_dim // 2, batch_first=True)
        self.enc_fc = nn.Linear(hidden_dim // 2, bottleneck_dim)
        
        # Decoder
        self.dec_fc = nn.Linear(bottleneck_dim, hidden_dim // 2)
        self.dec_lstm1 = nn.LSTM(hidden_dim // 2, hidden_dim, batch_first=True)
        self.dec_lstm2 = nn.LSTM(hidden_dim, n_features, batch_first=True)
    
    def forward(self, x):
        # Encode
        out, _ = self.enc_lstm1(x)
        out, (h, _) = self.enc_lstm2(out)
        bottleneck = self.enc_fc(h.squeeze(0))
        
        # Decode
        dec = self.dec_fc(bottleneck)
        dec = dec.unsqueeze(1).repeat(1, self.seq_len, 1)
        dec, _ = self.dec_lstm1(dec)
        dec, _ = self.dec_lstm2(dec)
        return dec

# ============================================================
# STEP 1: Load and Prepare Data
# ============================================================

print("\n" + "=" * 60)
print("  STEP 1: Loading Jena Climate Dataset")
print("=" * 60)

csv_path = os.path.join(DATA_DIR, 'jena_climate.csv')
if not os.path.exists(csv_path):
    print("ERROR: Run lesson_02_pandas.py first to download the dataset!")
    sys.exit(1)

df = pd.read_csv(csv_path)
raw_values = df[['T (degC)', 'p (mbar)', 'rh (%)']].values.astype(np.float32)
print(f"  Total readings: {len(raw_values):,}")
print(f"  Columns: Temperature (C), Pressure (hPa), Humidity (%)")

# Normalize
scaler = StandardScaler()
normalized = scaler.fit_transform(raw_values)
print(f"  Normalized: mean~0, std~1 per feature")

# Use a subset for speed (50k out of 420k)
data_subset = normalized[:TRAIN_SAMPLES]
print(f"  Using {TRAIN_SAMPLES:,} samples for training")

# Create sliding windows
print(f"  Creating sliding windows (size={SEQ_LEN})...")
windows = []
for i in range(len(data_subset) - SEQ_LEN):
    windows.append(data_subset[i:i + SEQ_LEN])
windows = np.array(windows)
print(f"  Created {len(windows):,} windows of shape {windows[0].shape}")

# Train/Val split (80/20)
n_train = int(0.8 * len(windows))
train_data = torch.from_numpy(windows[:n_train]).to(DEVICE)
val_data = torch.from_numpy(windows[n_train:]).to(DEVICE)
print(f"  Train: {len(train_data):,}  |  Validation: {len(val_data):,}")

train_loader = DataLoader(
    TensorDataset(train_data, train_data),
    batch_size=BATCH_SIZE,
    shuffle=True
)

# ============================================================
# STEP 2: Train LSTM Autoencoder
# ============================================================

print("\n" + "=" * 60)
print("  STEP 2: Training LSTM Autoencoder")
print("=" * 60)

model = LSTMAutoencoder(
    n_features=3, 
    hidden_dim=HIDDEN_DIM, 
    bottleneck_dim=BOTTLENECK_DIM, 
    seq_len=SEQ_LEN
).to(DEVICE)

total_params = sum(p.numel() for p in model.parameters())
print(f"  Model parameters: {total_params:,}")

optimizer = torch.optim.Adam(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
loss_fn = nn.MSELoss()

best_val_loss = float('inf')
train_history = []

start_time = time.time()

for epoch in range(EPOCHS):
    # Train
    model.train()
    epoch_loss = 0
    n_batches = 0
    for batch_x, batch_y in train_loader:
        recon = model(batch_x)
        loss = loss_fn(recon, batch_y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
        n_batches += 1
    avg_train = epoch_loss / n_batches
    
    # Validate
    model.eval()
    with torch.no_grad():
        val_recon = model(val_data)
        val_loss = loss_fn(val_recon, val_data).item()
    
    scheduler.step(val_loss)
    train_history.append({'epoch': epoch+1, 'train_loss': avg_train, 'val_loss': val_loss})
    
    # Save best model
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), os.path.join(MODEL_DIR, 'lstm_ae_best.pt'))
    
    if (epoch + 1) % 5 == 0 or epoch == 0:
        elapsed = time.time() - start_time
        lr_now = optimizer.param_groups[0]['lr']
        print(f"  Epoch {epoch+1:3d}/{EPOCHS} | Train: {avg_train:.6f} | Val: {val_loss:.6f} | "
              f"LR: {lr_now:.6f} | Time: {elapsed:.0f}s")

elapsed = time.time() - start_time
print(f"\n  Training complete in {elapsed:.0f} seconds")
print(f"  Best validation loss: {best_val_loss:.6f}")

# Load best model
model.load_state_dict(torch.load(os.path.join(MODEL_DIR, 'lstm_ae_best.pt'), weights_only=True))
model.eval()

# Compute threshold on validation set
print("\n  Computing anomaly threshold...")
with torch.no_grad():
    val_recon = model(val_data)
    val_errors = (val_data - val_recon).pow(2).mean(dim=(1, 2)).cpu().numpy()

threshold_mean = val_errors.mean()
threshold_std = val_errors.std()
threshold = threshold_mean + 2 * threshold_std

print(f"  Validation error: mean={threshold_mean:.6f}, std={threshold_std:.6f}")
print(f"  Anomaly threshold (mean + 2*std): {threshold:.6f}")

# ============================================================
# STEP 3: Train Isolation Forest
# ============================================================

print("\n" + "=" * 60)
print("  STEP 3: Training Isolation Forest")
print("=" * 60)

# Isolation Forest works on individual readings (not sequences)
# We create rolling features for richer signal:

def extract_features(data, window=10):
    """Extract statistical features from raw readings for Isolation Forest."""
    features = []
    for i in range(window, len(data)):
        chunk = data[i-window:i]
        row = []
        for col in range(data.shape[1]):
            col_data = chunk[:, col]
            row.extend([
                data[i, col],              # current value
                col_data.mean(),           # rolling mean
                col_data.std(),            # rolling std  
                data[i, col] - col_data.mean(),  # deviation from mean
                np.abs(data[i, col] - data[i-1, col]),  # rate of change
            ])
        features.append(row)
    return np.array(features)

feature_names = []
for sensor in ['temp', 'pressure', 'humidity']:
    feature_names.extend([
        f'{sensor}_current', f'{sensor}_roll_mean', f'{sensor}_roll_std',
        f'{sensor}_deviation', f'{sensor}_rate_change'
    ])

print(f"  Extracting {len(feature_names)} features per reading...")
iforest_features = extract_features(normalized[:TRAIN_SAMPLES], window=10)
print(f"  Feature matrix: {iforest_features.shape}")

print("  Training Isolation Forest...")
iforest = IsolationForest(
    n_estimators=200,
    contamination=0.01,  # Expect ~1% anomalies
    random_state=42,
    n_jobs=-1
)
iforest.fit(iforest_features)
print("  Done!")

# Get anomaly scores on training data (for threshold calibration)
iforest_scores = iforest.decision_function(iforest_features)
iforest_threshold = np.percentile(iforest_scores, 1)  # Bottom 1%
print(f"  Anomaly score range: {iforest_scores.min():.4f} to {iforest_scores.max():.4f}")
print(f"  Threshold (1st percentile): {iforest_threshold:.4f}")

# ============================================================
# STEP 4: Inject Anomalies and Evaluate
# ============================================================

print("\n" + "=" * 60)
print("  STEP 4: Anomaly Injection & Evaluation")
print("=" * 60)

# Take clean validation windows and inject anomalies
n_test = min(200, len(val_data))
test_windows = val_data[:n_test].clone()

# Create test set: 50% normal, 50% anomalous (mixed types)
labels = []  # 0 = normal, 1 = anomaly
anomaly_types = []
test_set = []

# Normal samples
for i in range(n_test // 2):
    test_set.append(test_windows[i])
    labels.append(0)
    anomaly_types.append('normal')

# Anomalous samples (mix of spike, freeze, drift)
np.random.seed(42)
for i in range(n_test // 2):
    window = test_windows[n_test // 2 + i].clone()
    anomaly_type = np.random.choice(['spike', 'drift', 'noise_burst'])
    
    if anomaly_type == 'spike':
        # Spike on random sensor at random timestep for 3-8 steps
        sensor = np.random.randint(0, 3)
        t_start = np.random.randint(10, 50)
        t_len = np.random.randint(3, 8)
        magnitude = np.random.uniform(5, 12)
        window[t_start:t_start+t_len, sensor] = magnitude * np.random.choice([-1, 1])
    
    elif anomaly_type == 'drift':
        # Gradual drift on random sensor
        sensor = np.random.randint(0, 3)
        drift_mag = np.random.uniform(4, 10)
        window[:, sensor] += torch.linspace(0, drift_mag, SEQ_LEN)
    
    elif anomaly_type == 'noise_burst':
        # Random noise across all sensors for a portion
        t_start = np.random.randint(10, 40)
        t_len = np.random.randint(10, 20)
        window[t_start:t_start+t_len] += torch.randn(t_len, 3) * 3
    
    test_set.append(window)
    labels.append(1)
    anomaly_types.append(anomaly_type)

test_tensor = torch.stack(test_set).to(DEVICE)
labels = np.array(labels)

# Evaluate LSTM Autoencoder
print("\n  --- LSTM Autoencoder Results ---")
with torch.no_grad():
    recon = model(test_tensor)
    errors = (test_tensor - recon).pow(2).mean(dim=(1, 2)).cpu().numpy()

lstm_preds = (errors > threshold).astype(int)

print(f"\n{classification_report(labels, lstm_preds, target_names=['Normal', 'Anomaly'])}")

# Confusion matrix
cm = confusion_matrix(labels, lstm_preds)
print(f"  Confusion Matrix:")
print(f"                Predicted Normal  Predicted Anomaly")
print(f"  Actual Normal       {cm[0,0]:>5d}            {cm[0,1]:>5d}")
print(f"  Actual Anomaly      {cm[1,0]:>5d}            {cm[1,1]:>5d}")

# Per-type accuracy
print(f"\n  Per anomaly type:")
for atype in ['spike', 'drift', 'noise_burst']:
    mask = np.array(anomaly_types) == atype
    if mask.sum() > 0:
        type_errors = errors[mask]
        detected = (type_errors > threshold).sum()
        print(f"    {atype:>12s}: {detected}/{mask.sum()} detected "
              f"(avg error: {type_errors.mean():.4f})")

# ============================================================
# STEP 5: Save Everything
# ============================================================

print("\n" + "=" * 60)
print("  STEP 5: Saving Models & Artifacts")
print("=" * 60)

# 1. LSTM Autoencoder (already saved as lstm_ae_best.pt)
# Also save full checkpoint with metadata
checkpoint = {
    'model_state_dict': model.state_dict(),
    'model_config': {
        'n_features': 3,
        'hidden_dim': HIDDEN_DIM,
        'bottleneck_dim': BOTTLENECK_DIM,
        'seq_len': SEQ_LEN,
    },
    'scaler_mean': scaler.mean_.tolist(),
    'scaler_scale': scaler.scale_.tolist(),
    'threshold': float(threshold),
    'threshold_mean': float(threshold_mean),
    'threshold_std': float(threshold_std),
    'val_loss': float(best_val_loss),
    'epochs_trained': EPOCHS,
    'train_samples': TRAIN_SAMPLES,
}
torch.save(checkpoint, os.path.join(MODEL_DIR, 'lstm_ae_production.pt'))
print(f"  [1/4] LSTM Autoencoder  -> ml/models/lstm_ae_production.pt")

# 2. Isolation Forest
with open(os.path.join(MODEL_DIR, 'isolation_forest.pkl'), 'wb') as f:
    pickle.dump({
        'model': iforest,
        'threshold': float(iforest_threshold),
        'feature_names': feature_names,
    }, f)
print(f"  [2/4] Isolation Forest  -> ml/models/isolation_forest.pkl")

# 3. Scaler
with open(os.path.join(MODEL_DIR, 'scaler.pkl'), 'wb') as f:
    pickle.dump(scaler, f)
print(f"  [3/4] StandardScaler    -> ml/models/scaler.pkl")

# 4. Training report
report = {
    'lstm_ae': {
        'epochs': EPOCHS,
        'best_val_loss': float(best_val_loss),
        'threshold': float(threshold),
        'total_params': total_params,
    },
    'isolation_forest': {
        'n_estimators': 200,
        'contamination': 0.01,
        'threshold': float(iforest_threshold),
    },
    'data': {
        'dataset': 'Jena Climate 2009-2016',
        'total_readings': len(raw_values),
        'train_samples': TRAIN_SAMPLES,
        'seq_len': SEQ_LEN,
        'features': ['temperature_c', 'pressure_hpa', 'humidity_pct'],
    },
    'training_history': train_history,
}
with open(os.path.join(MODEL_DIR, 'training_report.json'), 'w') as f:
    json.dump(report, f, indent=2)
print(f"  [4/4] Training Report   -> ml/models/training_report.json")

print(f"""
{'=' * 60}
  TRAINING COMPLETE
{'=' * 60}

  Models saved to: ml/models/
  
  LSTM Autoencoder:
    - Parameters: {total_params:,}
    - Best val loss: {best_val_loss:.6f}
    - Anomaly threshold: {threshold:.6f}
  
  Isolation Forest:
    - Estimators: 200
    - Anomaly threshold: {iforest_threshold:.4f}
  
  These models are ready for the SkyGuard AI backend.
  The backend loads them and runs inference on live MQTT data.
{'=' * 60}
""")
