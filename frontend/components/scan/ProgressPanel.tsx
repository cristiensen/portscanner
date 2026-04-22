"use client";

import { ScanProgress } from "@/lib/api";
import { formatTime } from "@/utils/format";
import { CheckCircle } from "lucide-react";

export default function ProgressPanel({
  progress,
}: {
  progress: ScanProgress | null;
}) {
  if (!progress || progress.status === "idle") return null;

  const pct =
    progress.total_hosts > 0
      ? Math.round((progress.hosts_completed / progress.total_hosts) * 100)
      : 0;

  const isRunning = progress.status === "running";

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {isRunning && (
            <span
              className="pulse"
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "var(--accent)",
                display: "inline-block",
              }}
            />
          )}
          {!isRunning && progress.status === "completed" && (
            <CheckCircle size={14} color="var(--open)" />
          )}
          <span
            style={{
              fontWeight: 600,
              textTransform: "uppercase",
              fontSize: "var(--fs-main)",
              color: "var(--text-muted)",
            }}
          >
            {progress.status}
          </span>
        </div>
        <span
          style={{ color: "var(--text-muted)", fontSize: "var(--fs-main)" }}
        >
          {formatTime(progress.elapsed_seconds)} elapsed
        </span>
      </div>

      <div
        style={{
          height: 4,
          background: "var(--bg-card2)",
          borderRadius: 2,
          marginBottom: 14,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: isRunning ? "var(--accent)" : "var(--open)",
            borderRadius: 2,
            transition: "width 0.5s ease",
          }}
        />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 8,
        }}
      >
        {[
          {
            label: "Hosts",
            value: `${progress.hosts_completed}/${progress.total_hosts}`,
          },
          {
            label: "Ports checked",
            value: progress.ports_checked.toLocaleString(),
          },
          {
            label: "Open ports",
            value: progress.open_ports_found,
            accent: true,
          },
          { label: "Complete", value: `${pct}%` },
        ].map((s) => (
          <div
            key={s.label}
            style={{
              background: "var(--bg-card2)",
              borderRadius: 6,
              padding: "8px 10px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: 18,
                fontWeight: 700,
                color: s.accent ? "var(--open)" : "var(--text)",
              }}
            >
              {s.value}
            </div>
            <div
              style={{
                fontSize: "var(--fs-main)",
                color: "var(--text-dim)",
                marginTop: 2,
              }}
            >
              {s.label}
            </div>
          </div>
        ))}
      </div>

      {isRunning && progress.current_host && (
        <div
          style={{
            marginTop: 10,
            fontSize: "var(--fs-main)",
            color: "var(--text-muted)",
            fontFamily: "monospace",
          }}
        >
          scanning:{" "}
          <span style={{ color: "var(--accent)" }}>
            {progress.current_host}
          </span>
          {progress.current_port && (
            <>
              {" "}
              :{" "}
              <span style={{ color: "var(--text)" }}>
                {progress.current_port}
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
