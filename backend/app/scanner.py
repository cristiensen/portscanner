import asyncio
import ipaddress
import socket
import time
import uuid
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional, Tuple
from .models import (
    PortResult, PortState, ScanConfig, ScanProgress, ScanStatus,
    ScanSummary, COMMON_SERVICES, TIMING_SETTINGS, PRESET_PORTS, ScanPreset
)
import urllib.request
import urllib.error

AGENT_URL = "http://host.docker.internal:9000"

def _call_agent(payload: dict) -> dict:
    """Call the Windows scan agent synchronously."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        AGENT_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

async def _call_agent_async(payload: dict) -> dict:
    """Call the Windows scan agent from async context."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _call_agent, payload)

_active_scans: dict[str, asyncio.Task] = {}
_scan_results: dict[str, list] = {}
_scan_progress: dict[str, ScanProgress] = {}
_scan_summaries: dict[str, ScanSummary] = {}
_cancel_flags: dict[str, asyncio.Event] = {}

def parse_targets(raw: str) -> List[str]:

    targets = []
    parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]

    if not parts:
        raise ValueError("No targets entered.")

    for part in parts:
        if "/" in part:
            try:
                net = ipaddress.IPv4Network(part, strict=False)
            except ValueError:
                raise ValueError(
                    f'"{part}" is not a valid CIDR range. '
                    f'Example: 192.168.1.0/24'
                )
            if net.num_addresses > 1024:
                raise ValueError(
                    f"{part} contains {net.num_addresses:,} hosts. "
                    f"Maximum allowed is 1024. Use /22 or smaller."
                )
            targets.extend(str(ip) for ip in net.hosts())

        elif "-" in part:
            segments = part.split("-", 1)
            start_str = segments[0].strip()
            end_str = segments[1].strip()

            try:
                start_ip = ipaddress.IPv4Address(start_str)
            except ValueError:
                raise ValueError(
                    f'"{start_str}" is not a valid IPv4 address '
                    f'(left side of range "{part}").'
                )

            if "." not in end_str:
                prefix = ".".join(start_str.split(".")[:-1])
                end_str = f"{prefix}.{end_str}"

            try:
                end_ip = ipaddress.IPv4Address(end_str)
            except ValueError:
                raise ValueError(
                    f'"{end_str}" is not a valid IPv4 address '
                    f'(right side of range "{part}").'
                )

            if start_ip > end_ip:
                raise ValueError(
                    f"Range start {start_ip} is greater than end {end_ip}. "
                    f"The lower address must come first."
                )

            count = int(end_ip) - int(start_ip) + 1
            if count > 1024:
                raise ValueError(
                    f"Range {part} contains {count:,} hosts. "
                    f"Maximum allowed is 1024."
                )
            targets.extend(
                str(ipaddress.IPv4Address(int(start_ip) + i))
                for i in range(count)
            )

        else:
            try:
                ipaddress.IPv4Address(part)
            except ValueError:
                raise ValueError(
                    f'"{part}" is not a valid IPv4 address. '
                    f'Only IPv4 addresses, ranges (e.g. 10.0.0.1-10.0.0.50), '
                    f'and CIDR subnets (e.g. 192.168.1.0/24) are accepted. '
                    f'Hostnames are not supported.'
                )
            targets.append(part)

    if not targets:
        raise ValueError("No valid targets found.")

    return targets


def parse_ports(raw: str) -> List[int]:
    """Parse port string into sorted deduplicated list of port numbers."""
    if not raw.strip():
        return []

    ports = set()
    parts = [p.strip() for p in raw.split(",") if p.strip()]

    for part in parts:
        if "-" in part:
            bounds = part.split("-")
            if len(bounds) != 2:
                raise ValueError(f"Invalid port range: {part}")
            start, end = int(bounds[0].strip()), int(bounds[1].strip())
            if not (1 <= start <= 65535 and 1 <= end <= 65535):
                raise ValueError(f"Port numbers must be between 1 and 65535. Got: {part}")
            if start > end:
                raise ValueError(f"Port range start {start} is greater than end {end}")
            ports.update(range(start, end + 1))
        else:
            p = int(part)
            if not 1 <= p <= 65535:
                raise ValueError(f"Port {p} is out of valid range (1-65535)")
            ports.add(p)

    return sorted(ports)


