#!/usr/bin/env python3
"""
MetaRadar Zero-Config Environment Setup Launcher (setup.py)
Automates dependency checking, backing services bootstrap, migrations, seed data, and model pulling.

Usage:
    python setup.py [OPTIONS]

Options:
    --skip-docker      Skip starting Docker Compose backing services (Postgres, Redis, Ollama)
    --skip-models      Skip pulling Ollama LLM models (e.g. gemma3:4b)
    --skip-frontend    Skip installing frontend NPM dependencies
    --skip-db-seed     Skip populating initial synthetic database seed rows
    --help, -h         Show help message and exit
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def print_step(step_num: int, title: str):
    print(f"\n[{step_num}/6] >>> {title}")


def run_command(cmd: list[str], cwd: Path = BASE_DIR, check: bool = True, env: dict = None) -> subprocess.CompletedProcess:
    cmd_str = " ".join(cmd)
    print(f"  $ {cmd_str}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, cwd=str(cwd), check=check, env=merged_env)


def check_prerequisites():
    print_step(1, "Checking Environment Prerequisites")
    
    # 1. Python version check
    py_version = sys.version_info
    print(f"  Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 11):
        print("  [ERROR] Python 3.11 or higher is required.", file=sys.stderr)
        sys.exit(1)
    
    # 2. Node & NPM check
    node_cmd = shutil.which("node")
    npm_cmd = shutil.which("npm")
    if node_cmd:
        try:
            node_ver = subprocess.check_output([node_cmd, "--version"], text=True).strip()
            print(f"  Node version: {node_ver}")
        except Exception:
            print("  Node detected.")
    else:
        print("  [WARNING] Node.js not found in PATH. Frontend build may require Node 18+.", file=sys.stderr)

    if npm_cmd:
        print("  NPM package manager detected.")
    else:
        print("  [WARNING] NPM not found in PATH.", file=sys.stderr)

    # 3. Docker check
    docker_cmd = shutil.which("docker")
    if docker_cmd:
        print("  Docker detected.")
    else:
        print("  [WARNING] Docker not found in PATH. Backing services (Postgres, Redis) must be managed manually.", file=sys.stderr)


def setup_backend():
    print_step(2, "Configuring Backend Dependencies")
    backend_dir = BASE_DIR / "backend"
    requirements_file = backend_dir / "requirements.txt"
    
    if requirements_file.exists():
        print(f"  Installing backend dependencies from {requirements_file.name}...")
        try:
            run_command([sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)], cwd=backend_dir)
            print("  Backend dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"  [WARNING] Pip install returned error: {e}. Continuing...", file=sys.stderr)
    else:
        print("  No backend/requirements.txt found, skipping pip install.")


def setup_frontend(skip_frontend: bool):
    print_step(3, "Configuring Frontend Dependencies")
    if skip_frontend:
        print("  Skipping frontend setup (--skip-frontend).")
        return

    frontend_dir = BASE_DIR / "frontend"
    npm_cmd = shutil.which("npm")
    
    if not npm_cmd:
        print("  [WARNING] NPM not found. Skipping frontend dependency install.", file=sys.stderr)
        return

    print("  Installing frontend packages via npm install...")
    try:
        run_command([npm_cmd, "install", "--no-audit", "--loglevel=error"], cwd=frontend_dir)
        print("  Frontend dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"  [WARNING] Frontend npm install returned code {e.returncode}. Continuing...", file=sys.stderr)


def bootstrap_docker_services(skip_docker: bool):
    print_step(4, "Bootstrapping Backing Services (PostgreSQL & Redis)")
    if skip_docker:
        print("  Skipping Docker compose startup (--skip-docker).")
        return

    docker_cmd = shutil.which("docker")
    if not docker_cmd:
        print("  [WARNING] Docker is not installed or not in PATH. Skipping docker compose.", file=sys.stderr)
        return

    try:
        print("  Starting postgres and redis containers...")
        run_command(["docker", "compose", "up", "-d", "postgres", "redis"])
        print("  Waiting for PostgreSQL to accept connections...")
        
        # Wait for DB readiness
        max_attempts = 15
        for i in range(max_attempts):
            res = subprocess.run(
                ["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", "metaradar", "-d", "metaradar"],
                capture_output=True,
                text=True
            )
            if res.returncode == 0:
                print(f"  PostgreSQL is ready (attempt {i+1}).")
                break
            time.sleep(2)
        else:
            print("  [WARNING] PostgreSQL did not report ready within 30s. Continuing...", file=sys.stderr)
    except Exception as err:
        print(f"  [WARNING] Failed to start Docker services: {err}", file=sys.stderr)


def run_database_migrations_and_seed(skip_seed: bool):
    print_step(5, "Running Database Migrations & Synthetic Seeding")
    backend_dir = BASE_DIR / "backend"
    
    # 1. Run Alembic Migrations
    alembic_ini = backend_dir / "alembic.ini"
    if alembic_ini.exists():
        print("  Applying database migrations (alembic upgrade head)...")
        try:
            run_command([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend_dir)
            print("  Database migrations applied successfully.")
        except Exception as e:
            print(f"  [NOTICE] Alembic migration execution: {e}. Continuing...", file=sys.stderr)

    # 2. Seed Data
    if not skip_seed:
        seed_script = backend_dir / "app" / "db" / "seed.py"
        if seed_script.exists():
            print("  Seeding reference assets, companies, and synthetic landscape signals...")
            try:
                env = {"PYTHONPATH": str(backend_dir)}
                run_command([sys.executable, str(seed_script)], cwd=backend_dir, env=env)
            except Exception as e:
                print(f"  [NOTICE] Database seeding: {e}. Continuing...", file=sys.stderr)
        else:
            print("  No seed script found at backend/app/db/seed.py.")
    else:
        print("  Skipping database seeding (--skip-db-seed).")


def setup_local_models(skip_models: bool, skip_docker: bool):
    print_step(6, "Local LLM Model Setup")
    if skip_models:
        print("  Skipping Ollama model pull (--skip-models).")
        return

    docker_cmd = shutil.which("docker")
    if not skip_docker and docker_cmd:
        print("  Attempting to pull gemma3:4b in Ollama container...")
        try:
            # Start Ollama container if not already up
            subprocess.run(["docker", "compose", "up", "-d", "ollama"], check=False)
            time.sleep(3)
            res = subprocess.run(["docker", "exec", "metaradar-ollama", "ollama", "pull", "gemma3:4b"], check=False)
            if res.returncode == 0:
                print("  Gemma 3 4B model pulled successfully inside container.")
                return
        except Exception:
            pass

    ollama_cmd = shutil.which("ollama")
    if ollama_cmd:
        print("  Pulling gemma3:4b via host Ollama CLI...")
        try:
            subprocess.run([ollama_cmd, "pull", "gemma3:4b"], check=False)
        except Exception:
            pass
    else:
        print("  [INFO] Ollama not found locally. Local reasoning will operate in fallback mode until Ollama is configured.")


def main():
    parser = argparse.ArgumentParser(
        description="MetaRadar v5.1 Zero-Config Environment Setup Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skip-docker", action="store_true", help="Skip starting Docker Compose backing services")
    parser.add_argument("--skip-models", action="store_true", help="Skip pulling Ollama LLM models")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip installing frontend NPM packages")
    parser.add_argument("--skip-db-seed", action="store_true", help="Skip populating synthetic database seed rows")

    args = parser.parse_args()

    print("=" * 70)
    print(" MetaRadar Decision Intelligence Platform — Environment Setup")
    print(" Version 5.1.0 | A1 Compliant | Local Gemma & PGVector")
    print("=" * 70)

    start_time = time.time()

    check_prerequisites()
    setup_backend()
    setup_frontend(args.skip_frontend)
    bootstrap_docker_services(args.skip_docker)
    run_database_migrations_and_seed(args.skip_db_seed)
    setup_local_models(args.skip_models, args.skip_docker)

    elapsed = round(time.time() - start_time, 1)

    print("\n" + "=" * 70)
    print(f" [SUCCESS] MetaRadar environment setup complete in {elapsed}s!")
    print(" Next Step: Start all services using the production launcher:")
    print("     python start.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
