import React from 'react';
import { 
  LayoutDashboard, 
  Map, 
  Activity, 
  FlaskConical, 
  Cpu, 
  BellRing, 
  BrainCircuit, 
  BarChart3, 
  Presentation,
  Shield,
  Radio
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeAlertsCount: number;
  healthyPercent: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  activeAlertsCount,
  healthyPercent
}) => {
  const navigationGroups = [
    {
      group: 'OPERATIONS',
      items: [
        { id: 'command-center', label: 'Command Center', icon: LayoutDashboard },
        { id: 'live-map', label: 'Live Risk Map', icon: Map },
        { id: 'station-deep-dive', label: 'Station Diagnostics', icon: Activity },
      ]
    },
    {
      group: 'MONITORING',
      items: [
        { id: 'hardware-edge', label: 'Hardware & Edge', icon: Cpu },
        { id: 'alert-center', label: 'Alert Center', icon: BellRing, badge: activeAlertsCount > 0 ? activeAlertsCount : null },
      ]
    },
    {
      group: 'INTELLIGENCE',
      items: [
        { id: 'model-intelligence', label: 'ML Intelligence', icon: BrainCircuit },
        { id: 'analytics', label: 'Analytics & Reliability', icon: BarChart3 },
      ]
    },
    {
      group: 'DEMO & EVALUATION',
      items: [
        { id: 'fault-lab', label: 'Fault Injection Lab', icon: FlaskConical },
        { id: 'presentation', label: 'Presentation Mode', icon: Presentation },
      ]
    }
  ];

  return (
    <aside className="w-64 bg-[#0D131F] border-r border-slate-800 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="px-5 py-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wider text-slate-100 uppercase">SKYGUARD AI</h1>
            <p className="text-[10px] text-slate-400 font-mono tracking-tight">IMD AWS Reliability</p>
          </div>
        </div>
        <div className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/50">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>v2.0</span>
        </div>
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {navigationGroups.map((grp) => (
          <div key={grp.group} className="space-y-1">
            <div className="px-3 text-[10px] font-semibold text-slate-500 tracking-wider uppercase">
              {grp.group}
            </div>
            <div className="space-y-0.5">
              {grp.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-slate-800/90 text-white border-l-2 border-emerald-400 pl-2.5 font-semibold shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <span>{item.label}</span>
                    </div>

                    {item.badge !== undefined && item.badge !== null && (
                      <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Network Status & Government Badge */}
      <div className="p-3 border-t border-slate-800/80 bg-[#0B0F17]/90 space-y-3">
        {/* Availability Bar */}
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400 font-medium">Network Availability</span>
            <span className="text-emerald-400 font-mono font-bold">{healthyPercent}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                healthyPercent > 80 ? 'bg-emerald-500' : healthyPercent > 50 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${healthyPercent}%` }}
            />
          </div>
        </div>

        {/* SIH Ministry Badge */}
        <div className="px-2 py-1 flex items-center justify-between text-[10px] text-slate-500 font-mono">
          <span>SIH26073 · MoES / IMD</span>
          <span className="text-slate-400">35 AWS Nodes</span>
        </div>
      </div>
    </aside>
  );
};
