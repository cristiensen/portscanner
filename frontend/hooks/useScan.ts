"use client";

import { useState, useRef } from "react";
import {
  scanApi,
  createWebSocket,
  ScanConfig,
  PortResult,
  ScanProgress,
} from "@/lib/api";
import validateTargetsInput from "./validateTargetsInput";

export function useScan() {
  const [config, setConfig] = useState<ScanConfig>({
    targets: "",
    ports: "22,80,443",
    timing: "balanced",
    preset: "custom",
    host_discovery: true,
    banner_grab: false,
  });

  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [results, setResults] = useState<PortResult[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);
  const clearResults = () => {
    wsRef.current?.close();
    setScanning(false);
    setResults([]);
  };

  const wsRef = useRef<WebSocket | null>(null);

  const startScan = async () => {
    setValidationError(null);

    if (!config.targets.trim()) {
      setValidationError("Missing targets");
      return;
    }

    const targetFormatError = validateTargetsInput(config.targets);
    if (targetFormatError) {
      setValidationError("Please enter a valid TARGET input.");
      return;
    }

    wsRef.current?.close();
    setResults([]);
    setProgress(null);

    const { scan_id } = await scanApi.start(config);
    setScanId(scan_id);
    setScanning(true);

    const ws = createWebSocket(scan_id);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "update") {
        setProgress(msg.progress);
        if (msg.new_results) {
          setResults((prev) => [...prev, ...msg.new_results]);
        }
      }

      if (msg.type === "complete") {
        setScanning(false);
      }
    };
  };

  const stopScan = async () => {
    if (!scanId) return;
    wsRef.current?.close();
    await scanApi.stop(scanId);
    setScanning(false);
    setProgress((prev) => (prev ? { ...prev, status: "cancelled" } : null));
  };

  return {
    config,
    setConfig,
    scanning,
    progress,
    results,
    clearResults,
    validationError,
    startScan,
    stopScan,
    scanId,
  };
}
