"use client";
import ScanConfigPanel from "@/components/scan/ScanConfigPanel";
import ProgressPanel from "@/components/scan/ProgressPanel";
import ResultsTable from "@/components/scan/ResultsTable";
import PresetsPanel from "@/components/modals/PresetsPanel";
import { useScan } from "@/hooks/useScan";
import { useState } from "react";

export default function Home() {
  const {
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
  } = useScan();

  const [showPresets, setShowPresets] = useState(false);

  return (
    <>
      <ScanConfigPanel
        config={config}
        setConfig={setConfig}
        onStart={startScan}
        onStop={stopScan}
        scanning={scanning}
        validationError={validationError}
      />

      <ProgressPanel progress={progress} />

      <ResultsTable
        key={config.preset}
        results={results}
        scanId={scanId}
        preset={config.preset}
        onCopySelected={(rows) => console.log(rows)}
        clearResults={clearResults}
      />

      {showPresets && (
        <PresetsPanel onClose={() => setShowPresets(false)} onLoad={() => {}} />
      )}
    </>
  );
}
