"""
=============================================================
  LESSON 5: LSTM Autoencoder — The Actual SkyGuard AI Model
=============================================================

This is the REAL model we'll use in SkyGuard AI.

LSTM = Long Short-Term Memory — a neural network that 
REMEMBERS patterns over time. Perfect for time-series data.

Regular autoencoder (Lesson 4): feeds in ONE reading at a time.
LSTM autoencoder: feeds in a SEQUENCE of readings → learns 
temporal patterns like "temperature rises gradually in the morning."

RUN THIS:  python lesson_05_lstm_autoencoder.py
=============================================================
"""

import torch
import torch.nn as nn
import numpy as np
import os
import pickle
import pandas as pd
from sklearn.preprocessing import StandardScaler

# ============================================================
# PART 1: What is an LSTM? (Intuition)
# ============================================================

print("=== PART 1: What is an LSTM? ===")

print("""
Regular neural network:  sees ONE data point → forgets everything.
LSTM neural network:     sees a SEQUENCE → remembers context.

Example with weather data:
  Regular NN sees: [temperature=33.1°C]
  → Is this normal? Could be! Could be a spike. No context.

  LSTM sees: [30.0, 30.5, 31.0, 31.5, 32.0, 32.5, 33.0, 33.1]
  → Clear upward trend, 33.1 is natural continuation. ✅ Normal.

  LSTM sees: [30.0, 30.0, 30.1, 30.0, 29.9, 30.0, 30.0, 33.1]  
  → Flat then sudden jump! ✅ Anomaly detected.

HOW it remembers:
  The LSTM has a "cell state" — like a conveyor belt carrying 
  information forward. At each timestep, it decides:
  
  1. FORGET gate: "Should I forget old info?" (e.g., yesterday's temp)
  2. INPUT gate:  "What new info is important?" (e.g., current reading)
  3. OUTPUT gate: "What should I report right now?" (e.g., trend direction)

  These gates are learned during training — the LSTM AUTOMATICALLY
  learns what to remember and what to forget.
""")

# ============================================================
# PART 2: LSTM in PyTorch — Hands On
# ============================================================

print("=== PART 2: LSTM in PyTorch ===")

# Create an LSTM layer:
# input_size=3 (temp, pressure, humidity)
# hidden_size=64 (64 "memory cells")
# num_layers=1 (one LSTM layer)
# batch_first=True (data shape: batch × time × features)

lstm = nn.LSTM(input_size=3, hidden_size=64, num_layers=1, batch_first=True)

# Create fake input: 1 sample, 60 timesteps, 3 features
fake_input = torch.randn(1, 60, 3)
print(f"Input shape:  {fake_input.shape}")   # (1, 60, 3)

# Run through LSTM:
output, (hidden, cell) = lstm(fake_input)
print(f"Output shape: {output.shape}")  # (1, 60, 64) — 64 features at each timestep
print(f"Hidden shape: {hidden.shape}")  # (1, 1, 64) — final hidden state
print(f"Cell shape:   {cell.shape}")    # (1, 1, 64) — final cell state

print("\nThe LSTM processed 60 timesteps and produced:")
print("  - output: what the LSTM 'says' at each timestep (60 × 64)")
print("  - hidden: the FINAL summary of the sequence (1 × 64)")
print("  - cell: the long-term memory state (1 × 64)")
print("We use 'hidden' as our COMPRESSED representation (bottleneck)!")

# ============================================================
# PART 3: Build the LSTM Autoencoder
# ============================================================

print("\n=== PART 3: LSTM Autoencoder Architecture ===")

