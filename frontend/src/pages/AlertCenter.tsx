import React, { useState } from 'react';
import type { NetworkOverview, AlertItem } from '../types';
import { apiService } from '../services/api';
import { SeverityBadge } from '../components/StatusBadge';
import { 
  BellRing, 
  CheckCircle2, 
  Clock, 
  Search, 
  Download, 
  Filter, 
  FileText, 
  UserCheck, 
  SearchCheck,
  ShieldCheck,
  ArrowRight
} from 'lucide-react';

interface AlertCenterProps {
  networkData: NetworkOverview | null;
  onRefresh: () => void;
  onSelectStation: (name: string) => void;
}

export const AlertCenter: React.FC<AlertCenterProps> = ({
  networkData,
  onRefresh,
  onSelectStation
}) => {
  const [filterState, setFilterState] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [notesState, setNotesState] = useState<{ [alertId: string]: string }>({});
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  if (!networkData) {
    return <div className="p-8 text-slate-500 font-mono animate-pulse">Loading Alert Center...</div>;
  }

  const alerts: AlertItem[] = networkData.alerts || [];

  const handleAction = async (alertId: string, action: string) => {
    try {
      setActionLoading(alertId);
      const note = notesState[alertId] || '';
      await apiService.updateAlertAction(alertId, action, note);
      onRefresh();
    } catch (e) {
      console.error('Alert action error:', e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDownloadCsv = () => {
    window.open('http://localhost:8000/api/export/csv', '_blank');
  };

  // Filter alerts
  const filteredAlerts = alerts.filter((a) => {
    const currentState = a.lifecycle?.state || 'NEW';
    const matchesTab = filterState === 'ALL' || currentState === filterState;
    const matchesSearch =
      (a.station || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.type || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.detail || '').toLowerCase().includes(searchTerm.toLowerCase());
    return matchesTab && matchesSearch;
  });

  const stateTabs = ['ALL', 'NEW', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED'];

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── HEADER WITH CSV EXPORT ── */}
      <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <BellRing className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">Incident Command & Alert Center</h2>
            <p className="text-xs text-slate-400 font-mono">Triage, operational lifecycle state machine, and incident audit log</p>
          </div>
        </div>

        <button
          onClick={handleDownloadCsv}
          className="px-3 py-2 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 text-xs font-mono transition flex items-center gap-2 self-start sm:self-auto"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export Audit Log (CSV)</span>
        </button>
      </div>

      {/* ── TABS & SEARCH BAR ── */}
      <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* State Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto">
          {stateTabs.map((tab) => {
            const count =
              tab === 'ALL'
                ? alerts.length
                : alerts.filter((a) => (a.lifecycle?.state || 'NEW') === tab).length;

            return (
              <button
                key={tab}
                onClick={() => setFilterState(tab)}
                className={`px-3 py-1.5 rounded text-xs font-mono transition flex items-center gap-1.5 ${
                  filterState === tab
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                <span>{tab}</span>
                <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-300">
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Filter by station, alert type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-600 font-mono"
          />
        </div>
      </div>

      {/* ── INCIDENT CARDS ── */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="py-16 text-center rounded-lg bg-[#0F172A] border border-slate-800/90 font-mono text-xs text-slate-500 space-y-2">
            <ShieldCheck className="w-8 h-8 text-emerald-500/40 mx-auto" />
            <p>No incidents in this view. All AWS telemetry nominal.</p>
          </div>
        ) : (
          filteredAlerts.map((a) => {
            const alertId = a.alert_id || `${a.station}_${a.type}`;
            const currentState = a.lifecycle?.state || 'NEW';
            const noteVal = notesState[alertId] !== undefined ? notesState[alertId] : (a.lifecycle?.notes || '');
            const isLoading = actionLoading === alertId;

            return (
              <div
                key={alertId}
                className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3 hover:border-slate-700/80 transition"
              >
                {/* Top Row: Station, Severity, Lifecycle Pill */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
                  <div className="flex items-center gap-2.5">
                    <button
                      onClick={() => onSelectStation(a.station)}
                      className="text-sm font-bold text-slate-100 hover:text-emerald-400 font-sans transition flex items-center gap-1"
                    >
                      <span>{a.station}</span>
                      <ArrowRight className="w-3 h-3 text-slate-500" />
                    </button>
                    <span className="text-xs font-mono text-slate-500">[{a.type}]</span>
                    <SeverityBadge severity={a.severity} />
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-slate-400">STATE:</span>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                      currentState === 'RESOLVED'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : currentState === 'INVESTIGATING'
                        ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                        : currentState === 'ACKNOWLEDGED'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    }`}>
                      {currentState}
                    </span>
                  </div>
                </div>

                {/* Detail & Layer Info */}
                <div className="text-xs font-mono text-slate-300 leading-relaxed">
                  {a.detail}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-slate-400 pt-1">
                  <div>
                    Detection Layer: <span className="text-slate-200">{a.layer}</span>
                  </div>
                  <div>
                    Timestamp: <span className="text-slate-300">{a.timestamp}</span>
                  </div>
                </div>

                {/* Operator Triage Notes & Action Buttons */}
                <div className="pt-2 border-t border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  {/* Notes Input */}
                  <div className="flex items-center gap-2 flex-1">
                    <span className="text-[11px] font-mono text-slate-500 shrink-0">Operator Notes:</span>
                    <input
                      type="text"
                      placeholder="Add triage comments / calibration ticket..."
                      value={noteVal}
                      onChange={(e) => setNotesState({ ...notesState, [alertId]: e.target.value })}
                      className="w-full px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-slate-600"
                    />
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    {currentState === 'NEW' && (
                      <button
                        onClick={() => handleAction(alertId, 'ACKNOWLEDGED')}
                        disabled={isLoading}
                        className="px-3 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-mono font-semibold transition"
                      >
                        Acknowledge
                      </button>
                    )}

                    {(currentState === 'NEW' || currentState === 'ACKNOWLEDGED') && (
                      <button
                        onClick={() => handleAction(alertId, 'INVESTIGATING')}
                        disabled={isLoading}
                        className="px-3 py-1 rounded bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-300 text-xs font-mono font-semibold transition"
                      >
                        Investigate
                      </button>
                    )}

                    {currentState !== 'RESOLVED' && (
                      <button
                        onClick={() => handleAction(alertId, 'RESOLVED')}
                        disabled={isLoading}
                        className="px-3 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-semibold transition"
                      >
                        Mark Resolved ✓
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* ── SYSTEM EVENT AUDIT TRAIL ── */}
      {networkData.event_log && networkData.event_log.length > 0 && (
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-100 uppercase tracking-wide">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span>Immutable Event & Incident Audit Trail</span>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto font-mono text-xs">
            {networkData.event_log.slice().reverse().map((ev, i) => (
              <div key={i} className="p-2 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 text-[11px]">{ev.timestamp}</span>
                  <span className="text-emerald-400 font-semibold">[{ev.event}]</span>
                  <span className="text-slate-300">{ev.station}:</span>
                  <span className="text-slate-400">{ev.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
