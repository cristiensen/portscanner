"use client";

import { Preset, presetsApi } from "@/lib/api";
import { Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";

export default function PresetsPanel({
  onLoad,
  onClose,
}: {
  onLoad: (preset: Preset) => void;
  onClose: () => void;
}) {
  const [presets, setPresets] = useState<Preset[]>([]);

  useEffect(() => {
    presetsApi.list().then(setPresets).catch(console.error);
  }, []);

  const deletePreset = async (id: string) => {
    await presetsApi.delete(id);
    setPresets(presets.filter((p) => p.id !== id));
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.7)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
      }}
    >
      <div
        className="card"
        style={{ width: 500, maxHeight: "80vh", overflow: "auto" }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: 16,
          }}
        >
          <span style={{ fontWeight: 600 }}>Saved Presets</span>
          <button
            className="btn btn-ghost"
            style={{ padding: "2px 8px" }}
            onClick={onClose}
          >
            <X size={14} />
          </button>
        </div>
        {presets.map((p) => (
          <div
            key={p.id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "10px 12px",
              borderRadius: 6,
              marginBottom: 6,
              background: "var(--bg-card2)",
              border: "1px solid var(--border)",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>{p.name}</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                {p.targets || "any"} · {p.ports || "no ports"} · {p.timing}
              </div>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                className="btn btn-primary"
                style={{ fontSize: 11, padding: "4px 10px" }}
                onClick={() => {
                  onLoad(p);
                  onClose();
                }}
              >
                Load
              </button>
              {p.id && (
                <button
                  className="btn btn-danger"
                  style={{ fontSize: 11, padding: "4px 8px" }}
                  onClick={() => p.id && deletePreset(p.id)}
                >
                  <Trash2 size={12} />
                </button>
              )}
            </div>
          </div>
        ))}
        {presets.length === 0 && (
          <div
            style={{
              color: "var(--text-dim)",
              textAlign: "center",
              padding: 20,
            }}
          >
            No saved presets yet.
          </div>
        )}
      </div>
    </div>
  );
}
