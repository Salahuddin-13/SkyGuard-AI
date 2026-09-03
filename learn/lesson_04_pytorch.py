"""
=============================================================
  LESSON 4: PyTorch — Building Neural Networks from Scratch
=============================================================

This is THE lesson. After this, you understand how ML models
actually work — not as a black box, but mechanically.

Three key ideas:
  1. TENSORS = arrays that track math operations
  2. FORWARD PASS = data flows through the network
  3. BACKPROPAGATION = network learns from its errors

RUN THIS:  python lesson_04_pytorch.py
=============================================================
"""

import torch
import torch.nn as nn
import numpy as np

# ============================================================
# PART 1: Tensors — Like NumPy arrays, but smarter
# ============================================================

print("=== PART 1: Tensors ===")

# A tensor is just an array that remembers what math you did to it.
# This lets PyTorch compute gradients (how to improve the model).

# Create from a list:
t = torch.tensor([1.0, 2.0, 3.0])
print(f"Tensor: {t}")
print(f"Shape:  {t.shape}")
print(f"Type:   {t.dtype}")

# From a NumPy array:
np_arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
t2 = torch.from_numpy(np_arr)
print(f"\n2D Tensor from NumPy:\n{t2}")
print(f"Shape: {t2.shape}")  # (2, 3)

# Tensor math (same as NumPy):
a = torch.tensor([1.0, 2.0, 3.0])
b = torch.tensor([4.0, 5.0, 6.0])
print(f"\na + b = {a + b}")
print(f"a * b = {a * b}")
print(f"Mean:  {a.mean()}")

# ============================================================
# PART 2: What is a Neural Network? (From scratch!)
# ============================================================

print("\n=== PART 2: Neural Network = Matrix Multiplications ===")

# A neural network is literally just:
#   output = activation(input × weights + bias)
#
# That's it. Seriously. The "magic" is in finding the right weights.

# Let's build one BY HAND:

# Fake input: 3 sensor readings [temp, pressure, humidity] (normalized)
input_data = torch.tensor([0.5, -0.3, 0.8])  # 3 features

# Layer 1: 3 inputs → 4 hidden neurons
# Weights: 4×3 matrix (4 neurons, each connected to 3 inputs)
W1 = torch.randn(4, 3)   # Random starting weights
b1 = torch.zeros(4)       # Biases start at 0

# Forward pass through layer 1:
hidden = input_data @ W1.T + b1   # @ = matrix multiply, .T = transpose
print(f"Raw hidden layer: {hidden}")

# Activation function (ReLU = keep positive values, zero out negatives):
hidden = torch.relu(hidden)
print(f"After ReLU:       {hidden}")

# Layer 2: 4 hidden → 1 output (anomaly score)
W2 = torch.randn(1, 4)
b2 = torch.zeros(1)

output = hidden @ W2.T + b2
print(f"Output (anomaly score): {output.item():.4f}")

print("\nThat's a 2-layer neural network! Just matrix multiplications + ReLU.")
print("Problem: the weights are RANDOM, so the output is meaningless.")
print("Next: how do we find GOOD weights? → Training!")

# ============================================================
# PART 3: nn.Module — PyTorch's Clean Way to Build Networks
# ============================================================

print("\n=== PART 3: nn.Module ===")

# Instead of manual matrix math, PyTorch gives us nn.Module:

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        # Define layers:
        self.layer1 = nn.Linear(3, 4)    # 3 inputs → 4 hidden
        self.layer2 = nn.Linear(4, 1)    # 4 hidden → 1 output
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # Define how data flows through the network:
        x = self.layer1(x)     # Linear transform
        x = self.relu(x)       # Activation
        x = self.layer2(x)     # Output
        return x

model = SimpleNet()
print(model)

# Count parameters:
total_params = sum(p.numel() for p in model.parameters())
print(f"Total trainable parameters: {total_params}")
# 3*4 + 4 (layer1 weights + biases) + 4*1 + 1 (layer2) = 21

# Forward pass:
output = model(input_data)
print(f"Output: {output.item():.4f}")

