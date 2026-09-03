import React from 'react';
import type { NetworkOverview } from '../types';
import { 
  Presentation, 
  Shield, 
  Cpu, 
  MapPin, 
  Zap, 
  CheckCircle2, 
  Layers, 
  X,
  Play
} from 'lucide-react';

interface PresentationModeProps {
  networkData: NetworkOverview | null;
  onClose: () => void;
  onNavigateToFaultLab: () => void;
}

export const PresentationMode: React.FC<PresentationModeProps> = ({
  networkData,
  onClose,
  onNavigateToFaultLab
}) => {
  const healthyCount = networkData?.healthy || 33;
  const totalCount = networkData?.total_stations || 35;
  const warnings = networkData?.warning || 2;
  const critical = networkData?.critical || 0;

  return (
    <div className="fixed inset-0 bg-[#070A10] z-50 flex flex-col overflow-y-auto select-none p-6 md:p-10 space-y-8">
      {/* ── TOP PRESENTATION HEADER ── */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wider text-slate-100 uppercase">SKYGUARD AI</h1>
            <p className="text-xs text-slate-400 font-mono">
              Smart India Hackathon (SIH26073) · Ministry of Earth Sciences / IMD
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onNavigateToFaultLab}
            className="px-4 py-2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-mono font-bold hover:bg-emerald-500/30 transition flex items-center gap-2"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Launch Live Fault Lab Demo →</span>
          </button>

          <button
            onClick={onClose}
            className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* ── CORE VALUE NARRATIVE BANNER ── */}
      <div className="p-6 rounded-lg bg-[#0F172A] border border-slate-800 space-y-3">
        <span className="text-xs font-mono text-emerald-400 font-bold uppercase tracking-wider">
          PROBLEM STATEMENT & SOLUTION ARCHITECTURE
        </span>
        <h2 className="text-2xl font-bold text-slate-100 font-sans">
          Intelligent Real-Time Anomaly Detection & Sensor Reliability for Automatic Weather Stations
        </h2>
        <p className="text-sm text-slate-300 leading-relaxed font-sans">
          SkyGuard AI combines deterministic thermodynamic rules (Magnus Dew Point), spatial barometric sea-level consensus ($800\text{km}$ Haversine), and a <strong className="text-emerald-300 font-semibold">Dual-ML Ensemble (PyTorch LSTM Autoencoder + Scikit-Learn Isolation Forest)</strong> to distinguish between physical transducer electrical failures and genuine atmospheric storm fronts with $&lt;12\text{ms}$ inference latency.
        </p>
      </div>

      {/* ── 4 KEY DEFENSE PILLARS ── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800 space-y-2 font-mono">
          <div className="text-emerald-400 font-bold text-xs uppercase">Layer 1: Rules</div>
          <div className="text-base font-bold text-slate-100 font-sans">Altitude Bounds & Jumps</div>
          <p className="text-xs text-slate-400">WMO-compliant range limits, flatlines (std &lt; 0.01), and &gt;6°C/hr rate jumps.</p>
        </div>

        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800 space-y-2 font-mono">
          <div className="text-emerald-400 font-bold text-xs uppercase">Layer 2: Dual ML</div>
          <div className="text-base font-bold text-slate-100 font-sans">LSTM AE + Isolation Forest</div>
          <p className="text-xs text-slate-400">57,196-param temporal waveform reconstruction + 200-tree statistical isolation.</p>
        </div>

        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800 space-y-2 font-mono">
          <div className="text-emerald-400 font-bold text-xs uppercase">Layer 3: Physics</div>
          <div className="text-base font-bold text-slate-100 font-sans">Thermodynamic Laws</div>
          <p className="text-xs text-slate-400">Magnus Dew Point ($T_d \le T_a$) and convective storm signature ($T\downarrow, P\uparrow, RH\uparrow$).</p>
        </div>

        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800 space-y-2 font-mono">
          <div className="text-emerald-400 font-bold text-xs uppercase">Layer 4: Spatial</div>
          <div className="text-base font-bold text-slate-100 font-sans">800km Sea-Level Reduction</div>
          <p className="text-xs text-slate-400">Laplace pressure reduction removes elevation bias for Leh, Shimla, and hills.</p>
        </div>
      </div>

      {/* ── STATS STRIP ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center font-mono">
        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="text-3xl font-bold text-slate-100">{totalCount}</div>
          <div className="text-xs text-slate-400 mt-1 uppercase">Pan-India AWS Stations</div>
        </div>
        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="text-3xl font-bold text-emerald-400">&lt; 12 ms</div>
          <div className="text-xs text-slate-400 mt-1 uppercase">Detection Latency</div>
        </div>
        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="text-3xl font-bold text-emerald-400">₹ 582</div>
          <div className="text-xs text-slate-400 mt-1 uppercase">ESP32 Hardware BOM Cost</div>
        </div>
        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="text-3xl font-bold text-sky-400">99.98 %</div>
          <div className="text-xs text-slate-400 mt-1 uppercase">Station Availability SLA</div>
        </div>
      </div>
    </div>
  );
};
