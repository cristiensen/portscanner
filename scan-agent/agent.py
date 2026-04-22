import asyncio
import socket
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading


async def check_port(host: str, port: int, timeout: float) -> dict:
    start = time.monotonic()
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return {"state": "open", "latency_ms": round((time.monotonic() - start) * 1000, 2)}
    except asyncio.TimeoutError:
        return {"state": "timeout", "latency_ms": round((time.monotonic() - start) * 1000, 2)}
    except ConnectionRefusedError:
        return {"state": "refused", "latency_ms": round((time.monotonic() - start) * 1000, 2)}
    except OSError:
        return {"state": "unreachable", "latency_ms": None}
    except Exception as e:
        return {"state": "error", "latency_ms": None, "reason": str(e)}


async def check_host(host: str, timeout: float) -> dict:
    ping_timeout_ms = max(int(timeout * 1000), 250)

    try:
        proc = await asyncio.create_subprocess_exec(
            "ping",
            "-n", "1",
            "-w", str(ping_timeout_ms),
            host,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        ping_rc = await asyncio.wait_for(proc.wait(), timeout=timeout + 1.0)
        if ping_rc == 0:
            return {"alive": True}
    except Exception:
        pass

    probe_ports = [80, 443, 22, 3389, 445, 8080, 135]

    async def probe(port: int) -> str:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            return "open"
        except asyncio.TimeoutError:
            return "timeout"
        except ConnectionRefusedError:
            return "refused"
        except Exception:
            return "error"

    outcomes = await asyncio.gather(*[probe(p) for p in probe_ports])
    alive = any(o in ("open", "refused") for o in outcomes)
    return {"alive": alive}


async def handle_request(body: dict) -> dict:
    action = body.get("action")
    host = body.get("host")
    timeout = body.get("timeout", 2.0)

    if action == "check_host":
        return await check_host(host, timeout)
    elif action == "check_port":
        port = body.get("port")
        return await check_port(host, port, timeout)
    else:
        return {"error": f"Unknown action: {action}"}


class AgentHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        result = asyncio.run(handle_request(body))
        response = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9000), AgentHandler)
    print("Scan agent listening on port 9000")
    print("Keep this window open while using PortScanner.")
    server.serve_forever()
