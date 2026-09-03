import React from 'react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  PieChart, 
  Pie, 
  Cell, 
  Legend 
} from 'recharts';
import type { NetworkOverview } from '../types';
import { 
  BarChart3, 
  ShieldCheck, 
  Clock, 
  Zap, 
  CheckCircle2, 
  Database,
  Layers,
  MapPin
} from 'lucide-react';

interface AnalyticsProps {
  networkData: NetworkOverview | null;
}

export const Analytics: React.FC<AnalyticsProps> = ({ networkData }) => {
  if (!networkData) {
    return <div className="p-8 text-slate-500 font-mono animate-pulse">Loading Analytics...</div>;
  }

  const healthy = networkData.healthy || 0;
  const warning = networkData.warning || 0;
  const critical = networkData.critical || 0;

  const statusPieData = [
    { name: 'Nominal', value: healthy, color: '#10B981' },
    { name: 'Warning', value: warning, color: '#F59E0B' },
    { name: 'Critical', value: critical, color: '#F43F5E' },
  ].filter((d) => d.value > 0);

  // Group stations by meteorological zone
  const zoneCounts: { [zone: string]: number } = {};
  Object.values(networkData.stations || {}).forEach((st) => {
    zoneCounts[st.zone] = (zoneCounts[st.zone] || 0) + 1;
  });

  const zoneBarData = Object.entries(zoneCounts).map(([zone, count]) => ({
    zone,
    count
  }));

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── HEADER ── */}
      <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">Network Analytics & Station Reliability</h2>
            <p className="text-xs text-slate-400 font-mono">Performance metrics, zonal density distribution, and training dataset statistics</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
            35 Stations Online
          </span>
        </div>
      </div>

      {/* ── KPI TILES ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Station Reliability SLA</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">99.98 %</div>
          <p className="mt-1 text-[11px] text-slate-500">Autonomous uptime guarantee</p>
        </div>

        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Mean Detection Latency</span>
            <Clock className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">&lt; 12 ms</div>
          <p className="mt-1 text-[11px] text-slate-500">Full 4-layer evaluation</p>
        </div>

        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Edge Node Unit Cost</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">₹ 582 INR</div>
          <p className="mt-1 text-[11px] text-slate-500">BOM: ESP32 + BMP280 + DHT22</p>
        </div>

        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">ML Training Samples</span>
            <Database className="w-4 h-4 text-sky-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">100,000</div>
          <p className="mt-1 text-[11px] text-slate-500">Jena Climate Dataset</p>
        </div>
      </div>

      {/* ── CHARTS ROW: STATUS DISTRIBUTION & ZONAL DENSITY ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Status Distribution */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Network Health Status Ratio</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {statusPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    borderColor: '#334155',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#F8FAFC',
                    fontFamily: 'monospace'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Zonal Station Density */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Meteorological Zonal AWS Density</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneBarData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="zone" stroke="#64748B" tick={{ fontSize: 10, fill: '#64748B' }} interval={0} angle={-20} textAnchor="end" />
                <YAxis stroke="#64748B" tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    borderColor: '#334155',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: '#F8FAFC',
                    fontFamily: 'monospace'
                  }}
                />
                <Bar dataKey="count" name="Stations" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
