import asyncio
import json
import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from ..models import ScanConfig, ScanStatus
from ..scanner import (
    run_scan, cancel_scan, get_progress, get_results,
    get_summary, is_scan_done, validate_scan_config
)
from ..database import save_history

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("/validate")
async def validate_scan(config: ScanConfig):
    """Validate scan config and return parsed target/port counts."""
    try:
        targets, ports = validate_scan_config(config)
        return {
            "valid": True,
            "host_count": len(targets),
            "port_count": len(ports),
            "total_combinations": len(targets) * max(len(ports), 1),
        }
    except ValueError as e:
        return {"valid": False, "error": str(e)}


@router.post("/start")
async def start_scan(config: ScanConfig):
    """Start a new scan. Returns scan_id immediately."""
    try:
        validate_scan_config(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    scan_id = await run_scan(config)
    return {"scan_id": scan_id, "status": "running"}


@router.delete("/{scan_id}/stop")
async def stop_scan(scan_id: str):
    """Cancel a running scan."""
    found = cancel_scan(scan_id)
    if not found:
        raise HTTPException(status_code=404, detail="Scan not found or already finished")
    return {"scan_id": scan_id, "status": "cancelling"}


@router.get("/{scan_id}/progress")
async def scan_progress(scan_id: str):
    progress = get_progress(scan_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return progress


@router.get("/{scan_id}/results")
async def scan_results(
    scan_id: str,
    state: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
):
    results = get_results(scan_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    filtered = results
    if state:
        filtered = [r for r in filtered if r["state"] == state]
    if host:
        filtered = [r for r in filtered if host.lower() in (r["host_ip"] + r.get("hostname", "") or "").lower()]
    if port:
        filtered = [r for r in filtered if r["port"] == port]

    return {"scan_id": scan_id, "count": len(filtered), "results": filtered}


@router.get("/{scan_id}/summary")
async def scan_summary(scan_id: str):
    summary = get_summary(scan_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return summary


@router.get("/{scan_id}/export/csv")
async def export_csv(
    scan_id: str,
    open_only: bool = False,
    state: Optional[str] = None,
):
    """Export scan results as CSV file download."""
    results = get_results(scan_id)
    summary = get_summary(scan_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    if open_only:
        results = [r for r in results if r["state"] == "open"]
    elif state:
        results = [r for r in results if r["state"] == state]

    output = io.StringIO()
    writer = csv.writer(output)

    if summary:
        writer.writerow(["# Port Scanner Export"])
        writer.writerow(["# Scan ID", summary.scan_id])
        writer.writerow(["# Targets", summary.targets])
        writer.writerow(["# Ports", summary.ports])
        writer.writerow(["# Timing", summary.timing])
        writer.writerow(["# Started", summary.started_at])
        writer.writerow(["# Finished", summary.finished_at or "N/A"])
        writer.writerow(["# Status", summary.status.value])
        writer.writerow([])

    writer.writerow(["host_input", "host_ip", "hostname", "port", "protocol",
                     "state", "service", "latency_ms", "banner", "timestamp", "error_reason"])
    for r in results:
        writer.writerow([
            r.get("host_input"), r.get("host_ip"), r.get("hostname"),
            r.get("port"), r.get("protocol"), r.get("state"),
            r.get("service"), r.get("latency_ms"), r.get("banner"),
            r.get("timestamp"), r.get("error_reason"),
        ])

    output.seek(0)
    filename = f"scan_{scan_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.websocket("/ws/{scan_id}")
async def websocket_progress(websocket: WebSocket, scan_id: str):
    """WebSocket endpoint: streams progress updates every 500ms until scan completes."""
    await websocket.accept()

    try:
        last_result_count = 0

        while True:
            progress = get_progress(scan_id)
            if progress is None:
                await websocket.send_json({"error": "Scan not found"})
                break

            results = get_results(scan_id) or []
            new_results = results[last_result_count:]
            last_result_count = len(results)

            await websocket.send_json({
                "type": "update",
                "progress": progress.model_dump(),
                "new_results": new_results,
            })

            if is_scan_done(scan_id):
                summary = get_summary(scan_id)
                if summary:
                    await save_history(summary)
                    await websocket.send_json({
                        "type": "complete",
                        "summary": summary.model_dump(),
                    })
                break

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass