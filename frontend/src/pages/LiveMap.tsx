import React, { useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { NetworkOverview, StationData } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { 
  Layers, 
  MapPin, 
  Thermometer, 
  Gauge, 
  Droplets, 
  ShieldAlert, 
  ArrowUpRight, 
  X,
  Compass
} from 'lucide-react';

interface LiveMapProps {
  networkData: NetworkOverview | null;
  onSelectStation: (name: string) => void;
}

// Helper to center map
function ChangeView({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

export const LiveMap: React.FC<LiveMapProps> = ({ networkData, onSelectStation }) => {
  const [selectedZone, setSelectedZone] = useState('ALL');
  const [selectedStationName, setSelectedStationName] = useState<string | null>('Delhi (Safdarjung)');
  const [showRadius, setShowRadius] = useState(true);

  if (!networkData) {
    return (
      <div className="p-6 h-[800px] flex items-center justify-center font-mono text-slate-500 animate-pulse">
        Loading GIS Map Engine...
      </div>
    );
  }

  const stations: StationData[] = Object.values(networkData.stations || {});
  const filteredStations = stations.filter(
    (s) => selectedZone === 'ALL' || s.zone.toUpperCase() === selectedZone
  );

  const selectedStation = selectedStationName ? networkData.stations[selectedStationName] : null;

  const zones = ['ALL', 'NORTH', 'WEST', 'CENTRAL', 'EAST', 'NORTH-EAST', 'SOUTH', 'ISLAND'];

  return (
    <div className="p-6 space-y-4 max-w-[1600px] mx-auto h-[calc(100vh-5rem)] flex flex-col">
      {/* ── MAP TOOLBAR ── */}
      <div className="p-3.5 rounded-lg bg-[#0F172A] border border-slate-800/90 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Pan-India AWS Geospatial Risk Map</h2>
          <span className="text-xs text-slate-500 font-mono">({filteredStations.length} Stations Displayed)</span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          {/* Spatial Radius Toggle */}
          <button
            onClick={() => setShowRadius(!showRadius)}
            className={`px-2.5 py-1 rounded text-xs font-mono transition border ${
              showRadius
                ? 'bg-sky-500/10 text-sky-400 border-sky-500/30'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            800km Spatial Ring: {showRadius ? 'ON' : 'OFF'}
          </button>

          {/* Zone Segments */}
          <div className="flex items-center gap-1">
            {zones.map((z) => (
              <button
                key={z}
                onClick={() => setSelectedZone(z)}
                className={`px-2 py-0.5 rounded text-xs font-mono transition ${
                  selectedZone === z
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {z}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── MAP CONTAINER WITH FLOATING DRAWER ── */}
      <div className="flex-1 rounded-lg overflow-hidden border border-slate-800/90 relative bg-[#0B0F17]">
        <MapContainer
          center={[22.5, 79.5]}
          zoom={5}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%', background: '#0B0F17' }}
        >
          <ChangeView center={[22.5, 79.5]} zoom={5} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* 800km Spatial Ring around selected station */}
          {selectedStation && showRadius && (
            <Circle
              center={[selectedStation.lat, selectedStation.lon]}
              radius={800000}
              pathOptions={{
                color: '#38BDF8',
                fillColor: '#38BDF8',
                fillOpacity: 0.05,
                weight: 1,
                dashArray: '4, 4'
              }}
            />
          )}

          {/* Station Markers */}
          {filteredStations.map((st) => {
            const isSelected = selectedStationName === st.station;
            const isCritical = st.status === 'CRITICAL' || st.status === 'HIGH_RISK';
            const isWarning = st.status === 'WARNING';

            let markerColor = '#10B981'; // Emerald
            if (isCritical) markerColor = '#F43F5E'; // Rose
            else if (isWarning) markerColor = '#F59E0B'; // Amber

            return (
              <CircleMarker
                key={st.station}
                center={[st.lat, st.lon]}
                radius={isSelected ? 10 : isCritical ? 8 : 6}
                pathOptions={{
                  color: isSelected ? '#38BDF8' : markerColor,
                  fillColor: markerColor,
                  fillOpacity: 0.85,
                  weight: isSelected ? 3 : 1.5
                }}
                eventHandlers={{
                  click: () => {
                    setSelectedStationName(st.station);
                  }
                }}
              >
                <Popup className="custom-leaflet-popup">
                  <div className="p-2 text-xs font-mono space-y-1 bg-[#0F172A] text-slate-200 rounded">
                    <div className="font-bold text-slate-100">{st.station}</div>
                    <div className="text-[11px] text-slate-400">{st.id} · {st.elevation_m}m AMSL</div>
                    <div className="pt-1 flex items-center justify-between">
                      <span>Temp: {st.temperature?.toFixed(1)}°C</span>
                      <span>RH: {st.humidity?.toFixed(0)}%</span>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>

        {/* ── FLOATING DETAIL DRAWER ── */}
        {selectedStation && (
          <div className="absolute top-4 right-4 w-80 bg-[#0F172A]/95 backdrop-blur border border-slate-700/80 rounded-lg p-4 shadow-2xl space-y-3.5 z-[1000] text-xs">
            {/* Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-2.5">
              <div>
                <h3 className="font-bold text-slate-100 text-sm font-sans">{selectedStation.station}</h3>
                <p className="text-[11px] text-slate-400 font-mono">{selectedStation.id} · {selectedStation.state}</p>
                <p className="text-[10px] text-slate-500 font-mono">{selectedStation.elevation_m}m AMSL · {selectedStation.lat.toFixed(4)}°N, {selectedStation.lon.toFixed(4)}°E</p>
              </div>
              <button
                onClick={() => setSelectedStationName(null)}
                className="p-1 text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Status & Risk */}
            <div className="flex items-center justify-between">
              <StatusBadge status={selectedStation.status} />
              <div className="flex items-center gap-1.5 font-mono">
                <span className="text-slate-400 text-[11px]">Risk Index:</span>
                <span className={`px-2 py-0.5 rounded font-bold ${
                  (selectedStation.risk?.score || 0) > 60
                    ? 'bg-rose-500/20 text-rose-300'
                    : (selectedStation.risk?.score || 0) > 30
                    ? 'bg-amber-500/20 text-amber-300'
                    : 'bg-emerald-500/20 text-emerald-300'
                }`}>
                  {selectedStation.risk?.score || 0} / 100
                </span>
              </div>
            </div>

            {/* Telemetry KPI Grid */}
            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Temperature</div>
                <div className="text-base font-bold text-slate-100">
                  {selectedStation.temperature !== null ? `${selectedStation.temperature.toFixed(1)} °C` : '—'}
                </div>
              </div>

              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Surface Pressure</div>
                <div className="text-base font-bold text-slate-100">
                  {selectedStation.pressure !== null ? `${selectedStation.pressure.toFixed(1)} hPa` : '—'}
                </div>
              </div>

              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Rel Humidity</div>
                <div className="text-base font-bold text-slate-100">
                  {selectedStation.humidity !== null ? `${selectedStation.humidity.toFixed(0)} %` : '—'}
                </div>
              </div>

              <div className="p-2 rounded bg-slate-900/80 border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Dew Point (Magnus)</div>
                <div className="text-base font-bold text-slate-300">
                  {selectedStation.dew_point !== null ? `${selectedStation.dew_point.toFixed(1)} °C` : '—'}
                </div>
              </div>
            </div>

            {/* Spatial Context */}
            {selectedStation.spatial && (
              <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800 space-y-1 text-[11px] font-mono">
                <div className="text-slate-400 font-semibold">Spatial Neighborhood Consensus:</div>
                <div className="text-slate-500">
                  Regional Mean: <span className="text-slate-300">{selectedStation.spatial.mean_temp?.toFixed(1)}°C</span> · 
                  Dev: <span className={selectedStation.spatial.temp_dev > 3 ? 'text-amber-400 font-bold' : 'text-slate-300'}>
                    +{selectedStation.spatial.temp_dev?.toFixed(1)}°C
                  </span>
                </div>
              </div>
            )}

            {/* Action */}
            <button
              onClick={() => onSelectStation(selectedStation.station)}
              className="w-full py-2 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
            >
              <span>Inspect Full Diagnostics</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* ── MAP LEGEND ── */}
        <div className="absolute bottom-4 left-4 bg-[#0F172A]/90 backdrop-blur border border-slate-800 rounded px-3 py-2 text-[11px] font-mono text-slate-300 flex items-center gap-4 z-[1000]">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <span>Nominal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span>Warning</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            <span>Critical Anomaly</span>
          </div>
        </div>
      </div>
    </div>
  );
};
