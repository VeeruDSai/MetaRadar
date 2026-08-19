#!/usr/bin/env python3
"""
MetaRadar Unified Orchestration & Process Launcher (start.py)
Starts backing services, host FastAPI backend, and Next.js frontend with live telemetry and graceful shutdown.

Usage:
    python start.py [OPTIONS]

Options:
    --no-frontend         Start only the backend API server
    --no-backend          Start only the Next.js frontend
    --no-docker           Skip starting Docker backing services (Postgres, Redis)
    --port-backend PORT   Port for FastAPI backend (default: 8000)
    --port-frontend PORT  Port for Next.js frontend (default: 3000)
    --daemon              Run processes in daemon mode without terminal status loop
    --help, -h            Show help message and exit
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"

# Global list of active child processes for cleanup
active_processes: list[subprocess.Popen] = []


def signal_handler(sig, frame):
    print("\n\n[SHUTDOWN] Received termination signal. Stopping all child processes...")
    cleanup_processes()
    print("[SHUTDOWN] All services stopped cleanly. Exiting.")
    sys.exit(0)


def cleanup_processes():
    for proc in active_processes:
        if proc.poll() is None:
            if sys.platform == "win32":
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        capture_output=True,
                        check=False,
                    )
                except Exception:
                    pass
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def print_recent_logs(log_path: Path, service_name: str, max_lines: int = 15):
    if not log_path.exists():
        return
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = lines[-max_lines:] if len(lines) > max_lines else lines
        if tail:
            print(f"\n--- [DIAGNOSTIC] Recent logs from {service_name} ({log_path.name}) ---", file=sys.stderr)
            for line in tail:
                print(f"  {line}", file=sys.stderr)
            print("-" * 60, file=sys.stderr)
    except Exception:
        pass


import socket


def check_socket_ready(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def free_port_if_in_use(port: int, service_name: str):
    """
    If a port is already occupied (e.g. lingering process from previous run),
    attempt to terminate the holding process so the new service instance can bind cleanly.
    """
    if not check_socket_ready("127.0.0.1", port, timeout=0.3):
        return

    print(f"  [PORT CHECK] Port {port} ({service_name}) is already in use. Cleaning up lingering process...")
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.stdout:
                for line in res.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.strip().split()
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) != os.getpid():
                            print(f"  [PORT CLEANUP] Terminating lingering process PID {pid} on port {port}...")
                            subprocess.run(
                                ["taskkill", "/F", "/T", "/PID", pid],
                                capture_output=True,
                                check=False,
                            )
        except Exception as e:
            print(f"  [WARNING] Could not free port {port}: {e}", file=sys.stderr)
    else:
        try:
            res = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.stdout:
                for pid in res.stdout.strip().splitlines():
                    if pid.isdigit() and int(pid) != os.getpid():
                        print(f"  [PORT CLEANUP] Terminating lingering process PID {pid} on port {port}...")
                        subprocess.run(["kill", "-9", pid], capture_output=True, check=False)
        except Exception as e:
            print(f"  [WARNING] Could not free port {port}: {e}", file=sys.stderr)

    time.sleep(0.8)


def wait_for_backing_service(host: str, port: int, service_name: str, max_retries: int = 15, delay: float = 1.0) -> bool:
    for i in range(max_retries):
        if check_socket_ready(host, port):
            print(f"  [READY] {service_name} online on {host}:{port}.")
            return True
        time.sleep(delay)
    print(f"  [WARNING] {service_name} on {host}:{port} was not ready after {max_retries * delay}s.", file=sys.stderr)
    return False


def start_docker_services(skip_docker: bool):
    if skip_docker:
        return

    docker_cmd = shutil.which("docker")
    if not docker_cmd:
        print("  [INFO] Docker executable not found in PATH. Checking direct backing port availability...")
        wait_for_backing_service("127.0.0.1", 5432, "PostgreSQL (port 5432)", max_retries=3, delay=0.5)
        wait_for_backing_service("127.0.0.1", 6379, "Redis (port 6379)", max_retries=3, delay=0.5)
        return

    # Check if Docker daemon is actually running and responding
    daemon_ready = False
    try:
        info_check = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=3)
        daemon_ready = (info_check.returncode == 0)
    except Exception:
        daemon_ready = False

    if not daemon_ready:
        print("  [INFO] Docker daemon is not active. Checking direct backing port availability...")
        wait_for_backing_service("127.0.0.1", 5432, "PostgreSQL (port 5432)", max_retries=3, delay=0.5)
        wait_for_backing_service("127.0.0.1", 6379, "Redis (port 6379)", max_retries=3, delay=0.5)
        return

    print("  [DOCKER] Ensuring backing databases (Postgres & Redis) are running...")
    try:
        res = subprocess.run(["docker", "compose", "up", "-d", "postgres", "redis"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if res.returncode != 0 and res.stderr:
            print(f"  [WARNING] Docker compose: {res.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"  [WARNING] Docker compose start: {e}", file=sys.stderr)

    # Wait for PostgreSQL and Redis to be accepting connections
    wait_for_backing_service("127.0.0.1", 5432, "PostgreSQL (port 5432)", max_retries=15, delay=1.0)
    wait_for_backing_service("127.0.0.1", 6379, "Redis (port 6379)", max_retries=15, delay=1.0)


def check_endpoint_health(url: str, timeout: float = 1.5) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MetaRadar-Launcher/5.1"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def start_backend(port: int) -> subprocess.Popen:
    backend_dir = BASE_DIR / "backend"
    log_file = LOGS_DIR / "backend.log"
    print(f"  [BACKEND] Starting FastAPI on http://localhost:{port} (logging to logs/backend.log)...")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)

    log_out = open(log_file, "a", encoding="utf-8")
    
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=str(backend_dir),
        env=env,
        stdout=log_out,
        stderr=subprocess.STDOUT,
    )
    active_processes.append(proc)
    return proc


def start_frontend(port: int, backend_port: int = 8000) -> subprocess.Popen:
    frontend_dir = BASE_DIR / "frontend"
    log_file = LOGS_DIR / "frontend.log"
    npm_cmd = shutil.which("npm") or "npm"
    print(f"  [FRONTEND] Starting Next.js 16 on http://localhost:{port} (logging to logs/frontend.log)...")

    env = os.environ.copy()
    env["NEXT_PUBLIC_API_URL"] = f"http://localhost:{backend_port}/api/v1"

    log_out = open(log_file, "a", encoding="utf-8")

    cmd = [npm_cmd, "run", "dev", "--", "-p", str(port)]

    proc = subprocess.Popen(
        cmd,
        cwd=str(frontend_dir),
        env=env,
        stdout=log_out,
        stderr=subprocess.STDOUT,
    )
    active_processes.append(proc)
    return proc


def main():
    parser = argparse.ArgumentParser(
        description="MetaRadar v5.1 Production Process Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--no-frontend", action="store_true", help="Start only the backend API server")
    parser.add_argument("--no-backend", action="store_true", help="Start only the Next.js frontend")
    parser.add_argument("--no-docker", action="store_true", help="Skip starting Docker backing services")
    parser.add_argument("--port-backend", type=int, default=8000, help="Port for FastAPI backend (default: 8000)")
    parser.add_argument("--port-frontend", type=int, default=3000, help="Port for Next.js frontend (default: 3000)")
    parser.add_argument("--daemon", action="store_true", help="Run processes in daemon mode without status loop")

    args = parser.parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Ensure logs directory
    LOGS_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print(" MetaRadar Decision Intelligence Platform — Process Launcher")
    print(" Version 5.1.0 | Fast In-Memory Pipelines (No Celery) | Local Gemma")
    print("=" * 70)

    # 1. Backing Services
    start_docker_services(args.no_docker)

    # 2. Launch Backend
    backend_proc = None
    if not args.no_backend:
        free_port_if_in_use(args.port_backend, "FastAPI Backend")
        backend_proc = start_backend(args.port_backend)

    # 3. Launch Frontend
    frontend_proc = None
    if not args.no_frontend:
        free_port_if_in_use(args.port_frontend, "Next.js Frontend")
        frontend_proc = start_frontend(args.port_frontend, args.port_backend)

    print("\n" + "-" * 70)
    print(f" Services launched. Press Ctrl+C to terminate all processes.")
    print("-" * 70)

    if args.daemon:
        print(" Running in daemon mode. Outputting to logs/.")
        return

    # Live telemetry display loop
    backend_url = f"http://localhost:{args.port_backend}/api/v1/health"
    frontend_url = f"http://localhost:{args.port_frontend}"

    iteration = 0
    try:
        while True:
            time.sleep(3)
            iteration += 1

            # Check process lifespans
            if backend_proc and backend_proc.poll() is not None:
                print(f"\n  [ERROR] Backend process exited unexpectedly with code {backend_proc.returncode}!", file=sys.stderr)
                print_recent_logs(LOGS_DIR / "backend.log", "FastAPI Backend")
                cleanup_processes()
                sys.exit(1)
            if frontend_proc and frontend_proc.poll() is not None:
                print(f"\n  [ERROR] Frontend process exited unexpectedly with code {frontend_proc.returncode}!", file=sys.stderr)
                print_recent_logs(LOGS_DIR / "frontend.log", "Next.js Frontend")
                cleanup_processes()
                sys.exit(1)

            b_ok = check_endpoint_health(backend_url) if backend_proc else None
            f_ok = check_endpoint_health(frontend_url) if frontend_proc else None

            b_status = "ONLINE (200 OK)" if b_ok else ("STARTING..." if b_ok is False else "DISABLED")
            f_status = "ONLINE (200 OK)" if f_ok else ("STARTING..." if f_ok is False else "DISABLED")

            if iteration % 3 == 0:
                print(f"  [TELEMETRY] Backend: {b_status} | Frontend: {f_status} | Active PID(s): {[p.pid for p in active_processes]}")

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
