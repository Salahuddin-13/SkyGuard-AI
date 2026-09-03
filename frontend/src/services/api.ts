import axios from 'axios';
import type { NetworkOverview, Alert } from '../types';

const isLocal = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const API_BASE = isLocal ? 'http://127.0.0.1:8000/api' : '/api';

export const api = {
  getOverview: async (): Promise<NetworkOverview> => {
    const res = await axios.get<NetworkOverview>(`${API_BASE}/overview`);
    return res.data;
  },

  getStations: async () => {
    const res = await axios.get(`${API_BASE}/stations`);
    return res.data;
  },

  getStationDetail: async (stationName: string) => {
    const res = await axios.get(`${API_BASE}/stations/${encodeURIComponent(stationName)}`);
    return res.data;
  },

  getAlerts: async () => {
    const res = await axios.get<{ alerts: Alert[]; total: number; event_log: any[] }>(`${API_BASE}/alerts`);
    return res.data;
  },

  updateAlertAction: async (alertId: string, action: string, operatorNotes?: string) => {
    const res = await axios.post(`${API_BASE}/alerts/action`, {
      alert_id: alertId,
      action,
      operator_notes: operatorNotes
    });
    return res.data;
  },

  injectFault: async (stationName: string, faultType: string) => {
    const res = await axios.post(`${API_BASE}/faults/inject`, {
      station_name: stationName,
      fault_type: faultType
    });
    return res.data;
  },

  clearFault: async (stationName?: string) => {
    const res = await axios.post(`${API_BASE}/faults/clear`, {
      station_name: stationName || null
    });
    return res.data;
  },

  injectHardwareFault: async (faultType: string) => {
    const res = await axios.post(`${API_BASE}/hardware/inject`, { fault_type: faultType });
    return res.data;
  },

  clearHardwareFault: async () => {
    const res = await axios.post(`${API_BASE}/hardware/clear`);
    return res.data;
  },

  getModelInfo: async () => {
    const res = await axios.get(`${API_BASE}/model/info`);
    return res.data;
  },

  getSystemHealth: async () => {
    const res = await axios.get(`${API_BASE}/system/health`);
    return res.data;
  }
};

export const apiService = api;

export class TelemetrySocket {
  private ws: WebSocket | null = null;
  private onMessageCallback: ((data: any) => void) | null = null;
  private onStatusChange: ((status: 'CONNECTED' | 'DISCONNECTED' | 'CONNECTING') => void) | null = null;
  private reconnectInterval: any = null;

  constructor(
    onMessage: (data: any) => void,
    onStatus: (status: 'CONNECTED' | 'DISCONNECTED' | 'CONNECTING') => void
  ) {
    this.onMessageCallback = onMessage;
    this.onStatusChange = onStatus;
    this.connect();
  }

  connect() {
    try {
      this.onStatusChange?.('CONNECTING');
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = isLocal 
        ? 'ws://127.0.0.1:8000/ws/telemetry'
        : `${protocol}//${window.location.host}/ws/telemetry`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.onStatusChange?.('CONNECTED');
        if (this.reconnectInterval) {
          clearInterval(this.reconnectInterval);
          this.reconnectInterval = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.onMessageCallback?.(payload);
        } catch (e) {
          console.error('WebSocket parse error', e);
        }
      };

      this.ws.onclose = () => {
        this.onStatusChange?.('DISCONNECTED');
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.onStatusChange?.('DISCONNECTED');
      };
    } catch (e) {
      this.onStatusChange?.('DISCONNECTED');
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (!this.reconnectInterval) {
      this.reconnectInterval = setInterval(() => {
        this.connect();
      }, 3000);
    }
  }

  disconnect() {
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval);
    }
    this.ws?.close();
  }
}
