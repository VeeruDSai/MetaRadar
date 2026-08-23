#!/usr/bin/env python3
"""
Model Downloader for MetaRadar
Downloads local GGUF reasoning models into the root models/ directory.
"""

import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"

# Default lightweight, fast, high-quality reasoning model
DEFAULT_MODEL_NAME = "gemma-3-4b-it-Q4_K_M.gguf"
DEFAULT_MODEL_URL = "https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf"


def download_model(url: str = DEFAULT_MODEL_URL, filename: str = DEFAULT_MODEL_NAME):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = MODELS_DIR / filename
    temp_path = dest_path.with_suffix(".tmp")

    if dest_path.exists():
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        print(f"[EXISTS] Model already exists at {dest_path} ({size_mb:.1f} MB).")
        return

    print("=" * 65)
    print(f" Downloading Reasoning Model: {filename}")
    print(f" Target Directory: {MODELS_DIR}")
    print(f" Source URL: {url}")
    print("=" * 65)

    start_time = time.time()

    def progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = min(100, int(count * block_size * 100 / total_size))
            mb_downloaded = (count * block_size) / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            elapsed = max(0.1, time.time() - start_time)
            speed_mb = mb_downloaded / elapsed
            sys.stdout.write(
                f"\r  [{percent:3d}%] {mb_downloaded:6.1f} MB / {total_mb:6.1f} MB ({speed_mb:4.1f} MB/s)"
            )
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, str(temp_path), reporthook=progress_hook)
        print("\n\nFinalizing model file...")
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        print(f"[SUCCESS] Download completed in {time.time() - start_time:.1f}s!")
        print(f"Saved: {dest_path} ({size_mb:.1f} MB)")
    except Exception as err:
        if temp_path.exists():
            temp_path.unlink()
        print(f"\n[ERROR] Download failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL_URL
    name = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL_NAME
    download_model(url, name)