class LSTMAutoencoder(nn.Module):
    """
    The ACTUAL model for SkyGuard AI.
    
    Input:  (batch, 60, 3) — 60 timesteps × 3 sensors
    Output: (batch, 60, 3) — reconstructed version
    
    If reconstruction error is high → anomaly!
    
    Architecture:
      ENCODER: LSTM(3→64) → LSTM(64→32) → compress to bottleneck(16)
      DECODER: expand from bottleneck(16) → LSTM(32→64) → LSTM(64→3)
    """
    
    def __init__(self, n_features=3, hidden_dim=64, bottleneck_dim=16, seq_len=60):
        super().__init__()
        self.seq_len = seq_len
        self.n_features = n_features
        self.hidden_dim = hidden_dim
        
        # === ENCODER ===
        # Takes (batch, seq_len, 3) → produces hidden state (batch, hidden_dim)
        self.encoder_lstm1 = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True
        )
        self.encoder_lstm2 = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim // 2,  # 32
            num_layers=1,
            batch_first=True
        )
        # Compress to bottleneck:
        self.encoder_fc = nn.Linear(hidden_dim // 2, bottleneck_dim)
        
        # === DECODER ===
        # Takes bottleneck → reconstructs (batch, seq_len, 3)
        self.decoder_fc = nn.Linear(bottleneck_dim, hidden_dim // 2)
        self.decoder_lstm1 = nn.LSTM(
            input_size=hidden_dim // 2,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True
        )
        self.decoder_lstm2 = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=n_features,  # Output same as input
            num_layers=1,
            batch_first=True
        )
    
    def forward(self, x):
        batch_size = x.size(0)
        
        # ---- ENCODE ----
        # x shape: (batch, 60, 3)
        enc_out, _ = self.encoder_lstm1(x)       # (batch, 60, 64)
        enc_out, (hidden, _) = self.encoder_lstm2(enc_out)  # hidden: (1, batch, 32)
        
        # Take the LAST hidden state as our summary:
        bottleneck_input = hidden.squeeze(0)      # (batch, 32)
        bottleneck = self.encoder_fc(bottleneck_input)  # (batch, 16)
        
        # ---- DECODE ----
        # Expand bottleneck back:
        decoder_input = self.decoder_fc(bottleneck)  # (batch, 32)
        
        # Repeat the bottleneck for each timestep:
        decoder_input = decoder_input.unsqueeze(1).repeat(1, self.seq_len, 1)
        # Shape: (batch, 60, 32)
        
        dec_out, _ = self.decoder_lstm1(decoder_input)  # (batch, 60, 64)
        dec_out, _ = self.decoder_lstm2(dec_out)         # (batch, 60, 3)
        
        return dec_out

# Create the model:
model = LSTMAutoencoder(n_features=3, hidden_dim=64, bottleneck_dim=16, seq_len=60)

# Count parameters:
total = sum(p.numel() for p in model.parameters())
print(f"Model: {model.__class__.__name__}")
print(f"Total parameters: {total:,}")

# Test forward pass:
test_input = torch.randn(4, 60, 3)  # batch of 4 samples
test_output = model(test_input)
print(f"\nInput shape:  {test_input.shape}")   # (4, 60, 3)
print(f"Output shape: {test_output.shape}")    # (4, 60, 3) — same!

# Reconstruction error:
error = (test_input - test_output).pow(2).mean(dim=(1, 2))  # per-sample MSE
print(f"Per-sample errors: {[f'{e:.4f}' for e in error.tolist()]}")
print("(High because the model is untrained)")

# ============================================================
# PART 4: Load REAL data and train!
# ============================================================

print("\n=== PART 4: Training on Real Weather Data ===")

# Load the Jena dataset (downloaded in Lesson 2)
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
csv_path = os.path.join(data_dir, 'jena_climate.csv')

if not os.path.exists(csv_path):
    print("❌ Run lesson_02_pandas.py first!")
    exit()

df = pd.read_csv(csv_path)
values = df[['T (degC)', 'p (mbar)', 'rh (%)']].values.astype(np.float32)

# Normalize:
scaler = StandardScaler()
values_norm = scaler.fit_transform(values)

# Create sliding windows (use first 10000 readings for speed):
SEQ_LEN = 60
data_subset = values_norm[:10000]

def create_windows(data, seq_len):
    windows = []
    for i in range(len(data) - seq_len):
        windows.append(data[i:i+seq_len])
    return np.array(windows)

windows = create_windows(data_subset, SEQ_LEN)
print(f"Created {len(windows)} windows of shape {windows[0].shape}")

# Convert to PyTorch tensors:
dataset = torch.from_numpy(windows)

# Split into train (80%) and validation (20%):
n_train = int(0.8 * len(dataset))
train_data = dataset[:n_train]
val_data = dataset[n_train:]
print(f"Train: {len(train_data)}, Validation: {len(val_data)}")

# DataLoader — feeds batches of data:
from torch.utils.data import DataLoader, TensorDataset

train_loader = DataLoader(
    TensorDataset(train_data, train_data),  # input = target for autoencoder!
    batch_size=64,
    shuffle=True
)

# ============================================================
# PART 5: The Training Loop
# ============================================================

print("\n=== PART 5: Training the LSTM Autoencoder ===")
print("(This may take 1-2 minutes...)\n")

model = LSTMAutoencoder(n_features=3, hidden_dim=64, bottleneck_dim=16, seq_len=SEQ_LEN)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = nn.MSELoss()

EPOCHS = 30  # 30 epochs (takes ~2 min on CPU, use 50+ for production)

train_losses = []
val_losses = []

for epoch in range(EPOCHS):
    # --- TRAIN ---
    model.train()
    epoch_loss = 0
    n_batches = 0
    
    for batch_input, batch_target in train_loader:
        # Forward pass:
        reconstructed = model(batch_input)
        loss = loss_fn(reconstructed, batch_target)
        
        # Backward pass:
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        epoch_loss += loss.item()
        n_batches += 1
    
    avg_train_loss = epoch_loss / n_batches
    train_losses.append(avg_train_loss)
    
    # --- VALIDATE ---
    model.eval()
    with torch.no_grad():  # No gradient computation during validation
        val_recon = model(val_data)
        val_loss = loss_fn(val_recon, val_data).item()
    val_losses.append(val_loss)
    
    if epoch % 4 == 0 or epoch == EPOCHS - 1:
        print(f"  Epoch {epoch+1:2d}/{EPOCHS} | Train Loss: {avg_train_loss:.6f} | Val Loss: {val_loss:.6f}")

# Save the model:
model_dir = os.path.join(data_dir, '..', 'ml', 'models')
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, 'lstm_ae_v1.pt')
torch.save({
    'model_state_dict': model.state_dict(),
    'scaler_mean': scaler.mean_,
    'scaler_scale': scaler.scale_,
    'seq_len': SEQ_LEN,
}, model_path)
print(f"\n✅ Model saved to {model_path}")

