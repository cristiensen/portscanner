import axios from "axios";

const API = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

export interface ScanConfig {
  targets: string;
  ports: string;
  timing: "safe" | "balanced" | "fast";
  preset: "quick" | "common" | "custom" | "discovery";
  host_discovery: boolean;
  banner_grab: boolean;
  scan_id?: string;
}

export interface PortResult {
  scan_id: string;
  host_input: string;
  host_ip: string;
  hostname?: string;
  port: number;
  protocol: string;
  state:
    | "open"
    | "closed"
    | "timeout"
    | "unreachable"
    | "error"
    | "reachable"
    | "host_down";
  latency_ms?: number;
  service?: string;
  banner?: string;
  timestamp: string;
  error_reason?: string;
}

export interface ScanProgress {
  scan_id: string;
  status: "idle" | "running" | "completed" | "cancelled" | "error";
  total_hosts: number;
  total_ports: number;
  hosts_completed: number;
  ports_checked: number;
  open_ports_found: number;
  elapsed_seconds: number;
  current_host?: string;
  current_port?: number;
  estimated_remaining_seconds?: number;
}

export interface Preset {
  id?: string;
  name: string;
  targets: string;
  ports: string;
  timing: string;
  host_discovery: boolean;
  banner_grab: boolean;
  preset_type: string;
}

export interface HistoryEntry {
  id: string;
  scan_id: string;
  started_at: string;
  finished_at?: string;
  targets: string;
  ports: string;
  timing: string;
  status: string;
  total_hosts: number;
  hosts_reachable: number;
  open_ports_found: number;
}

export const scanApi = {
  validate: (config: ScanConfig) =>
    API.post("/scan/validate", config).then((r) => r.data),

  start: (config: ScanConfig) =>
    API.post("/scan/start", config).then((r) => r.data),

  stop: (scanId: string) =>
    API.delete(`/scan/${scanId}/stop`).then((r) => r.data),

  results: (scanId: string, filters?: Record<string, string>) =>
    API.get(`/scan/${scanId}/results`, { params: filters }).then((r) => r.data),

  summary: (scanId: string) =>
    API.get(`/scan/${scanId}/summary`).then((r) => r.data),

  exportCsv: (scanId: string, openOnly = false) => {
    const url = `/api/scan/${scanId}/export/csv?open_only=${openOnly}`;
    window.open(url, "_blank");
  },
};

export const presetsApi = {
  list: () => API.get("/presets/").then((r) => r.data.presets as Preset[]),
  save: (preset: Preset) => API.post("/presets/", preset).then((r) => r.data),
  delete: (id: string) => API.delete(`/presets/${id}`).then((r) => r.data),
};

export const historyApi = {
  list: () =>
    API.get("/history/").then((r) => r.data.history as HistoryEntry[]),
  clear: () => API.delete("/history/").then((r) => r.data),
};

export function createWebSocket(scanId: string): WebSocket {
  const wsUrl = `ws://localhost:8000/api/scan/ws/${scanId}`;
  return new WebSocket(wsUrl);
}