def validate_scan_config(config: ScanConfig) -> Tuple[List[str], List[int]]:
    """Validate and parse scan config. Returns (targets, ports) or raises ValueError."""
    if not config.targets.strip():
        raise ValueError("Target field cannot be empty.")

    targets = parse_targets(config.targets)

    if config.preset != ScanPreset.custom and config.preset != ScanPreset.discovery:
        port_str = PRESET_PORTS[config.preset]
    else:
        port_str = config.ports

    if config.preset == ScanPreset.discovery:
        ports = []
    elif not port_str.strip():
        raise ValueError("Port field cannot be empty. Enter ports like: 22,80,443 or 1-1024")
    else:
        ports = parse_ports(port_str)

    if len(targets) * max(len(ports), 1) > 100_000:
        raise ValueError(
            f"Scan scope is very large ({len(targets)} hosts × {len(ports)} ports = "
            f"{len(targets) * len(ports):,} combinations). "
            f"Please reduce the target or port range."
        )

    return targets, ports

async def check_host_alive(host: str, timeout: float) -> Tuple[bool, Optional[str]]:
    """Ask the Windows scan agent whether a host is alive."""
    resolved = None
    try:
        info = await asyncio.get_event_loop().getaddrinfo(
            host, None, family=socket.AF_INET
        )
        if info:
            resolved = info[0][4][0]
    except Exception:
        return False, None

    target = resolved or host
    result = await _call_agent_async({"action": "check_host", "host": target, "timeout": timeout})
    return result.get("alive", False), resolved

async def check_port(
    host: str,
    port: int,
    scan_id: str,
    timeout: float,
    banner_grab: bool,
    host_input: str,
    hostname: Optional[str],
) -> PortResult:
    """Ask the Windows scan agent to check a single port."""
    ts = datetime.now(timezone.utc).isoformat()
    service = COMMON_SERVICES.get(port)

    result = await _call_agent_async({
        "action": "check_port",
        "host": host,
        "port": port,
        "timeout": timeout,
    })

    agent_state = result.get("state", "error")
    state_map = {
        "open": PortState.open,
        "timeout": PortState.timeout,
        "refused": PortState.closed,
        "unreachable": PortState.unreachable,
        "error": PortState.error,
    }
    state = state_map.get(agent_state, PortState.error)

    return PortResult(
        scan_id=scan_id,
        host_input=host_input,
        host_ip=host,
        hostname=hostname,
        port=port,
        protocol="tcp",
        state=state,
        latency_ms=result.get("latency_ms"),
        service=service,
        banner=None,
        timestamp=ts,
        error_reason=result.get("reason"),
    )


async def run_scan(config: ScanConfig) -> str:
    """Start a scan. Returns scan_id immediately; scan runs in background."""
    scan_id = config.scan_id or str(uuid.uuid4())
    config.scan_id = scan_id

    targets, ports = validate_scan_config(config)
    timing = TIMING_SETTINGS[config.timing]
    concurrency = timing["concurrency"]
    timeout = timing["timeout"]

    now = datetime.now(timezone.utc).isoformat()
    total_ports = len(ports) if ports else 0
    total_combos = len(targets) * max(total_ports, 1)

    _scan_results[scan_id] = []
    _cancel_flags[scan_id] = asyncio.Event()
    _scan_summaries[scan_id] = ScanSummary(
        scan_id=scan_id,
        status=ScanStatus.running,
        targets=config.targets,
        ports=config.ports,
        timing=config.timing.value,
        started_at=now,
        total_hosts=len(targets),
        hosts_reachable=0,
        open_ports_found=0,
    )
    _scan_progress[scan_id] = ScanProgress(
        scan_id=scan_id,
        status=ScanStatus.running,
        total_hosts=len(targets),
        total_ports=total_ports,
        hosts_completed=0,
        ports_checked=0,
        open_ports_found=0,
        elapsed_seconds=0,
        current_host=None,
        current_port=None,
    )

    task = asyncio.create_task(_scan_worker(
        scan_id, targets, ports, config, timing, concurrency, timeout
    ))
    _active_scans[scan_id] = task
    return scan_id


