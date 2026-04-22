from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import uuid

class TimingProfile(str, Enum):
    safe = "safe"
    balanced = "balanced"
    fast = "fast"

class ScanPreset(str, Enum):
    quick = "quick"
    common = "common"
    custom = "custom"
    discovery = "discovery"

class PortState(str, Enum):
    open = "open"
    closed = "closed"
    timeout = "timeout"
    unreachable = "unreachable"
    error = "error"
    reachable = "reachable"
    host_down = "host_down"

class ScanStatus(str, Enum):
    idle = "idle"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"
    error = "error"

class ScanConfig(BaseModel):
    targets: str = Field(..., description="Targets: IP, hostname, CIDR, or range")
    ports: str = Field(..., description="Ports: single, list, range, or combo")
    timing: TimingProfile = TimingProfile.balanced
    preset: ScanPreset = ScanPreset.custom
    host_discovery: bool = True
    banner_grab: bool = False
    scan_id: Optional[str] = None

class PortResult(BaseModel):
    scan_id: str
    host_input: str
    host_ip: str
    hostname: Optional[str] = None
    port: int
    protocol: str = "tcp"
    state: PortState
    latency_ms: Optional[float] = None
    service: Optional[str] = None
    banner: Optional[str] = None
    timestamp: str
    error_reason: Optional[str] = None

class ScanProgress(BaseModel):
    scan_id: str
    status: ScanStatus
    total_hosts: int
    total_ports: int
    hosts_completed: int
    ports_checked: int
    open_ports_found: int
    elapsed_seconds: float
    current_host: Optional[str] = None
    current_port: Optional[int] = None
    estimated_remaining_seconds: Optional[float] = None

class ScanSummary(BaseModel):
    scan_id: str
    status: ScanStatus
    targets: str
    ports: str
    timing: str
    started_at: str
    finished_at: Optional[str] = None
    total_hosts: int
    hosts_reachable: int
    open_ports_found: int

class PresetModel(BaseModel):
    id: Optional[str] = None
    name: str
    targets: str = ""
    ports: str = ""
    timing: TimingProfile = TimingProfile.balanced
    host_discovery: bool = True
    banner_grab: bool = False
    preset_type: ScanPreset = ScanPreset.custom

class HistoryEntry(BaseModel):
    id: str
    scan_id: str
    started_at: str
    finished_at: Optional[str]
    targets: str
    ports: str
    timing: str
    status: str
    total_hosts: int
    hosts_reachable: int
    open_ports_found: int

COMMON_SERVICES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    67: "DHCP", 68: "DHCP", 69: "TFTP", 80: "HTTP", 110: "POP3",
    111: "RPC", 119: "NNTP", 123: "NTP", 135: "MS-RPC", 137: "NetBIOS",
    138: "NetBIOS", 139: "NetBIOS", 143: "IMAP", 161: "SNMP", 162: "SNMP",
    389: "LDAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS", 514: "Syslog",
    587: "SMTP", 636: "LDAPS", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL",
    1521: "Oracle", 2049: "NFS", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
    8888: "HTTP-Alt", 9200: "Elasticsearch", 27017: "MongoDB",
}

PRESET_PORTS = {
    ScanPreset.quick: "22,80,443,3389,8080",
    ScanPreset.common: "21,22,23,25,53,80,110,135,139,143,443,445,993,995,1433,3306,3389,5432,5900,8080,8443",
    ScanPreset.discovery: "",
    ScanPreset.custom: "",
}

TIMING_SETTINGS = {
    TimingProfile.safe: {"concurrency": 10, "timeout": 3.0, "retries": 1},
    TimingProfile.balanced: {"concurrency": 50, "timeout": 2.0, "retries": 1},
    TimingProfile.fast: {"concurrency": 150, "timeout": 1.0, "retries": 0},
}