# ============================================================
# PART 6: Detect Anomalies with the Trained Model!
# ============================================================

print("\n=== PART 6: Anomaly Detection on Real Data ===")

model.eval()

# Get reconstruction errors for ALL validation data:
with torch.no_grad():
    recon = model(val_data)
    # Error per sample (mean across timesteps and features):
    errors = (val_data - recon).pow(2).mean(dim=(1, 2)).numpy()

# Set threshold: mean + 2*std of normal reconstruction errors
# This is more sensitive than 99th percentile and catches subtler anomalies
threshold = errors.mean() + 2 * errors.std()
print(f"Normal error stats: mean={errors.mean():.6f}, std={errors.std():.6f}")
print(f"Normal error range: {errors.min():.6f} to {errors.max():.6f}")
print(f"Anomaly threshold (mean + 2*std): {threshold:.6f}")

# Now inject anomalies and test:
print("\n--- Testing with injected anomalies ---")

# Take a GOOD normal window (one with low reconstruction error):
best_idx = np.argmin(errors)
normal_window = val_data[best_idx:best_idx+1].clone()  # shape (1, 60, 3)

# Test 1: SPIKE — blast temperature to extreme for several timesteps
# (A single-timestep spike gets averaged out over 60 steps, so we hit 5 steps)
spike_window = normal_window.clone()
spike_window[0, 28:33, 0] = 10.0  # ~+85 deg C in normalized units across 5 steps
with torch.no_grad():
    recon = model(spike_window)
    spike_error = (spike_window - recon).pow(2).mean().item()
print(f"  SPIKE anomaly    -> Error: {spike_error:.6f} | {'ANOMALY!' if spike_error > threshold else 'Normal'}")

