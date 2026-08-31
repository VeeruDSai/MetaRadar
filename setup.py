#!/usr/bin/env python3
"""
MetaRadar Zero-Config Environment Setup Launcher (setup.py)
Automates dependency checking, .env initialization, backing services bootstrap,
migrations, seed data, and model setup.

Usage:
    python setup.py [OPTIONS]

Options:
    --skip-docker      Skip starting Docker Compose backing services (Postgres, Redis)
    --skip-models      Skip pulling or downloading LLM models
    --skip-frontend    Skip installing frontend NPM dependencies
    --skip-db-seed     Skip populating initial synthetic database seed rows
    --skip-cuda        Skip CUDA-accelerated llama-cpp-python and use CPU-only version
    --download-model   Automatically download default local GGUF model into models/
    --api-key KEY      Provide xAI Grok API key for hosted reasoning
    --no-interactive   Disable interactive prompts
    --help, -h         Show help message and exit
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TOTAL_STEPS = 7


def print_step(step_num: int, title: str):
    print(f"\n[{step_num}/{TOTAL_STEPS}] >>> {title}")


def run_command(cmd: list[str], cwd: Path = BASE_DIR, check: bool = True, env: dict = None) -> subprocess.CompletedProcess:
    cmd_str = " ".join(cmd)
    print(f"  $ {cmd_str}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(cmd, cwd=str(cwd), check=check, env=merged_env)


def ensure_env_file():
    """Ensures .env exists; copies from .env.example if missing."""
    env_file = BASE_DIR / ".env"
    env_example = BASE_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("  [SUCCESS] Initialized .env configuration from .env.example template.")
    elif env_file.exists():
        print("  .env configuration file detected.")
    else:
        print("  [WARNING] Neither .env nor .env.example found.", file=sys.stderr)


def check_prerequisites():
    print_step(1, "Checking Environment Prerequisites & Configuration")

    # 1. Ensure .env exists
    ensure_env_file()

    # 2. Python version check
    py_version = sys.version_info
    print(f"  Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 11):
        print("  [ERROR] Python 3.11 or higher is required.", file=sys.stderr)
        sys.exit(1)

    # 3. Virtual environment check & recommendation
    in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ
    if in_venv:
        print("  Python virtual environment active.")
    else:
        print("  [TIP] Recommended: Run setup inside a Python virtual environment (e.g. python -m venv .venv).")

    # 4. Node & Package Manager check
    node_cmd = shutil.which("node")
    pnpm_cmd = shutil.which("pnpm")
    npm_cmd = shutil.which("npm")
    if node_cmd:
        try:
            node_ver = subprocess.check_output([node_cmd, "--version"], text=True).strip()
            print(f"  Node version: {node_ver}")
        except Exception:
            print("  Node detected.")
    else:
        print("  [WARNING] Node.js not found in PATH. Frontend build requires Node 20+.", file=sys.stderr)

    if pnpm_cmd:
        print("  pnpm package manager detected (preferred).")
    elif npm_cmd:
        print("  npm package manager detected.")
    else:
        print("  [WARNING] Neither pnpm nor npm found in PATH.", file=sys.stderr)

    # 5. Docker check
    docker_cmd = shutil.which("docker")
    if docker_cmd:
        print("  Docker detected.")
    else:
        print("  [WARNING] Docker not found in PATH. Backing services (Postgres, Redis) must be managed manually.", file=sys.stderr)

    # 6. CUDA / NVIDIA check
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            res = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                print(f"  NVIDIA GPU detected: {res.stdout.strip()}")
            else:
                print("  NVIDIA GPU: nvidia-smi found but returned no device info.")
        except Exception:
            print("  NVIDIA GPU: nvidia-smi present but query failed.")
    else:
        print("  NVIDIA GPU: nvidia-smi not in PATH. Will install CPU-only llama-cpp-python.")

    return nvidia_smi is not None


def setup_backend():
    print_step(2, "Configuring Backend Python Dependencies")
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


def setup_llama_cpp(skip_cuda: bool, has_gpu: bool):
    """
    Install llama-cpp-python with CUDA acceleration if a compatible NVIDIA GPU is present.
    Falls back gracefully to CPU-only build if CUDA toolchain is unavailable.
    """
    print_step(3, "Installing llama-cpp-python (Local GGUF Inference Engine)")

    if skip_cuda or not has_gpu:
        print("  Installing llama-cpp-python (CPU-only, no CUDA)...")
        try:
            run_command([
                sys.executable, "-m", "pip", "install",
                "llama-cpp-python", "--quiet",
                "--extra-index-url", "https://pypi.org/simple",
            ])
            print("  llama-cpp-python (CPU) installed.")
        except subprocess.CalledProcessError:
            print("  [WARNING] CPU llama-cpp-python install failed. Continuing...", file=sys.stderr)
        return

    # --- CUDA path ---
    cuda_index = "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu124"
    print(f"  Installing CUDA-accelerated llama-cpp-python for RTX GPU (CUDA 12.4)...")
    print(f"  Source: {cuda_index}")
    try:
        run_command([
            sys.executable, "-m", "pip", "install",
            "llama-cpp-python",
            "--upgrade",
            "--force-reinstall",
            "--extra-index-url", cuda_index,
        ])
        print("  llama-cpp-python (CUDA 12.4) installed successfully. GPU acceleration ready.")
        update_env_variable("LLM_DEVICE", "cuda")
    except subprocess.CalledProcessError:
        print("  [WARNING] CUDA wheel install failed. Falling back to CPU-only llama-cpp-python.", file=sys.stderr)
        try:
            run_command([sys.executable, "-m", "pip", "install", "llama-cpp-python", "--quiet"])
            update_env_variable("LLM_DEVICE", "cpu")
            print("  llama-cpp-python (CPU fallback) installed.")
        except subprocess.CalledProcessError:
            print("  [WARNING] CPU llama-cpp-python also failed. Continuing...", file=sys.stderr)


def setup_frontend(skip_frontend: bool):
    print_step(4, "Configuring Frontend Dependencies")
    if skip_frontend:
        print("  Skipping frontend setup (--skip-frontend).")
        return

    frontend_dir = BASE_DIR / "frontend"
    pnpm_cmd = shutil.which("pnpm")
    npm_cmd = shutil.which("npm")

    if pnpm_cmd:
        print("  Installing frontend packages via pnpm install...")
        try:
            run_command([pnpm_cmd, "install", "--loglevel=error"], cwd=frontend_dir)
            print("  Frontend dependencies installed successfully via pnpm.")
            return
        except subprocess.CalledProcessError as e:
            print(f"  [WARNING] Frontend pnpm install returned code {e.returncode}. Trying npm fallback...", file=sys.stderr)

    if npm_cmd:
        print("  Installing frontend packages via npm install...")
        try:
            run_command([npm_cmd, "install", "--no-audit", "--loglevel=error"], cwd=frontend_dir)
            print("  Frontend dependencies installed successfully via npm.")
        except subprocess.CalledProcessError as e:
            print(f"  [WARNING] Frontend npm install returned code {e.returncode}. Continuing...", file=sys.stderr)
    else:
        print("  [WARNING] Neither pnpm nor npm found. Skipping frontend dependency install.", file=sys.stderr)


def bootstrap_docker_services(skip_docker: bool):
    print_step(5, "Bootstrapping Backing Services (PostgreSQL & Redis)")
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
    print_step(6, "Running Database Migrations & Synthetic Seeding")
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


def download_file_with_progress(url: str, dest_path: Path):
    """Downloads a file with clean command-line progress updates."""
    import urllib.request

    print(f"  Downloading model to {dest_path.name}...")
    print(f"  Source URL: {url}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".tmp")

    def progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            mb_downloaded = (count * block_size) / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\r  Progress: {percent}% [{mb_downloaded:.1f} MB / {total_mb:.1f} MB]")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, str(temp_path), reporthook=progress_hook)
        print("\n  Download complete. Finalizing model file...")
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
        print(f"  [SUCCESS] Local GGUF model saved to {dest_path}")
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"\n  [ERROR] Failed to download model: {e}", file=sys.stderr)


def update_env_variable(key: str, value: str):
    """Safely updates or adds a key-value pair in .env file."""
    env_file = BASE_DIR / ".env"
    lines = []
    found = False
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}=") or line.strip().startswith(f"{key} ="):
                lines[i] = f"{key}={value}"
                found = True
                break
    if not found:
        lines.append(f"{key}={value}")
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Updated {key} in .env")


def setup_local_models(
    skip_models: bool,
    download_model: bool,
    api_key: str,
    no_interactive: bool,
    skip_docker: bool,
):
    print_step(7, "Reasoning Model Setup (Local Gemma GGUF or Hosted API Key)")
    if skip_models:
        print("  Skipping reasoning model setup (--skip-models).")
        return

    models_dir = BASE_DIR / "models"
    models_dir.mkdir(exist_ok=True)
    existing_gguf = list(models_dir.glob("*.gguf"))

    if existing_gguf:
        print(f"  [INFO] Found local GGUF model in models/: {existing_gguf[0].name}")
        print("  Model setup complete — skipping download.")
        return

    # Handle explicit CLI args
    if api_key:
        update_env_variable("XAI_API_KEY", api_key)
        update_env_variable("ENABLE_GROK_FALLBACK", "true")
        update_env_variable("LLM_PROVIDER", "xai")
        print("  [SUCCESS] Configured xAI Grok API key for hosted reasoning.")
        return

    default_model_url = "https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf"
    default_model_dest = models_dir / "gemma-3-4b-it-Q4_K_M.gguf"

    if download_model:
        print("  Downloading Gemma 3 4B Instruct Q4_K_M GGUF (~2.48 GB)...")
        download_file_with_progress(default_model_url, default_model_dest)
        return

    # Interactive choice if running in a terminal
    is_interactive = sys.stdin.isatty() and not no_interactive

    if is_interactive:
        print("\n  " + "-" * 64)
        print("  Reasoning Provider Selection:")
        print("  MetaRadar requires a reasoning provider for Ask Athena synthesis.\n")
        print("  [1] Download Gemma 3 4B Instruct Q4 GGUF into models/ [~2.48 GB]")
        print("      100% offline, private, zero API fees.")
        print("      Requires CUDA GPU or CPU (slower without GPU).")
        print("  [2] Enter Hosted LLM API Key (xAI Grok / OpenAI compatible)")
        print("      Instant cloud execution without local disk footprint.")
        print("  [3] Skip for now (operates in BART degraded factual fallback mode)")
        print("  " + "-" * 64)

        try:
            choice = input("  Select an option [1/2/3] (default: 1): ").strip()
        except (KeyboardInterrupt, EOFError):
            choice = "3"

        if choice == "2":
            key_input = input("  Enter your xAI / Grok API Key: ").strip()
            if key_input:
                update_env_variable("XAI_API_KEY", key_input)
                update_env_variable("ENABLE_GROK_FALLBACK", "true")
                update_env_variable("LLM_PROVIDER", "xai")
                print("  [SUCCESS] Configured xAI Grok API key in .env.")
            else:
                print("  No key entered. Continuing with default configuration.")
            return
        elif choice in ("1", ""):
            print("  Downloading Gemma 3 4B Instruct Q4_K_M GGUF (~2.48 GB)...")
            download_file_with_progress(default_model_url, default_model_dest)
            return
        else:
            print("  Skipping reasoning model setup. System will use BART degraded factual mode.")
            return

    # Non-interactive fallback
    print("  [INFO] No local GGUF found. Run with --download-model to fetch Gemma 3 4B automatically.")
    print("         Place any .gguf file into models/ for offline reasoning.")


def main():
    parser = argparse.ArgumentParser(
        description="MetaRadar Zero-Config Environment Setup Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skip-docker", action="store_true", help="Skip starting Docker Compose backing services")
    parser.add_argument("--skip-models", action="store_true", help="Skip pulling or downloading LLM models")
    parser.add_argument("--skip-cuda", action="store_true", help="Skip CUDA llama-cpp-python, install CPU-only version")
    parser.add_argument("--download-model", action="store_true", help="Automatically download default local GGUF model")
    parser.add_argument("--api-key", type=str, default="", help="Provide xAI Grok API key for hosted reasoning")
    parser.add_argument("--no-interactive", action="store_true", help="Disable interactive prompts")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip installing frontend NPM packages")
    parser.add_argument("--skip-db-seed", action="store_true", help="Skip populating synthetic database seed rows")

    args = parser.parse_args()

    print("=" * 70)
    print(" MetaRadar Decision Intelligence Platform — Environment Setup")
    print(" Production Ready | Local Gemma GGUF + CUDA | PGVector | Next.js 16")
    print("=" * 70)

    start_time = time.time()

    has_gpu = check_prerequisites()
    setup_backend()
    setup_llama_cpp(args.skip_cuda, has_gpu)
    setup_frontend(args.skip_frontend)
    bootstrap_docker_services(args.skip_docker)
    run_database_migrations_and_seed(args.skip_db_seed)
    setup_local_models(
        args.skip_models,
        args.download_model,
        args.api_key,
        args.no_interactive,
        args.skip_docker,
    )

    elapsed = round(time.time() - start_time, 1)

    print("\n" + "=" * 70)
    print(f" [SUCCESS] MetaRadar environment setup complete in {elapsed}s!")
    print()
    print(" Next Steps:")
    print("   1. Start all services:   python start.py")
    print("   2. Open the app:         http://localhost:3000/dashboard")
    print()
    print(" GPU Acceleration:")
    if has_gpu:
        print("   NVIDIA GPU detected — Gemma will run on CUDA with full RTX offload.")
        print("   Set LLM_GPU_LAYERS in .env to tune (default: -1 = all layers on GPU).")
    else:
        print("   No NVIDIA GPU — Gemma will run on CPU (slower, ~30-90s per response).")
    print("=" * 70)


if __name__ == "__main__":
    main()
