from __future__ import annotations

import http.client
import json
import os
import subprocess
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env()

PROXY_HOST = os.getenv("SEARXNG_PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("SEARXNG_PROXY_PORT", "18081"))
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = int(os.getenv("SEARXNG_BACKEND_PORT", "18080"))
IDLE_TIMEOUT = int(os.getenv("SEARXNG_IDLE_TIMEOUT_SECONDS", "300"))
WAKE_TIMEOUT = int(os.getenv("SEARXNG_WAKE_TIMEOUT_SECONDS", "120"))
SEARCH_TIMEOUT = int(os.getenv("SEARXNG_SEARCH_TIMEOUT_SECONDS", "120"))

state_lock = threading.Lock()
wake_lock = threading.Lock()
last_activity = time.monotonic()
active_requests = 0

HOP_REQUEST_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
HOP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
}


def log(message: str) -> None:
    print(f"searxng-wake: {message}", flush=True)


def compose(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    command = ["docker", "compose", "-f", str(ROOT / "docker-compose.yml"), *args]
    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def backend_healthy(timeout: float = 0.5) -> bool:
    connection = None
    try:
        connection = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=timeout)
        connection.request("GET", "/healthz")
        response = connection.getresponse()
        response.read()
        return 200 <= response.status < 300
    except Exception:
        return False
    finally:
        if connection is not None:
            connection.close()


def ensure_docker() -> None:
    active = subprocess.run(
        ["systemctl", "is-active", "--quiet", "docker"],
        capture_output=True,
        text=True,
    )
    if active.returncode == 0:
        return
    subprocess.run(
        ["sudo", "-n", "systemctl", "start", "docker.service"],
        check=True,
    )


def wake_backend() -> None:
    if backend_healthy():
        return
    with wake_lock:
        if backend_healthy():
            return
        log("starting backend")
        ensure_docker()
        result = compose("up", "-d", "--wait", "--wait-timeout", str(WAKE_TIMEOUT))
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        deadline = time.monotonic() + WAKE_TIMEOUT
        while time.monotonic() < deadline:
            if backend_healthy():
                log("backend ready")
                return
            time.sleep(0.2)
        raise RuntimeError("backend did not become healthy")


def compose_has_containers() -> bool:
    result = compose("ps", "-q")
    return bool(result.stdout.strip())


def idle_worker() -> None:
    global active_requests
    while True:
        time.sleep(5)
        with state_lock:
            idle = time.monotonic() - last_activity
            active = active_requests
        if idle < IDLE_TIMEOUT or active > 0:
            continue
        with wake_lock:
            with state_lock:
                idle = time.monotonic() - last_activity
                active = active_requests
            if idle < IDLE_TIMEOUT or active > 0 or not compose_has_containers():
                continue
            log(f"idle for {int(idle)}s; stopping backend")
            compose("stop")


def begin_request() -> None:
    global active_requests
    with state_lock:
        last_activity = time.monotonic()
        active_requests += 1


def end_request() -> None:
    global active_requests
    with state_lock:
        active_requests -= 1


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "searxng-wake"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        log(f"{self.address_string()} {format % args}")

    def send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> bytes:
        raw_length = self.headers.get("Content-Length")
        if not raw_length:
            return b""
        length = int(raw_length)
        return self.rfile.read(length) if length > 0 else b""

    def proxy(self) -> None:
        begin_request()
        try:
            wake_backend()
            parsed = urllib.parse.urlsplit(self.path)
            target = parsed.path or "/"
            if parsed.query:
                target = f"{target}?{parsed.query}"
            body = self.read_body()
            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in HOP_REQUEST_HEADERS and key.lower() != "host"
            }
            headers["Host"] = f"{BACKEND_HOST}:{BACKEND_PORT}"
            connection = http.client.HTTPConnection(
                BACKEND_HOST,
                BACKEND_PORT,
                timeout=SEARCH_TIMEOUT,
            )
            try:
                connection.request(
                    self.command,
                    target,
                    body=body or None,
                    headers=headers,
                )
                response = connection.getresponse()
                response_body = response.read()
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() not in HOP_RESPONSE_HEADERS:
                        self.send_header(key, value)
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            finally:
                connection.close()
        except Exception as exc:
            log(f"request failed: {exc}")
            self.send_json(502, {"error": str(exc)})
        finally:
            end_request()

    def do_GET(self) -> None:
        if urllib.parse.urlsplit(self.path).path == "/wake":
            begin_request()
            try:
                wake_backend()
                self.send_json(200, {"status": "awake"})
            except Exception as exc:
                log(f"wake failed: {exc}")
                self.send_json(503, {"error": str(exc)})
            finally:
                end_request()
            return
        self.proxy()

    def do_POST(self) -> None:
        self.proxy()

    def do_PUT(self) -> None:
        self.proxy()

    def do_PATCH(self) -> None:
        self.proxy()

    def do_DELETE(self) -> None:
        self.proxy()

    def do_OPTIONS(self) -> None:
        self.proxy()

    def do_HEAD(self) -> None:
        self.proxy()


def main() -> None:
    threading.Thread(target=idle_worker, name="searxng-idle", daemon=True).start()
    server = ThreadingHTTPServer((PROXY_HOST, PROXY_PORT), Handler)
    server.daemon_threads = True
    log(f"listening on http://{PROXY_HOST}:{PROXY_PORT}")
    log(f"backend on http://{BACKEND_HOST}:{BACKEND_PORT}")
    log(f"idle timeout {IDLE_TIMEOUT}s")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
