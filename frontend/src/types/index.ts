export type StationStatus = 'HEALTHY' | 'WARNING' | 'HIGH_RISK' | 'CRITICAL' | 'OFFLINE';
export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export interface StationReading {
  temperature: number | null;
  pressure: number | null;
  humidity: number | null;
  wind_speed?: number | null;
  weather_code?: number | null;
  timestamp: string;
}

export interface Alert {
  station: string;
  station_id: string;
  alert_id: string;
  layer: string;
  type: string;
  severity: Severity;
  detail: string;
  sensor?: string;
  score?: number;
  threshold?: number;
  timestamp?: string;
  lifecycle?: {
    state: 'NEW' | 'ACKNOWLEDGED' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';
    history: Array<{ timestamp: string; action: string; notes?: string }>;
    notes?: string;
  };
}

export interface SpatialContext {
  available: boolean;
  nearby_count?: number;
  nearby_stations?: string[];
  temp_regional_avg?: number;
  temp_deviation?: number;
  temp_consistent?: boolean;
  pres_regional_avg?: number;
  pres_deviation?: number;
  pres_consistent?: boolean;
  hum_regional_avg?: number;
  hum_deviation?: number;
  hum_consistent?: boolean;
  overall_consistent?: boolean;
  reason?: string;
}

export interface DataQuality {
  score: number;
  issues: string[];
  fresh: boolean;
  complete: boolean;
  valid: boolean;
  consistent: boolean;
  age_seconds?: number;
}

export interface RiskScore {
  score: number;
  level: StationStatus;
  components: {
    rule_violations: number;
    temporal_anomaly: number;
    spatial_deviation: number;
    data_quality: number;
  };
}

export interface Explanation {
  reasons: string[];
  conclusion: string;
  recommended_action: string;
  classification: string;
  layers_fired: string[];
  sensors_affected: string[];
  spatial_consistent: boolean;
}

export interface StationDetail {
  station: string;
  id: string;
  state: string;
  zone: string;
  lat: number;
  lon: number;
  elevation_m: number;
  temperature: number | null;
  pressure: number | null;
  humidity: number | null;
  wind_speed?: number;
  dew_point: number | null;
  timestamp: string;
  status: StationStatus;
  risk: RiskScore;
  quality: DataQuality;
  spatial: SpatialContext;
  detection: {
    alerts: Alert[];
    layer1: 'PASS' | 'FAIL';
    layer2_lstm?: {
      model: string;
      anomaly_score: number;
      threshold: number;
      is_anomaly: boolean;
      error_temperature: number;
      error_pressure: number;
      error_humidity: number;
    } | null;
    layer2_iforest?: {
      model: string;
      decision_score: number;
      threshold: number;
      is_anomaly: boolean;
    } | null;
    layer3: 'PASS' | 'FAIL';
  };
  explanation: Explanation;
  hourly?: {
    time: string[];
    temperature_2m: number[];
    surface_pressure: number[];
    relative_humidity_2m: number[];
  };
  source: string;
  active_fault?: string | null;
}

export interface HardwareState {
  device_id: string;
  station_id: string;
  station_name: string;
  firmware_version: string;
  uptime_seconds: number;
  wifi_rssi_dbm: number;
  battery_mv: number;
  i2c_bus_status: string;
  bmp280_status: string;
  dht22_status: string;
  packet_drop_rate_pct: number;
  last_packet_timestamp: string;
  hardware_fault: string | null;
}

export interface NetworkOverview {
  timestamp: string;
  total_stations: number;
  healthy: number;
  warning: number;
  critical: number;
  active_faults_count: number;
  stations: Record<string, StationDetail>;
  alerts: Alert[];
  hardware: HardwareState;
}

export type StationData = StationDetail;
export type AlertItem = Alert;
