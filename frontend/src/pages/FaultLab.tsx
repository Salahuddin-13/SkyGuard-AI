import React, { useState } from 'react';
import type { NetworkOverview } from '../types';
import { apiService } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { 
  FlaskConical, 
  Play, 
  RotateCcw, 
  Zap, 
  Snowflake, 
  TrendingUp, 
  RadioTower, 
  CheckCircle2, 
  AlertTriangle, 
  Layers,
  Sparkles,
  ChevronDown
} from 'lucide-react';

interface FaultLabProps {
  networkData: NetworkOverview | null;
  onRefresh: () => void;
}

export const FaultLab: React.FC<FaultLabProps> = ({ networkData, onRefresh }) => {
  const [targetStation, setTargetStation] = useState<string>('Delhi (Safdarjung)');
  const [isInjecting, setIsInjecting] = useState(false);
  const [demoStep, setDemoStep] = useState<number>(0);
  const [demoStatus, setDemoStatus] = useState<string>('');

  if (!networkData) {
    return <div className="p-8 text-slate-500 font-mono animate-pulse">Loading Fault Lab...</div>;
  }

  const station = networkData.stations[targetStation] || Object.values(networkData.stations)[0];

  const handleInject = async (faultType: string) => {
    try {
      setIsInjecting(true);
      await apiService.injectFault(targetStation, faultType);
      onRefresh();
    } catch (e) {
      console.error('Inject error:', e);
    } finally {
      setIsInjecting(false);
    }
  };

  const handleClear = async (all = false) => {
    try {
      setIsInjecting(true);
      await apiService.clearFault(all ? undefined : targetStation);
      onRefresh();
    } catch (e) {
      console.error('Clear error:', e);
    } finally {
      setIsInjecting(false);
    }
  };

  const handleRunDemo = async () => {
    setDemoStep(1);
    setDemoStatus('Step 1/4: Ingesting nominal IMD baseline on Delhi Safdarjung...');
    setTargetStation('Delhi (Safdarjung)');
    await apiService.clearFault();
    onRefresh();

    setTimeout(async () => {
      setDemoStep(2);
      setDemoStatus('Step 2/4: Injecting +25°C thermal spike anomaly into live telemetry stream...');
      await apiService.injectFault('Delhi (Safdarjung)', 'spike');
      onRefresh();

      setTimeout(async () => {
        setDemoStep(3);
        setDemoStatus('Step 3/4: Dual ML models (LSTM + Isolation Forest) isolating temporal phase shift & rate jump...');
        onRefresh();

        setTimeout(async () => {
          setDemoStep(4);
          setDemoStatus('Step 4/4: Demonstration complete. Restoring nominal baseline...');
          await apiService.clearFault();
          onRefresh();
          setTimeout(() => {
            setDemoStep(0);
            setDemoStatus('');
          }, 3000);
        }, 5000);
      }, 4000);
    }, 3000);
  };

  const scenarios = [
    {
      id: 'spike',
      title: 'Sensor Thermal Spike',
      delta: '+25.0 °C Jump',
      icon: Zap,
      color: 'text-amber-400',
      borderColor: 'hover:border-amber-500/50',
      description: 'Simulates instantaneous ADC voltage spike or electrical noise on temperature transducer.',
      expectedLayers: ['Layer 1 Rate (>6°C/hr)', 'Layer 2 LSTM Autoencoder', 'Layer 2 Isolation Forest']
    },
    {
      id: 'freeze',
      title: 'Transducer Frozen Flatline',
      delta: 'Zero Variance (0.0)',
      icon: Snowflake,
      color: 'text-sky-400',
      borderColor: 'hover:border-sky-500/50',
      description: 'Simulates transducer firmware hang or I2C bus freeze returning repeated identical bits.',
      expectedLayers: ['Layer 1 Flatline Check (std < 0.01)', 'Layer 2 Temporal Anomaly']
    },
    {
      id: 'drift',
      title: 'Insidious Moisture Drift',
      delta: '+35.0% Humidity Drift',
      icon: TrendingUp,
      color: 'text-purple-400',
      borderColor: 'hover:border-purple-500/50',
      description: 'Simulates gradual polymer degradation in DHT22 capacitive element drifting over hours.',
      expectedLayers: ['Layer 2 Isolation Forest', 'Layer 3 Magnus Dew Point (Td > Ta breach)']
    },
    {
      id: 'dropout',
      title: 'Telemetry Packet Dropout',
      delta: 'Null / NaN Readings',
      icon: RadioTower,
      color: 'text-rose-400',
      borderColor: 'hover:border-rose-500/50',
      description: 'Simulates missing packets from wireless transmitter timeout or telemetry queue corruption.',
      expectedLayers: ['Layer 1 Completeness Rule', 'Quality Score Degradation']
    }
  ];

  const allStations = Object.keys(networkData.stations);

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── HEADER WITH 1-CLICK DEMO ── */}
      <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">Fault Injection & Verification Lab</h2>
            <p className="text-xs text-slate-400 font-mono">Test and evaluate the 4-layer anomaly detection pipeline in real time</p>
          </div>
        </div>

        {/* 1-Click SIH Live Demo Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunDemo}
            disabled={demoStep > 0}
            className={`px-4 py-2 rounded text-xs font-bold font-mono transition flex items-center gap-2 ${
              demoStep > 0
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse'
                : 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/40 shadow-lg shadow-emerald-950/40'
            }`}
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{demoStep > 0 ? `DEMO RUNNING (${demoStep}/4)` : '▶ Run 1-Click SIH Live Demo'}</span>
          </button>

          <button
            onClick={() => handleClear(true)}
            disabled={isInjecting}
            className="px-3 py-2 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 text-xs font-mono transition flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear All</span>
          </button>
        </div>
      </div>

      {/* Demo Status Banner if running */}
      {demoStep > 0 && (
        <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs font-mono flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span>{demoStatus}</span>
        </div>
      )}

      {/* ── TARGET STATION TELEMETRY STRIP ── */}
      <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 font-mono">TARGET STATION:</span>
            <div className="relative">
              <select
                value={targetStation}
                onChange={(e) => setTargetStation(e.target.value)}
                className="px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono appearance-none pr-8 cursor-pointer focus:outline-none focus:border-slate-600"
              >
                {allStations.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <StatusBadge status={station.status} />
            {station.active_fault && (
              <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                ACTIVE FAULT: {station.active_fault.toUpperCase()}
              </span>
            )}
          </div>
        </div>

        {/* Live Observation Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
            <div className="text-[10px] text-slate-500 uppercase">Observed Temperature</div>
            <div className="text-lg font-bold text-slate-100">{station.temperature?.toFixed(1)} °C</div>
          </div>
          <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
            <div className="text-[10px] text-slate-500 uppercase">Surface Pressure</div>
            <div className="text-lg font-bold text-slate-100">{station.pressure?.toFixed(1)} hPa</div>
          </div>
          <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
            <div className="text-[10px] text-slate-500 uppercase">Relative Humidity</div>
            <div className="text-lg font-bold text-slate-100">{station.humidity?.toFixed(0)} %</div>
          </div>
          <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
            <div className="text-[10px] text-slate-500 uppercase">Risk Index Score</div>
            <div className={`text-lg font-bold ${
              (station.risk?.score || 0) > 40 ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {station.risk?.score || 0} / 100
            </div>
          </div>
        </div>
      </div>

      {/* ── 4 FAULT SCENARIO TILES ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isActive = station.active_fault === sc.id;

          return (
            <div
              key={sc.id}
              className={`p-4 rounded-lg bg-[#0F172A] border transition flex flex-col justify-between space-y-4 ${
                isActive ? 'border-amber-500 bg-amber-950/20 shadow-lg' : `border-slate-800/90 ${sc.borderColor}`
              }`}
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className={`w-8 h-8 rounded bg-slate-900 border border-slate-800 flex items-center justify-center ${sc.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-900 text-slate-300 border border-slate-800">
                    {sc.delta}
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-100 font-sans">{sc.title}</h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{sc.description}</p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 space-y-1">
                  <div className="text-[10px] text-slate-500 font-mono uppercase">Expected Layer Triggers:</div>
                  <div className="space-y-0.5">
                    {sc.expectedLayers.map((l, i) => (
                      <div key={i} className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-slate-600" />
                        <span>{l}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              {isActive ? (
                <button
                  onClick={() => handleClear(false)}
                  disabled={isInjecting}
                  className="w-full py-2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold font-mono hover:bg-amber-500/30 transition flex items-center justify-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Clear Active Fault</span>
                </button>
              ) : (
                <button
                  onClick={() => handleInject(sc.id)}
                  disabled={isInjecting}
                  className="w-full py-2 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 text-xs font-semibold font-mono transition"
                >
                  Inject Scenario →
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* ── VERDICT & ROOT CAUSE EXPLANATION ── */}
      {station.active_fault && (
        <div className="p-4 rounded-lg bg-[#0F172A] border border-amber-500/40 space-y-3">
          <div className="flex items-center gap-2 text-amber-300 font-bold text-sm font-sans uppercase">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Real-Time Anomaly Verdict & Root Cause Explanation</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">Detection Summary</div>
              <div className="text-slate-200 font-bold mt-1">
                {station.detection?.alerts?.length || 0} Alert(s) Generated
              </div>
              <p className="text-slate-400 text-[11px] mt-1">{station.explanation?.primary_reason || 'Anomaly detected across physical rules and ML models.'}</p>
            </div>

            <div className="p-3 rounded bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">Risk Assessment</div>
              <div className="text-rose-400 font-bold mt-1">
                Score: {station.risk?.score || 0} / 100 ({station.risk?.level || 'ELEVATED'})
              </div>
              <p className="text-slate-400 text-[11px] mt-1">{station.explanation?.conclusion || 'Sensor flagged for operator investigation.'}</p>
            </div>

            <div className="p-3 rounded bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">Recommended Operator Action</div>
              <div className="text-emerald-400 font-bold mt-1">Automated Recommendation</div>
              <p className="text-slate-300 text-[11px] mt-1">{station.explanation?.recommended_action || 'Inspect physical transducer wiring and calibrate telemetry baseline.'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
