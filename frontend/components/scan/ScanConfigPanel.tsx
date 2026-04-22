import validateTargetsInput from "@/hooks/validateTargetsInput";
import { ScanConfig } from "@/lib/api";
import { AlertTriangle, CheckCircle, Play, Square, Target } from "lucide-react";
import { useState } from "react";

export default function ScanConfigPanel({
  config,
  setConfig,
  onStart,
  onStop,
  scanning,
  validationError,
}: {
  config: ScanConfig;
  setConfig: (c: ScanConfig) => void;
  onStart: () => void;
  onStop: () => void;
  scanning: boolean;
  validationError: string | null;
}) {
  const [targetError, setTargetError] = useState<string | null>(null);

  const isCustomPreset = config.preset === "custom";

  const presetOptions = [
    { value: "custom", label: "Custom" },
    { value: "quick", label: "Quick (common ports)" },
    { value: "common", label: "Common (top ~20 ports)" },
    { value: "discovery", label: "Discovery (active hosts only)" },
  ];

  const timingOptions = [
    { value: "safe", label: "Safe — slower, minimal load" },
    { value: "balanced", label: "Balanced — recommended" },
    { value: "fast", label: "Fast — aggressive, may miss ports" },
  ];

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 16,
        }}
      >
        <Target size={16} color="var(--accent)" />
        <span style={{ fontWeight: 600, color: "var(--accent)" }}>
          Scan Configuration
        </span>
      </div>

      <div style={{ gridColumn: "1 / -1" }}>
        <label
          style={{
            display: "block",
            marginBottom: 4,
            color: "var(--text-muted)",
            fontSize: "var(--fs-main)",
          }}
        >
          TARGETS
        </label>
        <input
          value={config.targets}
          placeholder="192.168.1.1  or  192.168.1.0/24  or  10.0.0.1-10.0.0.50"
          disabled={scanning}
          onChange={(e) => {
            setConfig({ ...config, targets: e.target.value });
            setTargetError(validateTargetsInput(e.target.value));
          }}
        />
        {targetError ? (
          <div
            style={{
              marginTop: 6,
              fontSize: "var(--fs-main)",
              color: "var(--error)",
              display: "flex",
              gap: 5,
              alignItems: "flex-start",
            }}
          >
            <AlertTriangle size={12} style={{ flexShrink: 0, marginTop: 1 }} />
            {targetError}
          </div>
        ) : (
          config.targets.trim() && (
            <div
              style={{
                marginTop: 6,
                fontSize: "var(--fs-main)",
                color: "var(--open)",
                display: "flex",
                gap: 5,
                alignItems: "center",
              }}
            >
              <CheckCircle size={12} />
              Valid target format
            </div>
          )
        )}
      </div>

      <div className="flex flex-row gap-3">
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 4,
              color: "var(--text-muted)",
              fontSize: "var(--fs-main)",
            }}
          >
            PRESET
          </label>
          <select
            value={config.preset}
            onChange={(e) => {
              setConfig({
                ...config,
                preset: e.target.value as ScanConfig["preset"],
              });
            }}
            disabled={scanning}
            style={{ appearance: "none" }}
          >
            {presetOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            style={{
              display: "block",
              marginBottom: 4,
              color: "var(--text-muted)",
              fontSize: "var(--fs-main)",
            }}
          >
            PORTS
          </label>
          <input
            onChange={(e) => {
              setConfig({ ...config, ports: e.target.value });
            }}
            placeholder={
              isCustomPreset
                ? "22,80,443  or  1-1024  or  22,80,8000-8100"
                : "Preset defines ports"
            }
            disabled={scanning || !isCustomPreset}
            style={{
              backgroundColor:
                scanning || !isCustomPreset
                  ? "rgba(255, 255, 255, 0.05)"
                  : "var(--bg)",
              cursor: scanning || !isCustomPreset ? "not-allowed" : "text",
              opacity: scanning || !isCustomPreset ? 0.6 : 1,
            }}
          />
        </div>
      </div>
      <div
        className="flex flex-row items-center"
        style={{
          marginTop: 12,
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 12,
        }}
      >
        <div>
          <label
            style={{
              display: "block",
              marginBottom: 4,
              color: "var(--text-muted)",
              fontSize: "var(--fs-main)",
            }}
          >
            TIMING PROFILE
          </label>
          <select
            value={config.timing}
            onChange={(e) =>
              setConfig({
                ...config,
                timing: e.target.value as ScanConfig["timing"],
              })
            }
            disabled={scanning}
            style={{ appearance: "none" }}
          >
            {timingOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 8,
            paddingTop: 20,
          }}
        ></div>
      </div>
      {validationError && (
        <div
          style={{
            marginTop: 12,
            padding: "10px 12px",
            borderRadius: 6,
            background: "rgba(248,81,73,0.1)",
            border: "1px solid rgba(248,81,73,0.3)",
            color: "var(--error)",
            fontSize: "var(--fs-main)",
            display: "flex",
            gap: 8,
            alignItems: "flex-start",
          }}
        >
          <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
          {validationError}
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        {!scanning ? (
          <button
            className="btn btn-primary"
            onClick={onStart}
            style={{ flex: 1 }}
          >
            <Play size={14} /> Start Scan
          </button>
        ) : (
          <button
            className="btn btn-danger"
            onClick={onStop}
            style={{ flex: 1 }}
          >
            <Square size={14} /> Stop Scan
          </button>
        )}
      </div>

      <div
        style={{
          marginTop: 12,
          padding: "8px 10px",
          borderRadius: 6,
          background: "rgba(210,153,34,0.08)",
          border: "1px solid rgba(210,153,34,0.2)",
          color: "#d29922",
          fontSize: "var(--fs-main)",
        }}
      >
        <strong>⚠ Authorized use only.</strong> Only scan systems and networks
        you have explicit permission to scan. Unauthorized scanning may be
        illegal.
      </div>
    </div>
  );
}