# ============================================================
# PART 4: Loss Functions — Measuring How Wrong the Model Is
# ============================================================

print("\n=== PART 4: Loss Functions ===")

# A "loss function" computes how far off the model's prediction is
# from the true answer. Lower loss = better model.

# For SkyGuard's autoencoder, we use MSE (Mean Squared Error):
# MSE = mean((actual - predicted)²)

prediction = torch.tensor([32.4, 1008.0, 68.5])
actual      = torch.tensor([32.6, 1008.2, 68.3])

mse = nn.MSELoss()
loss = mse(prediction, actual)
print(f"Prediction: {prediction}")
print(f"Actual:     {actual}")
print(f"MSE Loss:   {loss.item():.6f}")

# Small loss = prediction is close to actual = GOOD
# Big loss = prediction is way off = BAD (or: anomaly!)

# ============================================================
# PART 5: TRAINING — How the Model Learns
# ============================================================

print("\n=== PART 5: Training Loop (THE core concept) ===")

# Training is this loop:
#   1. Feed data through the model (FORWARD PASS)
#   2. Compute the loss (how wrong is it?)
#   3. Compute gradients (BACKPROPAGATION — which weights to change?)
#   4. Update weights (OPTIMIZER step)
#   5. Repeat thousands of times

# Let's train a tiny model to learn the function: y = 2*x + 1

# Generate training data:
X_train = torch.linspace(-5, 5, 100).unsqueeze(1)  # 100 points, shape (100, 1)
y_train = 2 * X_train + 1 + torch.randn_like(X_train) * 0.3  # Add noise

# Simple model: 1 input → 1 output (just a line: y = w*x + b)
model = nn.Linear(1, 1)

# Optimizer: HOW we update weights (Adam is the go-to)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)  # lr = learning rate
loss_fn = nn.MSELoss()

# Training loop:
print("Training...")
for epoch in range(200):
    # 1. Forward pass
    predictions = model(X_train)
    
    # 2. Compute loss
    loss = loss_fn(predictions, y_train)
    
    # 3. Backpropagation (compute gradients)
    optimizer.zero_grad()   # Clear old gradients
    loss.backward()         # Compute new gradients
    
    # 4. Update weights
    optimizer.step()
    
    if epoch % 40 == 0:
        w = model.weight.item()
        b = model.bias.item()
        print(f"  Epoch {epoch:3d} | Loss: {loss.item():.4f} | "
              f"Learned: y = {w:.2f}*x + {b:.2f}")

# Check final result:
w = model.weight.item()
b = model.bias.item()
print(f"\n🎯 Final model: y = {w:.2f}*x + {b:.2f}")
print(f"   True function: y = 2.00*x + 1.00")
print(f"   Pretty close!")

# ============================================================
# PART 6: What is an AUTOENCODER?
# ============================================================

print("\n=== PART 6: Autoencoders — The Key to SkyGuard ===")

print("""
An AUTOENCODER is a network that learns to COPY its input.

Wait, why is that useful? Because we force it through a BOTTLENECK:

  Input (3 values)  →  Encoder  →  Bottleneck (2 values)  →  Decoder  →  Output (3 values)
  [32.4, 1008, 68]  →  compress →  [x, y]  →  decompress →  [32.3, 1008.1, 68.2]

Key insight:
  - The bottleneck is SMALLER than the input
  - So the model must learn to COMPRESS the data efficiently
  - It can only do this by learning the PATTERNS in the data
  
For anomaly detection:
  - Train on NORMAL weather data only
  - The model learns: "normal weather looks like THIS pattern"
  - When you feed it ABNORMAL data (sensor glitch), it CAN'T 
    reconstruct it well → reconstruction error is HIGH → ANOMALY!
""")

# Build a simple autoencoder:
class SimpleAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        # Encoder: 3 → 8 → 2 (compress)
        self.encoder = nn.Sequential(
            nn.Linear(3, 8),
            nn.ReLU(),
            nn.Linear(8, 2),    # Bottleneck!
        )
        # Decoder: 2 → 8 → 3 (decompress)
        self.decoder = nn.Sequential(
            nn.Linear(2, 8),
            nn.ReLU(),
            nn.Linear(8, 3),    # Back to original size
        )
    
    def forward(self, x):
        encoded = self.encoder(x)     # Compress
        decoded = self.decoder(encoded)  # Reconstruct
        return decoded