async def _scan_worker(
    scan_id: str,
    targets: List[str],
    ports: List[int],
    config: ScanConfig,
    timing: dict,
    concurrency: int,
    timeout: float,
):
    """Background worker that performs the actual scan."""
    cancel = _cancel_flags[scan_id]
    progress = _scan_progress[scan_id]
    results = _scan_results[scan_id]
    semaphore = asyncio.Semaphore(concurrency)
    start_time = time.monotonic()
    hosts_reachable = 0

    try:
        for host_idx, host_input in enumerate(targets):
            if cancel.is_set():
                break

            # Resolve hostname
            resolved_ip = host_input
            hostname = None
            try:
                info = await asyncio.get_event_loop().getaddrinfo(
                    host_input, None, family=socket.AF_INET
                )
                if info:
                    resolved_ip = info[0][4][0]
                    if resolved_ip != host_input:
                        hostname = host_input
            except Exception:
                pass

            progress.current_host = host_input
            elapsed = time.monotonic() - start_time

            host_alive = True
            should_check_host_alive = config.preset == ScanPreset.discovery or (
                config.host_discovery and bool(ports)
            )
            if should_check_host_alive:
                alive, _ = await check_host_alive(resolved_ip, timeout)
                host_alive = alive

            if not ports:
                state = PortState.reachable if host_alive else PortState.host_down
                result = PortResult(
                    scan_id=scan_id,
                    host_input=host_input,
                    host_ip=resolved_ip,
                    hostname=hostname,
                    port=0,
                    protocol="icmp-sim",
                    state=state,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                results.append(result.model_dump())
                if host_alive:
                    hosts_reachable += 1
                    _scan_summaries[scan_id].hosts_reachable = hosts_reachable
                progress.hosts_completed += 1
                progress.ports_checked += 1
                progress.elapsed_seconds = round(time.monotonic() - start_time, 1)
                continue

            if not host_alive:
                for port in ports:
                    if cancel.is_set():
                        break
                    result = PortResult(
                        scan_id=scan_id,
                        host_input=host_input,
                        host_ip=resolved_ip,
                        hostname=hostname,
                        port=port,
                        protocol="tcp",
                        state=PortState.unreachable,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                    results.append(result.model_dump())
                    progress.ports_checked += 1
                progress.hosts_completed += 1
                progress.elapsed_seconds = round(time.monotonic() - start_time, 1)
                continue

            if host_alive:
                hosts_reachable += 1
                _scan_summaries[scan_id].hosts_reachable = hosts_reachable

            async def scan_one(port: int):
                if cancel.is_set():
                    return
                async with semaphore:
                    if cancel.is_set():
                        return
                    result = await check_port(
                        resolved_ip, port, scan_id, timeout,
                        config.banner_grab, host_input, hostname
                    )
                    results.append(result.model_dump())
                    progress.ports_checked += 1
                    progress.current_port = port
                    if result.state == PortState.open:
                        progress.open_ports_found += 1
                        _scan_summaries[scan_id].open_ports_found = progress.open_ports_found
                    progress.elapsed_seconds = round(time.monotonic() - start_time, 1)

            await asyncio.gather(*[scan_one(port) for port in ports])
            progress.hosts_completed += 1
            progress.elapsed_seconds = round(time.monotonic() - start_time, 1)

        final_status = ScanStatus.cancelled if cancel.is_set() else ScanStatus.completed
        progress.status = final_status
        _scan_summaries[scan_id].status = final_status
        _scan_summaries[scan_id].finished_at = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        progress.status = ScanStatus.error
        _scan_summaries[scan_id].status = ScanStatus.error
        _scan_summaries[scan_id].finished_at = datetime.now(timezone.utc).isoformat()

    finally:
        _active_scans.pop(scan_id, None)

def cancel_scan(scan_id: str) -> bool:
    """Signal a running scan to stop. Returns True if scan was found."""
    if scan_id in _cancel_flags:
        _cancel_flags[scan_id].set()
        return True
    return False

def get_progress(scan_id: str) -> Optional[ScanProgress]:
    return _scan_progress.get(scan_id)

def get_results(scan_id: str) -> Optional[list]:
    return _scan_results.get(scan_id)

def get_summary(scan_id: str) -> Optional[ScanSummary]:
    return _scan_summaries.get(scan_id)

def is_scan_done(scan_id: str) -> bool:
    if scan_id not in _scan_progress:
        return True
    return _scan_progress[scan_id].status in (
        ScanStatus.completed, ScanStatus.cancelled, ScanStatus.error
    )