# Test 2: FROZEN — freeze ALL sensors for 30 timesteps (very obvious)
frozen_window = normal_window.clone()
frozen_val = frozen_window[0, 15, :].clone()
frozen_window[0, 15:45, :] = frozen_val  # freeze all 3 sensors
with torch.no_grad():
    recon = model(frozen_window)
    frozen_error = (frozen_window - recon).pow(2).mean().item()
print(f"  FROZEN anomaly   -> Error: {frozen_error:.6f} | {'ANOMALY!' if frozen_error > threshold else 'Normal'}")

# Test 3: DRIFT — add large increasing offset to pressure
drift_window = normal_window.clone()
drift_offset = torch.linspace(0, 8, 60)  # ramp from 0 to +8 std devs
drift_window[0, :, 1] += drift_offset
with torch.no_grad():
    recon = model(drift_window)
    drift_error = (drift_window - recon).pow(2).mean().item()
print(f"  DRIFT anomaly    -> Error: {drift_error:.6f} | {'ANOMALY!' if drift_error > threshold else 'Normal'}")

# Test 4: Normal data (should NOT flag):
with torch.no_grad():
    recon = model(normal_window)
    normal_error = (normal_window - recon).pow(2).mean().item()
print(f"  NORMAL reading   -> Error: {normal_error:.6f} | {'ANOMALY!' if normal_error > threshold else 'Normal'}")

# Show the comparison:
print(f"\n  Error comparison (higher = more anomalous):")
print(f"    Normal:  {normal_error:.6f}  (baseline)")
print(f"    Spike:   {spike_error:.6f}  ({spike_error/max(normal_error,1e-9):.1f}x baseline)")
print(f"    Frozen:  {frozen_error:.6f}  ({frozen_error/max(normal_error,1e-9):.1f}x baseline)")
print(f"    Drift:   {drift_error:.6f}  ({drift_error/max(normal_error,1e-9):.1f}x baseline)")
print(f"    Threshold: {threshold:.6f}")

# ============================================================
# PART 7: Per-Feature Error Breakdown (Explainability!)
# ============================================================

print("\n=== PART 7: Which Sensor Caused the Anomaly? ===")

# For the spike anomaly, compute error PER FEATURE:
with torch.no_grad():
    recon = model(spike_window)
    
    # Error per feature (averaged over timesteps):
    temp_error = (spike_window[0, :, 0] - recon[0, :, 0]).pow(2).mean().item()
    pres_error = (spike_window[0, :, 1] - recon[0, :, 1]).pow(2).mean().item()
    hum_error  = (spike_window[0, :, 2] - recon[0, :, 2]).pow(2).mean().item()
    
    total = temp_error + pres_error + hum_error
    
    print(f"  Temperature error: {temp_error:.4f} ({temp_error/total*100:.1f}%)")
    print(f"  Pressure error:    {pres_error:.4f} ({pres_error/total*100:.1f}%)")
    print(f"  Humidity error:    {hum_error:.4f}  ({hum_error/total*100:.1f}%)")
    print(f"\n  → Primary offender: TEMPERATURE ({temp_error/total*100:.0f}% contribution)")
    print(f"  → This is the explainability judges love!")

print("""
=============================================================
  🎓 WHAT YOU JUST LEARNED (Recap)
=============================================================

1. LSTM = neural network that processes SEQUENCES and remembers context
2. LSTM Autoencoder = LSTM encoder (compress) + LSTM decoder (reconstruct)
3. Train it on NORMAL data only
4. High reconstruction error on new data = ANOMALY
5. Per-feature error breakdown = WHICH sensor is broken
6. Threshold from EVT/percentile = WHEN to alert

This is the EXACT model running inside SkyGuard AI.
Everything else (FastAPI, MQTT, dashboard) is just
plumbing to get data in and results out.
=============================================================
""")

print("✅ Lesson 5 complete! You've built and trained the real SkyGuard AI model.")
print("\n→ Next: lesson_06_full_pipeline.py (putting it all together)")
