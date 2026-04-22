import aiosqlite
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .models import PresetModel, HistoryEntry, ScanSummary, TimingProfile, ScanPreset

DB_PATH = Path("/app/data/portscanner.db")

async def init_db():
    """Create tables if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                targets TEXT DEFAULT '',
                ports TEXT DEFAULT '',
                timing TEXT DEFAULT 'balanced',
                host_discovery INTEGER DEFAULT 1,
                banner_grab INTEGER DEFAULT 0,
                preset_type TEXT DEFAULT 'custom',
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                targets TEXT,
                ports TEXT,
                timing TEXT,
                status TEXT,
                total_hosts INTEGER DEFAULT 0,
                hosts_reachable INTEGER DEFAULT 0,
                open_ports_found INTEGER DEFAULT 0
            )
        """)
        await db.commit()
    await _seed_presets()

async def _seed_presets():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM presets")
        count = (await cursor.fetchone())[0]
        if count == 0:
            builtins = [
                ("Quick Scan", "", "22,80,443,3389,8080", "balanced", True, False, "quick"),
                ("Common Ports", "", "21,22,25,53,80,110,135,139,143,443,445,993,995,1433,3306,3389,5432,8080,8443", "balanced", True, False, "common"),
                ("Host Discovery", "", "", "safe", True, False, "discovery"),
                ("Web Ports", "", "80,443,8080,8443,8000,8888,3000,4000,5000", "balanced", True, False, "custom"),
            ]
            for name, targets, ports, timing, hd, bg, pt in builtins:
                await db.execute(
                    "INSERT INTO presets VALUES (?,?,?,?,?,?,?,?,?)",
                    (str(uuid.uuid4()), name, targets, ports, timing, int(hd), int(bg), pt, datetime.now(timezone.utc).isoformat())
                )
            await db.commit()

async def get_presets() -> List[PresetModel]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM presets ORDER BY created_at")
        rows = await cursor.fetchall()
        return [PresetModel(
            id=r["id"], name=r["name"], targets=r["targets"],
            ports=r["ports"], timing=TimingProfile(r["timing"]),
            host_discovery=bool(r["host_discovery"]),
            banner_grab=bool(r["banner_grab"]),
            preset_type=ScanPreset(r["preset_type"])
        ) for r in rows]

async def save_preset(preset: PresetModel) -> PresetModel:
    preset.id = preset.id or str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO presets VALUES (?,?,?,?,?,?,?,?,?)",
            (preset.id, preset.name, preset.targets, preset.ports,
             preset.timing.value, int(preset.host_discovery),
             int(preset.banner_grab), preset.preset_type.value,
             datetime.now(timezone.utc).isoformat())
        )
        await db.commit()
    return preset

async def delete_preset(preset_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM presets WHERE id=?", (preset_id,))
        await db.commit()
        return cursor.rowcount > 0

async def save_history(summary: ScanSummary):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM scan_history WHERE id NOT IN (
                SELECT id FROM scan_history ORDER BY started_at DESC LIMIT 99
            )
        """)
        await db.execute(
            "INSERT OR REPLACE INTO scan_history VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), summary.scan_id, summary.started_at,
             summary.finished_at, summary.targets, summary.ports,
             summary.timing, summary.status.value,
             summary.total_hosts, summary.hosts_reachable,
             summary.open_ports_found)
        )
        await db.commit()


async def get_history(limit: int = 50) -> List[HistoryEntry]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM scan_history ORDER BY started_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [HistoryEntry(
            id=r["id"], scan_id=r["scan_id"],
            started_at=r["started_at"], finished_at=r["finished_at"],
            targets=r["targets"], ports=r["ports"], timing=r["timing"],
            status=r["status"], total_hosts=r["total_hosts"],
            hosts_reachable=r["hosts_reachable"],
            open_ports_found=r["open_ports_found"]
        ) for r in rows]


async def clear_history():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scan_history")
        await db.commit()