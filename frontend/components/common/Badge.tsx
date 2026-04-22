export function Badge({ state }: { state: string }) {
  const cls = state.replace("_", "-");
  const labelMap: Record<string, string> = {
    reachable: "active host",
    host_down: "host down",
  };
  return (
    <span className={`badge badge-${cls}`}>
      {labelMap[state] ?? state.replace("_", " ")}
    </span>
  );
}