ae = SimpleAutoencoder()
print(f"Autoencoder architecture:\n{ae}")

# Test with a normal reading:
normal = torch.tensor([0.5, -0.3, 0.8])   # normalized sensor values
reconstructed = ae(normal)
error = (normal - reconstructed).pow(2).mean()  # MSE
print(f"\nNormal reading:      {normal.tolist()}")
print(f"Reconstructed:       {[f'{x:.3f}' for x in reconstructed.tolist()]}")
print(f"Reconstruction error: {error.item():.4f}")
print("(Error is random now because the model is untrained)")

# ============================================================
# PART 7: Training the Autoencoder on "Normal" Data
# ============================================================

print("\n=== PART 7: Training the Autoencoder ===")

# Generate fake "normal" weather data:
# Normal: temp ~30±3, pressure ~1010±5, humidity ~65±10
np.random.seed(42)
n_samples = 1000
normal_data = np.column_stack([
    30 + 3 * np.random.randn(n_samples),       # temperature
    1010 + 5 * np.random.randn(n_samples),      # pressure  
    65 + 10 * np.random.randn(n_samples),       # humidity
]).astype(np.float32)

# Normalize:
data_mean = normal_data.mean(axis=0)
data_std  = normal_data.std(axis=0)
normal_normalized = (normal_data - data_mean) / data_std

train_tensor = torch.from_numpy(normal_normalized)

# Train the autoencoder:
ae = SimpleAutoencoder()
optimizer = torch.optim.Adam(ae.parameters(), lr=0.005)
loss_fn = nn.MSELoss()

print("Training autoencoder on normal data...")
for epoch in range(300):
    reconstructed = ae(train_tensor)
    loss = loss_fn(reconstructed, train_tensor)  # target = input!
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if epoch % 60 == 0:
        print(f"  Epoch {epoch:3d} | Reconstruction Loss: {loss.item():.6f}")

# ============================================================
# PART 8: DETECTING ANOMALIES with the trained autoencoder
# ============================================================

print("\n=== PART 8: Anomaly Detection! ===")

# Test on normal data:
normal_test = torch.tensor([[0.1, -0.2, 0.3]])  # normal reading
recon = ae(normal_test)
normal_error = (normal_test - recon).pow(2).mean().item()
print(f"Normal reading  → Error: {normal_error:.6f} ✅")

# Test on a SPIKE anomaly (temp = 55°C → normalized ≈ 8.3):
spike = torch.tensor([[8.0, -0.2, 0.3]])  # temp way too high!
recon = ae(spike)
spike_error = (spike - recon).pow(2).mean().item()
print(f"Spike anomaly   → Error: {spike_error:.6f} 🔴")

# Test on a WEIRD combination (high temp + high humidity = unusual):
weird = torch.tensor([[3.0, -0.2, 3.0]])
recon = ae(weird)
weird_error = (weird - recon).pow(2).mean().item()
print(f"Weird combo     → Error: {weird_error:.6f} ⚠️")

print(f"\nAnomaly detection works! Errors:")
print(f"  Normal:  {normal_error:.6f}")
print(f"  Spike:   {spike_error:.6f} ({spike_error/normal_error:.0f}x higher!)")
print(f"  Weird:   {weird_error:.6f} ({weird_error/normal_error:.0f}x higher!)")
print(f"\nThe autoencoder learned what 'normal' looks like.")
print(f"Anything that doesn't fit → high reconstruction error → ANOMALY!")

print("\n✅ Lesson 4 complete!")
print("You now understand: tensors, neural networks, loss functions,")
print("training loops, autoencoders, and anomaly detection via reconstruction error.")
print("\nThis is the CORE of SkyGuard AI. Everything else is engineering.")
print("\n→ Next: lesson_05_lstm_autoencoder.py (the real model with time-series)")
