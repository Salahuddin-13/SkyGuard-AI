import React, { useState } from 'react';
import type { 
  NetworkOverview, 
  StationData 
} from '../types';
import { StatusBadge, SeverityBadge } from '../components/StatusBadge';
import { apiService } from '../services/api';
import { 
  Search, 
  ArrowUpRight, 
  AlertOctagon, 
  ShieldCheck, 
  Cpu, 
  Layers, 
  Radio,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  MapPin,
  Flame,
  Snowflake,
  Activity,
  CheckCircle2,
  RefreshCw,
  Zap
} from 'lucide-react';

interface CommandCenterProps {
  networkData: NetworkOverview | null;
  onSelectStation: (name: string) => void;
  onNavigateToFaultLab: () => void;
  onNavigateToMap: () => void;
  onNavigateToAlerts: () => void;
  onRefresh?: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  networkData,
  onSelectStation,
  onNavigateToFaultLab,
  onNavigateToMap,
  onNavigateToAlerts,
  onRefresh
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedZone, setSelectedZone] = useState('ALL');
  const [sortBy, setSortBy] = useState<'risk' | 'name' | 'temp'>('risk');
  const [simLoading, setSimLoading] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const stationsArray: StationData[] = Object.values(networkData?.stations || {});
  
  const totalStations = networkData?.total_stations || stationsArray.length || 35;
  const healthyCount = networkData?.healthy ?? stationsArray.filter(s => s.status === 'HEALTHY').length;
  const warningCount = networkData?.warning ?? stationsArray.filter(s => s.status === 'WARNING' || s.status === 'HIGH_RISK').length;
  const criticalCount = networkData?.critical ?? stationsArray.filter(s => s.status === 'CRITICAL').length;
  const activeAlerts = networkData?.alerts || [];
  const activeFaultsCount = networkData?.active_faults_count || 0;

  // Filter and sort stations
  const filteredStations = stationsArray.filter((st) => {
    const matchesSearch = st.station.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          st.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          st.state.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesZone = selectedZone === 'ALL' || st.zone === selectedZone;
    return matchesSearch && matchesZone;
  }).sort((a, b) => {
    if (sortBy === 'risk') return (b.risk?.score || 0) - (a.risk?.score || 0);
    if (sortBy === 'temp') return (b.temperature || 0) - (a.temperature || 0);
    return a.station.localeCompare(b.station);
  });

  // Zones metadata
  const zones = ['ALL', 'North', 'West', 'Central', 'East', 'South', 'North-East', 'Island'];

  // Quick simulation trigger
  const handleQuickFault = async (stationName: string, faultType: string) => {
    try {
      setSimLoading(true);
      await apiService.injectFault(stationName, faultType);
      setFeedbackMsg(`⚡ Injected ${faultType.toUpperCase()} fault into ${stationName}`);
      onRefresh?.();
      setTimeout(() => setFeedbackMsg(null), 4000);
    } catch (e) {
      console.error(e);
    } finally {
      setSimLoading(false);
    }
  };

  const handleClearFaults = async () => {
    try {
      setSimLoading(true);
      await apiService.clearFault();
      setFeedbackMsg(`✓ Restored nominal telemetry across all 35 stations`);
      onRefresh?.();
      setTimeout(() => setFeedbackMsg(null), 4000);
    } catch (e) {
      console.error(e);
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── TOP OPERATIONAL TICKER & FEEDBACK NOTIFICATION ── */}
      {feedbackMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center justify-between animate-fadeIn shadow-lg shadow-emerald-950/40">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="font-semibold">{feedbackMsg}</span>
          </div>
          <button 
            onClick={() => setFeedbackMsg(null)}
            className="text-emerald-400 hover:text-white px-2 py-0.5 rounded bg-emerald-900/50"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── TACTICAL FAULT INJECTION LAUNCHPAD ── */}
      <div className="p-3.5 rounded-lg bg-[#0F172A] border border-slate-800/90 flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          <span className="font-bold text-slate-200 uppercase tracking-wider">Quick Anomaly Testbench:</span>
          <span className="text-slate-400 hidden md:inline">Inject real-time faults in 1-click to test multi-layer detection</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            disabled={simLoading}
            onClick={() => handleQuickFault('Delhi (Safdarjung)', 'spike')}
            className="px-2.5 py-1.5 rounded bg-rose-950/40 border border-rose-800/50 text-rose-300 hover:bg-rose-900/50 text-xs font-mono font-semibold transition flex items-center gap-1.5"
          >
            <Flame className="w-3.5 h-3.5 text-rose-400" />
            <span>Spike (+25°C) Delhi</span>
          </button>

          <button
            disabled={simLoading}
            onClick={() => handleQuickFault('Leh Ladakh', 'freeze')}
            className="px-2.5 py-1.5 rounded bg-cyan-950/40 border border-cyan-800/50 text-cyan-300 hover:bg-cyan-900/50 text-xs font-mono font-semibold transition flex items-center gap-1.5"
          >
            <Snowflake className="w-3.5 h-3.5 text-cyan-400" />
            <span>Zero Freeze Leh</span>
          </button>

          <button
            disabled={simLoading}
            onClick={() => handleQuickFault('Mumbai (Colaba)', 'drift')}
            className="px-2.5 py-1.5 rounded bg-amber-950/40 border border-amber-800/50 text-amber-300 hover:bg-amber-900/50 text-xs font-mono font-semibold transition flex items-center gap-1.5"
          >
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            <span>Drift (+35% RH) Mumbai</span>
          </button>

          {activeFaultsCount > 0 && (
            <button
              disabled={simLoading}
              onClick={handleClearFaults}
              className="px-3 py-1.5 rounded bg-emerald-950/60 border border-emerald-700/60 text-emerald-300 hover:bg-emerald-900/70 text-xs font-mono font-bold transition flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5 text-emerald-400 animate-spin" />
              <span>Reset Nominal ({activeFaultsCount})</span>
            </button>
          )}
        </div>
      </div>

      {/* ── TOP KPI METRIC STRIP ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 font-mono">
        {/* Metric 1: Network Health */}
        <div className="p-3.5 rounded-lg bg-[#0F172A] border border-slate-800/90 relative overflow-hidden group">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Network Health</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100">
              {totalStations > 0 ? Math.round((healthyCount / totalStations) * 100) : 100}%
            </span>
            <span className="text-xs text-emerald-400 font-semibold">{healthyCount}/{totalStations} Nominal</span>
          </div>
          <div className="mt-2 w-full bg-slate-800 h-1 rounded-full overflow-hidden">
            <div 
              className="bg-emerald-500 h-full transition-all duration-500" 
              style={{ width: `${totalStations > 0 ? (healthyCount / totalStations) * 100 : 100}%` }}
            />
          </div>
        </div>

        {/* Metric 2: Monitored AWS Stations */}
        <div className="p-3.5 rounded-lg bg-[#0F172A] border border-slate-800/90">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Monitored AWS</span>
            <Radio className="w-4 h-4 text-sky-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100">{totalStations}</span>
            <span className="text-xs text-slate-400 font-semibold">Pan-India IMD</span>
          </div>
          <div className="mt-2 text-[10px] text-slate-500 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Open-Meteo Calibrated</span>
          </div>
        </div>

        {/* Metric 3: Active Warnings */}
        <div className="p-3.5 rounded-lg bg-[#0F172A] border border-slate-800/90">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Active Warnings</span>
            <AlertOctagon className={`w-4 h-4 ${warningCount > 0 ? 'text-amber-400 animate-pulse' : 'text-slate-500'}`} />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${warningCount > 0 ? 'text-amber-400' : 'text-slate-100'}`}>
              {warningCount}
            </span>
            <span className="text-xs text-slate-500">Tier 2 Triage</span>
          </div>
          <div className="mt-2 text-[10px] text-slate-500">
            {warningCount === 0 ? 'Zero active warnings' : 'Inspection advised'}
          </div>
        </div>

        {/* Metric 4: Critical Incidents */}
        <div className="p-3.5 rounded-lg bg-[#0F172A] border border-slate-800/90">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Critical Faults</span>
            <Flame className={`w-4 h-4 ${criticalCount > 0 ? 'text-rose-400 animate-pulse' : 'text-slate-500'}`} />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${criticalCount > 0 ? 'text-rose-400' : 'text-slate-100'}`}>
              {criticalCount}
            </span>
            <span className="text-xs text-slate-500">Immediate Action</span>
          </div>
          <div className="mt-2 text-[10px] text-slate-500">
            {criticalCount === 0 ? 'Zero critical errors' : 'Immediate dispatch'}
          </div>
        </div>

        {/* Metric 5: Inference Latency */}
        <div className="p-3.5 rounded-lg bg-[#0F172A] border border-slate-800/90 col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Inference Latency</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-emerald-400">&lt; 12 ms</span>
            <span className="text-xs text-slate-500">4 Layers</span>
          </div>
          <div className="mt-2 text-[10px] text-slate-500 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Dual-ML Pipeline</span>
          </div>
        </div>
      </div>

      {/* ── MAIN INTERACTIVE GRID: 35 STATIONS MATRIX + SIDEBAR INTEL ── */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Left 3 Columns: 35-Station Telemetry Grid */}
        <div className="xl:col-span-3 space-y-4">
          <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
                  Station Network Telemetry Matrix
                </h3>
                <span className="text-xs font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  {filteredStations.length} of {totalStations} Stations
                </span>
              </div>

              {/* Search & Sort Controls */}
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search AWS name, ID, or state..."
                    className="pl-8 pr-3 py-1 text-xs bg-slate-900 border border-slate-800 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-600 font-mono w-48 sm:w-60"
                  />
                </div>

                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded px-2 py-1 font-mono focus:outline-none"
                >
                  <option value="risk">Sort by Risk</option>
                  <option value="temp">Sort by Temp</option>
                  <option value="name">Sort by Name</option>
                </select>
              </div>
            </div>

            {/* Zonal Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-mono scrollbar-none">
              <span className="text-[11px] text-slate-500 mr-1 uppercase">Zone:</span>
              {zones.map((zone) => (
                <button
                  key={zone}
                  onClick={() => setSelectedZone(zone)}
                  className={`px-2.5 py-0.5 rounded transition ${
                    selectedZone === zone
                      ? 'bg-slate-800 text-slate-100 font-bold border border-slate-700'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  {zone}
                </button>
              ))}
            </div>

            {/* Telemetry Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead className="bg-slate-900/80 text-[11px] text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Station / ID</th>
                    <th className="py-2.5 px-3">Zone / State</th>
                    <th className="py-2.5 px-3 text-right">Temp (°C)</th>
                    <th className="py-2.5 px-3 text-right">Pressure (hPa)</th>
                    <th className="py-2.5 px-3 text-right">RH (%)</th>
                    <th className="py-2.5 px-3 text-right">Risk Score</th>
                    <th className="py-2.5 px-3 text-center">4-Layer Verdict</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredStations.map((st) => {
                    const isFaulty = Boolean(st.active_fault);
                    const riskVal = st.risk?.score || 0;
                    return (
                      <tr 
                        key={st.id || st.station}
                        onClick={() => onSelectStation(st.station)}
                        className="hover:bg-slate-800/40 transition cursor-pointer group"
                      >
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          <StatusBadge status={st.status} />
                        </td>
                        <td className="py-2.5 px-3 font-medium text-slate-200 group-hover:text-emerald-300 transition">
                          <div className="flex items-center gap-1.5">
                            <span className="font-sans font-semibold">{st.station}</span>
                            {isFaulty && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-950 text-rose-400 border border-rose-800 font-bold">
                                {st.active_fault}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono">{st.id} · {st.elevation_m}m AMSL</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                          <div>{st.zone}</div>
                          <div className="text-[10px] text-slate-500">{st.state}</div>
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-200">
                          {st.temperature !== null && st.temperature !== undefined ? `${st.temperature.toFixed(1)}°C` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-300">
                          {st.pressure !== null && st.pressure !== undefined ? `${st.pressure.toFixed(1)} hPa` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-300">
                          {st.humidity !== null && st.humidity !== undefined ? `${Math.round(st.humidity)}%` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <span className={`font-bold ${riskVal > 60 ? 'text-rose-400' : riskVal > 30 ? 'text-amber-400' : 'text-emerald-400'}`}>
                            {riskVal} / 100
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            st.detection?.layer1 === 'FAIL' || st.detection?.layer2_lstm?.is_anomaly || st.detection?.layer3 === 'FAIL'
                              ? 'bg-rose-950/60 text-rose-400 border border-rose-800/60'
                              : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                          }`}>
                            {st.detection?.layer1 === 'FAIL' || st.detection?.layer2_lstm?.is_anomaly || st.detection?.layer3 === 'FAIL'
                              ? 'ANOMALY'
                              : 'NOMINAL'}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectStation(st.station);
                            }}
                            className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition"
                            title="Inspect Station Diagnostics"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right 1 Column: Active Incidents & Engine Pipeline Health */}
        <div className="space-y-4 font-mono">
          {/* Active Incidents Feed */}
          <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2 font-sans font-bold text-sm text-slate-100">
                <AlertOctagon className="w-4 h-4 text-amber-400" />
                <span>Active Incident Feed</span>
              </div>
              <button 
                onClick={onNavigateToAlerts}
                className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1"
              >
                <span>Alerts ({activeAlerts.length})</span>
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>

            {activeAlerts.length === 0 ? (
              <div className="py-6 text-center text-slate-500 space-y-1">
                <CheckCircle2 className="w-8 h-8 text-emerald-500/40 mx-auto" />
                <p className="text-xs text-slate-400">Zero active incidents across network.</p>
                <p className="text-[10px] text-slate-600">All 35 IMD AWS nodes nominal.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {activeAlerts.slice(0, 5).map((a, i) => (
                  <div 
                    key={i}
                    onClick={() => onSelectStation(a.station)}
                    className="p-2.5 rounded bg-slate-900/90 border border-slate-800 hover:border-slate-700 cursor-pointer space-y-1 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-slate-200 font-sans">{a.station}</span>
                      <SeverityBadge severity={a.severity} />
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{a.detail}</p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                      <span>{a.layer}</span>
                      <span>{a.type}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 4-Layer Defense Engine Pipeline Status */}
          <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2 font-sans font-bold text-sm text-slate-100">
                <Layers className="w-4 h-4 text-emerald-400" />
                <span>Detection Pipeline</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold">
                ACTIVE
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="font-bold text-slate-200 font-sans">Layer 1: Deterministic Rules</div>
                  <div className="text-[10px] text-slate-500">WMO Range & Rate-of-Change</div>
                </div>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>

              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="font-bold text-slate-200 font-sans">Layer 2: Dual ML Ensemble</div>
                  <div className="text-[10px] text-slate-500">PyTorch LSTM AE + Isolation Forest</div>
                </div>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>

              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="font-bold text-slate-200 font-sans">Layer 3: Physical Thermodynamics</div>
                  <div className="text-[10px] text-slate-500">Magnus Dew Point & Storm Fronts</div>
                </div>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>

              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="font-bold text-slate-200 font-sans">Layer 4: Spatial Consensus</div>
                  <div className="text-[10px] text-slate-500">800km Sea-Level Reduction</div>
                </div>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={onNavigateToFaultLab}
                className="w-full py-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-emerald-400 font-semibold transition flex items-center justify-center gap-1.5"
              >
                <span>Launch Fault Injection Sandbox</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
