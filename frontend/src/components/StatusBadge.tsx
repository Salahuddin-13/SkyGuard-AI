import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, XCircle, HelpCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  className?: string;
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  className = '',
  showIcon = true
}) => {
  const normStatus = (status || '').toUpperCase();

  switch (normStatus) {
    case 'HEALTHY':
    case 'NOMINAL':
    case 'NORMAL':
    case 'PASS':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-950/40 text-emerald-300 border border-emerald-800/40 ${className}`}>
          {showIcon && <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />}
          <span>NOMINAL</span>
        </span>
      );

    case 'WARNING':
    case 'ADVISORY':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-950/40 text-amber-300 border border-amber-800/40 ${className}`}>
          {showIcon && <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />}
          <span>WARNING</span>
        </span>
      );

    case 'HIGH_RISK':
    case 'HIGH':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-orange-950/40 text-orange-300 border border-orange-800/40 ${className}`}>
          {showIcon && <AlertTriangle className="w-3 h-3 text-orange-400 shrink-0" />}
          <span>HIGH RISK</span>
        </span>
      );

    case 'CRITICAL':
    case 'FAIL':
    case 'ANOMALY':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-rose-950/50 text-rose-300 border border-rose-800/50 ${className}`}>
          {showIcon && <AlertOctagon className="w-3 h-3 text-rose-400 shrink-0 animate-pulse" />}
          <span>CRITICAL</span>
        </span>
      );

    case 'OFFLINE':
    case 'STALE':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-900 text-slate-400 border border-slate-800 ${className}`}>
          {showIcon && <XCircle className="w-3 h-3 text-slate-500 shrink-0" />}
          <span>OFFLINE</span>
        </span>
      );

    default:
      return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-900 text-slate-400 border border-slate-800 ${className}`}>
          {showIcon && <HelpCircle className="w-3 h-3 text-slate-500 shrink-0" />}
          <span>{status || 'UNKNOWN'}</span>
        </span>
      );
  }
};

export const SeverityBadge: React.FC<{ severity: string; className?: string }> = ({ severity, className = '' }) => {
  const norm = (severity || '').toUpperCase();
  if (norm === 'CRITICAL' || norm === 'HIGH') {
    return (
      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 ${className}`}>
        {norm}
      </span>
    );
  }
  if (norm === 'WARNING' || norm === 'MEDIUM') {
    return (
      <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 ${className}`}>
        {norm}
      </span>
    );
  }
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-400 border border-slate-700/50 ${className}`}>
      {norm || 'LOW'}
    </span>
  );
};
