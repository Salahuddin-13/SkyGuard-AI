import React, { useState, useEffect } from 'react';
import { 
  Wifi, 
  WifiOff, 
  Clock, 
  RotateCw, 
  Radio, 
  Presentation, 
  AlertTriangle,
  Server
} from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  isConnected: boolean;
  onRefresh: () => void;
  isRefreshing: boolean;
  onOpenPresentation: () => void;
  activeFaultCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  isConnected,
  onRefresh,
  isRefreshing,
  onOpenPresentation,
  activeFaultCount
}) => {
  const [istTime, setIstTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      };
      const dateOptions: Intl.DateTimeFormatOptions = {
        timeZone: 'Asia/Kolkata',
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      };
      const timeStr = new Intl.DateTimeFormat('en-IN', options).format(now);
      const dateStr = new Intl.DateTimeFormat('en-IN', dateOptions).format(now);
      setIstTime(`${dateStr} · ${timeStr} IST`);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getBreadcrumb = () => {
    switch (activeTab) {
      case 'command-center': return 'OPERATIONS / COMMAND CENTER';
      case 'live-map': return 'OPERATIONS / LIVE RISK MAP (GIS)';
      case 'station-deep-dive': return 'OPERATIONS / STATION DIAGNOSTICS';
      case 'hardware-edge': return 'MONITORING / HARDWARE & EDGE INGESTION';
      case 'alert-center': return 'MONITORING / INCIDENT COMMAND & ALERTS';
      case 'model-intelligence': return 'INTELLIGENCE / ML MODEL OBSERVABILITY';
      case 'analytics': return 'INTELLIGENCE / NETWORK RELIABILITY & METRICS';
      case 'fault-lab': return 'DEMO & EVALUATION / FAULT INJECTION LAB';
      case 'presentation': return 'DEMO & EVALUATION / SIH PRESENTATION MODE';
      default: return 'OPERATIONS / OVERVIEW';
    }
  };

  return (
    <header className="h-14 bg-[#0D131F] border-b border-slate-800/80 px-6 flex items-center justify-between select-none z-10 shrink-0">
      {/* Left Context Breadcrumb */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-mono tracking-wide text-slate-400">
          <span className="text-slate-200 font-semibold">SKYGUARD AI</span>
          <span className="text-slate-600">/</span>
          <span className="text-emerald-400 font-medium">{getBreadcrumb()}</span>
        </div>
      </div>

      {/* Right Controls & Telemetry Heartbeat */}
      <div className="flex items-center gap-3">
        {/* Simulation Badge if faults are active */}
        {activeFaultCount > 0 && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-950/60 border border-amber-800/60 text-amber-300 text-xs font-mono font-medium">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            <span>{activeFaultCount} FAULT{activeFaultCount > 1 ? 'S' : ''} ACTIVE</span>
          </div>
        )}

        {/* WebSocket Connection Status */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono border ${
          isConnected
            ? 'bg-slate-900/90 text-slate-300 border-slate-800'
            : 'bg-rose-950/40 text-rose-300 border-rose-800/50'
        }`}>
          {isConnected ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>LIVE FEED (3s)</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-rose-400" />
              <span>RECONNECTING...</span>
            </>
          )}
        </div>

        {/* Live IST Clock */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900/70 border border-slate-800 text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{istTime || 'Loading time...'}</span>
        </div>

        {/* Manual Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh IMD Observations"
          className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
        </button>

        {/* Presentation Kiosk Trigger */}
        <button
          onClick={onOpenPresentation}
          className="flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 hover:border-emerald-500/50 text-xs font-medium transition"
        >
          <Presentation className="w-3.5 h-3.5" />
          <span>Presentation Mode</span>
        </button>
      </div>
    </header>
  );
};
