"use client";
import { PortResult, scanApi } from "@/lib/api";
import { Badge } from "@/components/common/Badge";
import { useState } from "react";
import { Copy, Download, Search } from "lucide-react";

type SortHeaderProps = {
  col: keyof PortResult;
  label: string;
  sortCol: keyof PortResult;
  sortAsc: boolean;
  toggleSort: (col: keyof PortResult) => void;
};

function SortHeader({
  col,
  label,
  sortCol,
  sortAsc,
  toggleSort,
}: SortHeaderProps) {
  return (
    <th
      onClick={() => toggleSort(col)}
      style={{
        padding: "8px 12px",
        textAlign: "left",
        fontSize: 11,
        color: sortCol === col ? "var(--accent)" : "var(--text-dim)",
        cursor: "pointer",
        userSelect: "none",
        whiteSpace: "nowrap",
        fontWeight: 600,
        letterSpacing: "0.05em",
        borderBottom: "1px solid var(--border)",
      }}
    >
      {label} {sortCol === col ? (sortAsc ? "↑" : "↓") : ""}
    </th>
  );
}

export default function ResultsTable({
  results,
  scanId,
  preset,
  onCopySelected,
  clearResults,
}: {
  results: PortResult[];
  scanId: string | null;
  preset: "quick" | "common" | "custom" | "discovery";
  onCopySelected: (rows: PortResult[]) => void;
  clearResults: () => void;
}) {
  const [search, setSearch] = useState("");
  const [filterState, setFilterState] = useState(
    preset === "discovery" ? "reachable" : "all",
  );
  const [sortCol, setSortCol] = useState<keyof PortResult>("port");
  const [sortAsc, setSortAsc] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const filtered = results
    .filter((r) => {
      if (filterState !== "all" && r.state !== filterState) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          r.host_ip.includes(q) ||
          (r.hostname || "").toLowerCase().includes(q) ||
          r.port.toString().includes(q) ||
          (r.service || "").toLowerCase().includes(q) ||
          r.state.includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => {
      const av = a[sortCol] ?? "";
      const bv = b[sortCol] ?? "";
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortAsc ? cmp : -cmp;
    });

  const toggleSort = (col: keyof PortResult) => {
    if (sortCol === col) setSortAsc(!sortAsc);
    else {
      setSortCol(col);
      setSortAsc(true);
    }
  };

  const openCount = results.filter((r) => r.state === "open").length;

  const rowKey = (r: PortResult) => `${r.host_ip}:${r.port}`;

  const toggleSelect = (r: PortResult) => {
    const k = rowKey(r);
    const s = new Set(selected);

    if (s.has(k)) {
      s.delete(k);
    } else {
      s.add(k);
    }
    setSelected(s);
  };

  const stateFilters = [
    "all",
    "open",
    "closed",
    "timeout",
    "unreachable",
    "error",
    "reachable",
    "host_down",
  ];
  const filterLabels: Record<string, string> = {
    all: "all",
    open: "open",
    closed: "closed",
    timeout: "timeout",
    unreachable: "unreachable",
    error: "error",
    reachable: "active",
    host_down: "down",
  };

  return (
    <div className="card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontWeight: 600 }}>Results</span>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {filtered.length.toLocaleString()} shown /{" "}
            {results.length.toLocaleString()} total
          </span>
          {openCount > 0 && (
            <span className="badge badge-open">{openCount} open</span>
          )}
          <button
            className="btn btn-ghost"
            onClick={() => {
              console.log("clear clicked");
              clearResults();
            }}
            style={{
              padding: "4px 10px",
              fontSize: "var(--fs-main)",
              borderColor: "var(--border)",
              color: "var(--error)",
            }}
          >
            Clear results
          </button>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {selected.size > 0 && (
            <button
              className="btn btn-ghost"
              style={{ fontSize: 11, padding: "4px 10px" }}
              onClick={() =>
                onCopySelected(filtered.filter((r) => selected.has(rowKey(r))))
              }
            >
              <Copy size={12} /> Copy {selected.size}
            </button>
          )}
          {scanId && (
            <>
              <button
                className="btn btn-ghost"
                style={{ fontSize: "var(--fs-main)", padding: "4px 10px" }}
                onClick={() => scanApi.exportCsv(scanId, false)}
              >
                <Download size={12} /> Export CSV
              </button>
            </>
          )}
        </div>
      </div>

      <div
        style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}
      >
        <div style={{ position: "relative", flex: 1, minWidth: 200 }}>
          <Search
            size={13}
            style={{
              position: "absolute",
              left: 10,
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-dim)",
            }}
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={
              preset === "discovery"
                ? "Search active host, IP, state..."
                : "Search host, port, service..."
            }
            style={{ paddingLeft: 30 }}
          />
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {stateFilters.map((f) => (
            <button
              key={f}
              onClick={() => setFilterState(f)}
              className="btn btn-ghost"
              style={{
                padding: "4px 10px",
                fontSize: "var(--fs-main)",
                borderColor:
                  filterState === f ? "var(--accent)" : "var(--border)",
                color:
                  filterState === f ? "var(--accent)" : "var(--text-muted)",
              }}
            >
              {filterLabels[f] ?? f}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "40px 20px",
            color: "var(--text-dim)",
            fontSize: "var(--fs-main)",
          }}
        >
          {results.length === 0
            ? "No results yet. Start a scan."
            : "No results match your filters."}
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th
                  style={{
                    width: 32,
                    padding: "8px 12px",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <input
                    type="checkbox"
                    style={{ width: "auto" }}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelected(new Set(filtered.map(rowKey)));
                      } else {
                        setSelected(new Set());
                      }
                    }}
                  />
                </th>

                <SortHeader
                  col="state"
                  label="STATE"
                  sortCol={sortCol}
                  sortAsc={sortAsc}
                  toggleSort={toggleSort}
                />
                <SortHeader
                  col="host_ip"
                  label="HOST"
                  sortCol={sortCol}
                  sortAsc={sortAsc}
                  toggleSort={toggleSort}
                />
                <SortHeader
                  col="port"
                  label="PORT"
                  sortCol={sortCol}
                  sortAsc={sortAsc}
                  toggleSort={toggleSort}
                />
                <SortHeader
                  col="service"
                  label="SERVICE"
                  sortCol={sortCol}
                  sortAsc={sortAsc}
                  toggleSort={toggleSort}
                />
                <SortHeader
                  col="latency_ms"
                  label="LATENCY"
                  sortCol={sortCol}
                  sortAsc={sortAsc}
                  toggleSort={toggleSort}
                />
              </tr>
            </thead>

            <tbody>
              {filtered.map((r) => {
                const k = rowKey(r);

                return (
                  <>
                    <tr
                      key={k}
                      style={{
                        background: selected.has(k)
                          ? "rgba(0,212,170,0.05)"
                          : "transparent",
                      }}
                    >
                      <td
                        style={{ padding: "8px 12px" }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="checkbox"
                          style={{ width: "auto" }}
                          checked={selected.has(k)}
                          onChange={() => toggleSelect(r)}
                        />
                      </td>

                      <td style={{ padding: "8px 12px" }}>
                        <Badge state={r.state} />
                      </td>

                      <td style={{ padding: "8px 12px" }}>
                        <span>{r.host_ip}</span>
                        {r.hostname && (
                          <span
                            style={{
                              marginLeft: 6,
                              fontSize: "var(--fs-main)",
                            }}
                          >
                            ({r.hostname})
                          </span>
                        )}
                      </td>

                      <td
                        style={{
                          padding: "8px 12px",
                          fontWeight: 600,
                          color:
                            r.port === 0 ? "var(--text-dim)" : "var(--text)",
                        }}
                      >
                        {r.port === 0 ? "—" : r.port}
                      </td>

                      <td style={{ padding: "8px 12px" }}>
                        {r.service || "—"}
                      </td>

                      <td
                        style={{
                          padding: "8px 12px",
                          fontSize: "var(--fs-main)",
                        }}
                      >
                        {r.latency_ms != null ? `${r.latency_ms} ms` : "—"}
                      </td>
                    </tr>
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
