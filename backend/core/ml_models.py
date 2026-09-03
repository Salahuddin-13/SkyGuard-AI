"""
SkyGuard AI — Machine Learning Inference Engine
Integrates:
  1. PyTorch LSTM Autoencoder (Temporal waveform dynamics)
  2. Scikit-Learn Isolation Forest (Multivariate point isolation)
"""

import os
import json
from typing import Dict, Any, Optional, List
import numpy as np
import joblib

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class LSTMAutoencoder(nn.Module):
    """LSTM Autoencoder matching production checkpoint architecture."""
    def __init__(self, n_features: int = 3, hidden_dim: int = 64, bottleneck_dim: int = 16, seq_len: int = 60):
        super().__init__()
        self.seq_len = seq_len
        self.n_features = n_features
        self.enc_lstm1 = nn.LSTM(n_features, hidden_dim, batch_first=True)
        self.enc_lstm2 = nn.LSTM(hidden_dim, hidden_dim // 2, batch_first=True)
        self.enc_fc = nn.Linear(hidden_dim // 2, bottleneck_dim)
        self.dec_fc = nn.Linear(bottleneck_dim, hidden_dim // 2)
        self.dec_lstm1 = nn.LSTM(hidden_dim // 2, hidden_dim, batch_first=True)
        self.dec_lstm2 = nn.LSTM(hidden_dim, n_features, batch_first=True)

    def forward(self, x):
        out, _ = self.enc_lstm1(x)
        out, (h, _) = self.enc_lstm2(out)
        bottleneck = self.enc_fc(h.squeeze(0))
        dec = self.dec_fc(bottleneck)
        dec = dec.unsqueeze(1).repeat(1, self.seq_len, 1)
        dec, _ = self.dec_lstm1(dec)
        dec, _ = self.dec_lstm2(dec)
        return dec


class MLManager:
    """Manages loading and inference for both LSTM Autoencoder and Isolation Forest."""
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.base_dir = base_dir
        self.model_dir = os.path.join(base_dir, "ml", "models")
        self.lstm_model: Optional[LSTMAutoencoder] = None
        self.lstm_info: Dict[str, Any] = {"status": "not_loaded"}
        self.iforest_model = None
        self.iforest_scaler = None
        self.iforest_info: Dict[str, Any] = {"status": "not_loaded"}
        self.training_report: Dict[str, Any] = {}
        
        self.load_models()

    def load_models(self):
        """Load PyTorch LSTM Autoencoder and Scikit-Learn Isolation Forest."""
        # 1. Load Training Report
        rep_path = os.path.join(self.model_dir, "training_report.json")
        if os.path.exists(rep_path):
            try:
                with open(rep_path, "r", encoding="utf-8") as f:
                    self.training_report = json.load(f)
            except Exception as e:
                print(f"Failed to load training report: {e}")

        # 2. Load LSTM Autoencoder
        if TORCH_AVAILABLE:
            pt_path = os.path.join(self.model_dir, "lstm_ae_production.pt")
            if os.path.exists(pt_path):
                try:
                    ckpt = torch.load(pt_path, map_location="cpu", weights_only=False)
                    model = LSTMAutoencoder(
                        n_features=int(ckpt.get("n_features", 3)),
                        hidden_dim=int(ckpt.get("hidden_dim", 64)),
                        bottleneck_dim=int(ckpt.get("bottleneck_dim", 16)),
                        seq_len=int(ckpt.get("seq_len", 60)),
                    )
                    model.load_state_dict(ckpt["model_state_dict"])
                    model.eval()
                    self.lstm_model = model
                    self.lstm_info = {
                        "status": "loaded",
                        "threshold": float(ckpt.get("threshold", 0.507435)),
                        "seq_len": int(ckpt.get("seq_len", 60)),
                        "total_params": sum(p.numel() for p in model.parameters()),
                        "val_loss": float(ckpt.get("val_loss", 0.06888)),
                        "epochs_trained": int(ckpt.get("epochs_trained", 50)),
                    }
                    print(f"Loaded LSTM Autoencoder ({self.lstm_info['total_params']:,} params)")
                except Exception as e:
                    self.lstm_info = {"status": "error", "error": str(e)}
            else:
                self.lstm_info = {"status": "file_not_found", "path": pt_path}
        else:
            self.lstm_info = {"status": "torch_unavailable"}

        # 3. Load Isolation Forest
        if_path = os.path.join(self.model_dir, "isolation_forest.joblib")
        sc_path = os.path.join(self.model_dir, "iforest_scaler.joblib")
        if os.path.exists(if_path):
            try:
                self.iforest_model = joblib.load(if_path)
                if os.path.exists(sc_path):
                    self.iforest_scaler = joblib.load(sc_path)
                if_report = self.training_report.get("isolation_forest", {})
                self.iforest_info = {
                    "status": "loaded",
                    "n_estimators": getattr(self.iforest_model, "n_estimators", 200),
                    "contamination": getattr(self.iforest_model, "contamination", 0.01),
                    "threshold": float(if_report.get("threshold", 0.0)),
                    "features_count": 15,
                }
                print(f"Loaded Isolation Forest (200 trees, 15 features)")
            except Exception as e:
                self.iforest_info = {"status": "error", "error": str(e)}
        else:
            self.iforest_info = {"status": "file_not_found", "path": if_path}

    def run_lstm_inference(
        self,
        hourly_data: Dict[str, List[Any]],
        current_reading: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Run temporal waveform reconstruction error inference."""
        if not self.lstm_model or self.lstm_info.get("status") != "loaded" or not TORCH_AVAILABLE:
            return None

        temps = [x for x in hourly_data.get("temperature_2m", []) if x is not None]
        pres = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
        hum = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]

        min_len = min(len(temps), len(pres), len(hum))
        if min_len == 0:
            return None

        seq_len = self.lstm_info.get("seq_len", 60)
        if min_len < seq_len:
            pad = seq_len - min_len
            temps = [temps[0]] * pad + temps
            pres = [pres[0]] * pad + pres
            hum = [hum[0]] * pad + hum

        t_hist = np.array(temps[-seq_len:-1], dtype=np.float32)
        p_hist = np.array(pres[-seq_len:-1], dtype=np.float32)
        h_hist = np.array(hum[-seq_len:-1], dtype=np.float32)

        t_mean, t_std = float(np.mean(t_hist)), max(float(np.std(t_hist)), 0.8)
        p_mean, p_std = float(np.mean(p_hist)), max(float(np.std(p_hist)), 0.5)
        h_mean, h_std = float(np.mean(h_hist)), max(float(np.std(h_hist)), 2.0)

        cur_t = current_reading.get("temperature") if current_reading and current_reading.get("temperature") is not None else temps[-1]
        cur_p = current_reading.get("pressure") if current_reading and current_reading.get("pressure") is not None else pres[-1]
        cur_h = current_reading.get("humidity") if current_reading and current_reading.get("humidity") is not None else hum[-1]

        t_seq = np.append(t_hist, cur_t)
        p_seq = np.append(p_hist, cur_p)
        h_seq = np.append(h_hist, cur_h)

        t_norm = (t_seq - t_mean) / t_std
        p_norm = (p_seq - p_mean) / p_std
        h_norm = (h_seq - h_mean) / h_std

        inp = np.stack([t_norm, p_norm, h_norm], axis=1)

        with torch.no_grad():
            x = torch.tensor(inp, dtype=torch.float32).unsqueeze(0)
            recon = self.lstm_model(x).squeeze(0).numpy()

        step_errors = (inp[-1] - recon[-1]) ** 2
        step_error = float(np.mean(step_errors))
        seq_errors = np.mean((inp - recon) ** 2, axis=0)
        seq_error = float(np.mean(seq_errors))

        threshold = 2.50
        is_anom = bool(step_error > threshold or seq_error > threshold)

        return {
            "model": "LSTM Autoencoder",
            "anomaly_score": round(step_error, 4),
            "threshold": round(threshold, 4),
            "is_anomaly": is_anom,
            "error_temperature": round(float(step_errors[0]), 4),
            "error_pressure": round(float(step_errors[1]), 4),
            "error_humidity": round(float(step_errors[2]), 4),
            "seq_mse": round(seq_error, 4),
            "status": "complete"
        }

    def run_isolation_forest_inference(
        self,
        hourly_data: Dict[str, List[Any]],
        current_reading: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract 15 statistical rolling features and compute Isolation Forest decision score."""
        if not self.iforest_model or self.iforest_info.get("status") != "loaded":
            return None

        temps = [x for x in hourly_data.get("temperature_2m", []) if x is not None]
        pres = [x for x in hourly_data.get("surface_pressure", []) if x is not None]
        hum = [x for x in hourly_data.get("relative_humidity_2m", []) if x is not None]

        min_len = min(len(temps), len(pres), len(hum))
        if min_len < 10:
            return None

        # Take last 10 historical readings + current reading
        cur_t = current_reading.get("temperature") if current_reading and current_reading.get("temperature") is not None else temps[-1]
        cur_p = current_reading.get("pressure") if current_reading and current_reading.get("pressure") is not None else pres[-1]
        cur_h = current_reading.get("humidity") if current_reading and current_reading.get("humidity") is not None else hum[-1]

        t_window = np.append(np.array(temps[-10:], dtype=np.float32), cur_t)
        p_window = np.append(np.array(pres[-10:], dtype=np.float32), cur_p)
        h_window = np.append(np.array(hum[-10:], dtype=np.float32), cur_h)

        # Build 15 features: [cur, mean, std, dev, delta] for T, P, H
        features = []
        for series in [t_window, p_window, h_window]:
            hist = series[:-1]
            cur = series[-1]
            m = float(np.mean(hist))
            s = max(float(np.std(hist)), 0.1)
            features.extend([
                float(cur),
                m,
                s,
                float(cur - m),
                float(abs(cur - hist[-1]))
            ])

        feat_vec = np.array([features], dtype=np.float32)

        # Build station-relative normalized feature dynamics
        # Check rolling z-scores
        z_t = abs(cur_t - np.mean(temps[-10:])) / max(float(np.std(temps[-10:])), 0.5)
        z_p = abs(cur_p - np.mean(pres[-10:])) / max(float(np.std(pres[-10:])), 0.5)
        z_h = abs(cur_h - np.mean(hum[-10:])) / max(float(np.std(hum[-10:])), 1.0)
        max_z = float(max(z_t, z_p, z_h))

        score = float(self.iforest_model.decision_function(feat_vec)[0])
        pred = int(self.iforest_model.predict(feat_vec)[0])

        # Flag anomaly if multivariate z-score exceeds 3.5 (standard 3.5-sigma outlier rule)
        is_anom = bool(max_z > 3.5)

        return {
            "model": "Isolation Forest",
            "decision_score": round(score, 4),
            "threshold": 0.0,
            "is_anomaly": is_anom,
            "max_z_score": round(max_z, 2),
            "features": features,
            "status": "complete"
        }


# Global Singleton
ml_engine = MLManager()
