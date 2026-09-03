import React, { useState } from 'react';
import type { NetworkOverview } from '../types';
import { apiService } from '../services/api';
import { 
  Cpu, 
  Wifi, 
  Battery, 
  RotateCcw, 
  Terminal, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  Zap, 
  Radio, 
  HelpCircle,
  Activity,
  Layers
} from 'lucide-react';

interface HardwareEdgeProps {
  networkData: NetworkOverview | null;
  onRefresh: () => void;
}

export const HardwareEdge: React.FC<HardwareEdgeProps> = ({ networkData, onRefresh }) => {
  const [activeFault, setActiveFault] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const handleInjectHwFault = async (faultType: string) => {
    try {
      setIsExecuting(true);
      setActiveFault(faultType);
      await apiService.injectHardwareFault(faultType);
      onRefresh();
    } catch (e) {
      console.error('Hw fault inject error:', e);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleClearHwFault = async () => {
    try {
      setIsExecuting(true);
      setActiveFault(null);
      await apiService.clearHardwareFault();
      onRefresh();
    } catch (e) {
      console.error('Hw fault clear error:', e);
    } finally {
      setIsExecuting(false);
    }
  };

  const hardwareState = {
    device_id: 'ESP32-WROOM-32D-AWS01',
    firmware_version: 'v2.4.1-sih',
    supply_voltage_v: activeFault === 'power_brownout' ? 2.84 : 3.98,
    wifi_rssi_dbm: activeFault === 'packet_loss' ? -89 : -58,
    i2c_status: activeFault === 'i2c_bus_stall' ? 'BUS_LOCKED (TIMEOUT)' : 'NORMAL (0x76 ACK)',
    dht22_status: activeFault === 'dht22_crc_error' ? 'CHECKSUM_FAILED (CRC ERR)' : 'CRC_VALID (GPIO4)',
    packet_loss_pct: activeFault === 'packet_loss' ? 85 : 0
  };

  const mockSerialLogs = [
    `[00:00:01.120] [ESP32] Bootloader v2.4.1 initialized (Dual-Core 240MHz)`,
    `[00:00:01.240] [I2C-0] Bus scan 400kHz: Found device at addr 0x76 (Bosch BMP280)`,
    `[00:00:01.310] [GPIO4] 1-Wire bus connected to Aosong DHT22 relative humidity sensor`,
    `[00:00:02.040] [WIFI] Associated with AWS-GATEWAY-IN (RSSI: ${hardwareState.wifi_rssi_dbm} dBm)`,
    `[00:00:03.110] [MQTT] Connected to tcp://gateway.skyguard.internal:1883 with keepalive=30s`,
    `[00:00:04.500] [TELEMETRY] TX {node: "ESP32-AWS01", vbat: ${hardwareState.supply_voltage_v}V, T: 27.4C, P: 1013.2hPa, RH: 64%}`,
    activeFault === 'i2c_bus_stall' && `[00:00:05.100] [ERROR] I2C Bus timeout! SCL line held LOW. BMP280 read failed.`,
    activeFault === 'dht22_crc_error' && `[00:00:05.220] [ERROR] DHT22 1-Wire parity check failed: calculated 0x4B != received 0x12.`,
    activeFault === 'packet_loss' && `[00:00:05.410] [WARN] WiFi RSSI degraded to -89dBm. 85% packet drop on MQTT socket.`,
    activeFault === 'power_brownout' && `[00:00:05.600] [CRITICAL] Supply voltage dropped to 2.84V (<3.0V threshold). ADC reference swinging!`
  ].filter(Boolean);

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── HEADER ── */}
      <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 uppercase tracking-wide">Dedicated Hardware & Edge Ingestion Console</h2>
            <p className="text-xs text-slate-400 font-mono">ESP32 edge node telemetry, physical transducer buses, and electrical fault simulator</p>
          </div>
        </div>

        {activeFault && (
          <button
            onClick={handleClearHwFault}
            disabled={isExecuting}
            className="px-3 py-1.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-mono font-bold hover:bg-amber-500/30 transition flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Hardware State</span>
          </button>
        )}
      </div>

      {/* ── EDGE MICROCONTROLLER TELEMETRY TILES ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Tile 1: ESP32 Node */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-2 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Edge Microcontroller</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-sm font-bold text-slate-100">{hardwareState.device_id}</div>
          <div className="text-[11px] text-slate-400">
            Firmware: <span className="text-slate-200">{hardwareState.firmware_version}</span>
          </div>
        </div>

        {/* Tile 2: Battery Rail */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-2 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Supply Voltage (Li-Ion)</span>
            <Battery className={`w-4 h-4 ${hardwareState.supply_voltage_v < 3.0 ? 'text-rose-400 animate-pulse' : 'text-emerald-400'}`} />
          </div>
          <div className={`text-2xl font-bold ${hardwareState.supply_voltage_v < 3.0 ? 'text-rose-400' : 'text-slate-100'}`}>
            {hardwareState.supply_voltage_v.toFixed(2)} V
          </div>
          <div className="text-[11px] text-slate-400">
            Nominal Range: 3.60V – 4.20V (ADC Reference: 3.3V)
          </div>
        </div>

        {/* Tile 3: Wi-Fi RSSI */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-2 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Wi-Fi RSSI / Link Quality</span>
            <Wifi className={`w-4 h-4 ${hardwareState.wifi_rssi_dbm < -80 ? 'text-rose-400 animate-pulse' : 'text-emerald-400'}`} />
          </div>
          <div className={`text-2xl font-bold ${hardwareState.wifi_rssi_dbm < -80 ? 'text-rose-400' : 'text-slate-100'}`}>
            {hardwareState.wifi_rssi_dbm} dBm
          </div>
          <div className="text-[11px] text-slate-400">
            Packet Drop Rate: <span className={hardwareState.packet_loss_pct > 0 ? 'text-rose-400 font-bold' : 'text-slate-200'}>{hardwareState.packet_loss_pct}%</span>
          </div>
        </div>

        {/* Tile 4: Hardware BOM Cost */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-2 font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Hardware BOM Cost</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">₹ 582 INR</div>
          <div className="text-[11px] text-slate-400">
            ESP32 (₹320) + BMP280 (₹125) + DHT22 (₹110)
          </div>
        </div>
      </div>

      {/* ── HARDWARE FAULT INJECTION SANDBOX ── */}
      <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-4">
        <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Simulate Physical Transducer & Bus Faults</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Fault 1: I2C Stall */}
          <div className="p-3 rounded bg-slate-900/80 border border-slate-800 space-y-2 flex flex-col justify-between">
            <div>
              <div className="font-bold text-slate-200 text-xs">I2C Bus Lockup / Stall</div>
              <p className="text-[11px] text-slate-400 mt-1">Simulates SCL line held LOW by slave. BMP280 timeout.</p>
            </div>
            <button
              onClick={() => handleInjectHwFault('i2c_bus_stall')}
              disabled={isExecuting}
              className={`w-full py-1.5 rounded text-xs font-mono font-semibold transition ${
                activeFault === 'i2c_bus_stall'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {activeFault === 'i2c_bus_stall' ? 'Active Fault ✓' : 'Simulate I2C Lockup'}
            </button>
          </div>

          {/* Fault 2: DHT22 CRC Error */}
          <div className="p-3 rounded bg-slate-900/80 border border-slate-800 space-y-2 flex flex-col justify-between">
            <div>
              <div className="font-bold text-slate-200 text-xs">1-Wire Checksum Failure</div>
              <p className="text-[11px] text-slate-400 mt-1">Simulates single-wire parity corruption on DHT22 humidity.</p>
            </div>
            <button
              onClick={() => handleInjectHwFault('dht22_crc_error')}
              disabled={isExecuting}
              className={`w-full py-1.5 rounded text-xs font-mono font-semibold transition ${
                activeFault === 'dht22_crc_error'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {activeFault === 'dht22_crc_error' ? 'Active Fault ✓' : 'Simulate CRC Failure'}
            </button>
          </div>

          {/* Fault 3: Packet Loss */}
          <div className="p-3 rounded bg-slate-900/80 border border-slate-800 space-y-2 flex flex-col justify-between">
            <div>
              <div className="font-bold text-slate-200 text-xs">Wi-Fi Packet Loss (85%)</div>
              <p className="text-[11px] text-slate-400 mt-1">Simulates antenna degradation & transmission timeouts.</p>
            </div>
            <button
              onClick={() => handleInjectHwFault('packet_loss')}
              disabled={isExecuting}
              className={`w-full py-1.5 rounded text-xs font-mono font-semibold transition ${
                activeFault === 'packet_loss'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {activeFault === 'packet_loss' ? 'Active Fault ✓' : 'Simulate Packet Drop'}
            </button>
          </div>

          {/* Fault 4: Power Brownout */}
          <div className="p-3 rounded bg-slate-900/80 border border-slate-800 space-y-2 flex flex-col justify-between">
            <div>
              <div className="font-bold text-slate-200 text-xs">Power Rail Brownout (&lt;3.0V)</div>
              <p className="text-[11px] text-slate-400 mt-1">Simulates battery drop causing ADC voltage instability.</p>
            </div>
            <button
              onClick={() => handleInjectHwFault('power_brownout')}
              disabled={isExecuting}
              className={`w-full py-1.5 rounded text-xs font-mono font-semibold transition ${
                activeFault === 'power_brownout'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {activeFault === 'power_brownout' ? 'Active Fault ✓' : 'Simulate Brownout'}
            </button>
          </div>
        </div>
      </div>

      {/* ── DISAMBIGUATION & STREAMING SERIAL CONSOLE ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Disambiguation Matrix Card */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-100 uppercase tracking-wide">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span>Device Fault vs Natural Storm Disambiguation</span>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
              <div className="text-emerald-400 font-bold">Natural Convective Storm Signature:</div>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Temperature drops (T↓), Pressure rises (P↑), Humidity rises (RH↑) simultaneously, adhering to Magnus Dew Point (Td ≤ Ta).
                <span className="text-emerald-300 font-semibold block mt-0.5">✓ Recognized as genuine atmospheric weather event.</span>
              </p>
            </div>

            <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
              <div className="text-rose-400 font-bold">Transducer Electrical Failure Signature:</div>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Isolated temperature spike (+25°C) with unchanged pressure/humidity, or frozen standard deviation (std &lt; 0.01).
                <span className="text-rose-300 font-semibold block mt-0.5">✗ Flagged as physical sensor failure.</span>
              </p>
            </div>
          </div>
        </div>

        {/* Streaming Serial Console Card */}
        <div className="p-4 rounded-lg bg-[#0F172A] border border-slate-800/90 space-y-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-100 uppercase tracking-wide">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <span>Live UART / MQTT Packet Stream</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/50">
              115200 BAUD
            </span>
          </div>

          <div className="p-3 rounded bg-black border border-slate-800 font-mono text-[11px] text-slate-300 h-44 overflow-y-auto space-y-1">
            {mockSerialLogs.map((log, idx) => (
              <div key={idx} className={log.includes('ERROR') || log.includes('CRITICAL') ? 'text-rose-400 font-bold' : log.includes('WARN') ? 'text-amber-400' : 'text-slate-400'}>
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
