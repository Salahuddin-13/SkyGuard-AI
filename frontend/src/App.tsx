import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { CommandCenter } from './pages/CommandCenter';
import { LiveMap } from './pages/LiveMap';
import { StationDeepDive } from './pages/StationDeepDive';
import { FaultLab } from './pages/FaultLab';
import { HardwareEdge } from './pages/HardwareEdge';
import { AlertCenter } from './pages/AlertCenter';
import { ModelIntelligence } from './pages/ModelIntelligence';
import { Analytics } from './pages/Analytics';
import { PresentationMode } from './pages/PresentationMode';
import { api, TelemetrySocket } from './services/api';
import type { NetworkOverview } from './types';
import { fallbackNetworkData } from './data/fallbackData';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('command-center');
  const [selectedStation, setSelectedStation] = useState<string>('Delhi (Safdarjung)');
  const [networkData, setNetworkData] = useState<NetworkOverview>(fallbackNetworkData);
  const [connectionStatus, setConnectionStatus] = useState<'CONNECTED' | 'DISCONNECTED' | 'CONNECTING'>('CONNECTING');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPresentation, setIsPresentation] = useState(false);

  const fetchOverview = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const data = await api.getOverview();
      setNetworkData(data);
    } catch (e) {
      console.error('Failed to fetch initial network snapshot', e);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();

    // Connect WebSocket
    const socket = new TelemetrySocket(
      (msg) => {
        if (msg.type === 'SNAPSHOT' || msg.type === 'TELEMETRY_PULSE' || msg.type === 'NETWORK_UPDATE') {
          setNetworkData(msg.data);
        } else if (msg.type === 'ALERT_UPDATE') {
          fetchOverview();
        }
      },
      (status) => {
        setConnectionStatus(status);
      }
    );

    return () => {
      socket.disconnect();
    };
  }, [fetchOverview]);

  const handleSelectStation = (name: string) => {
    setSelectedStation(name);
    setActiveTab('station-deep-dive');
  };

  const healthyPercent = networkData
    ? Math.round((networkData.healthy / (networkData.total_stations || 1)) * 100)
    : 100;

  return (
    <div className="flex h-screen bg-[#0B0F17] text-slate-100 overflow-hidden font-sans select-none">
      {/* Sidebar */}
      {!isPresentation && (
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          activeAlertsCount={networkData?.alerts?.length || 0}
          healthyPercent={healthyPercent}
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {!isPresentation && (
          <Header
            activeTab={activeTab}
            isConnected={connectionStatus === 'CONNECTED'}
            onRefresh={fetchOverview}
            isRefreshing={isRefreshing}
            onOpenPresentation={() => setIsPresentation(true)}
            activeFaultCount={networkData?.active_faults_count || 0}
          />
        )}

        <main className="flex-1 overflow-y-auto bg-[#0B0F17]">
          {activeTab === 'command-center' && (
            <CommandCenter
              networkData={networkData}
              onSelectStation={handleSelectStation}
              onNavigateToFaultLab={() => setActiveTab('fault-lab')}
              onNavigateToMap={() => setActiveTab('live-map')}
              onNavigateToAlerts={() => setActiveTab('alert-center')}
              onRefresh={fetchOverview}
            />
          )}

          {activeTab === 'live-map' && (
            <LiveMap
              networkData={networkData}
              onSelectStation={handleSelectStation}
            />
          )}

          {activeTab === 'station-deep-dive' && (
            <StationDeepDive
              networkData={networkData}
              selectedStationName={selectedStation}
              onSelectStation={setSelectedStation}
            />
          )}

          {activeTab === 'fault-lab' && (
            <FaultLab
              networkData={networkData}
              onRefresh={fetchOverview}
            />
          )}

          {activeTab === 'hardware-edge' && (
            <HardwareEdge
              networkData={networkData}
              onRefresh={fetchOverview}
            />
          )}

          {activeTab === 'alert-center' && (
            <AlertCenter
              networkData={networkData}
              onRefresh={fetchOverview}
              onSelectStation={handleSelectStation}
            />
          )}

          {activeTab === 'model-intelligence' && (
            <ModelIntelligence />
          )}

          {activeTab === 'analytics' && (
            <Analytics networkData={networkData} />
          )}

          {activeTab === 'presentation' && (
            <PresentationMode
              networkData={networkData}
              onClose={() => setActiveTab('command-center')}
              onNavigateToFaultLab={() => setActiveTab('fault-lab')}
            />
          )}
        </main>
      </div>

      {/* Fullscreen Presentation Modal */}
      {isPresentation && (
        <PresentationMode
          networkData={networkData}
          onClose={() => setIsPresentation(false)}
          onNavigateToFaultLab={() => {
            setIsPresentation(false);
            setActiveTab('fault-lab');
          }}
        />
      )}
    </div>
  );
};
export default App;
