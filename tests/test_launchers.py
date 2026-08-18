import subprocess
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]


def test_setup_py_help():
    setup_script = base_dir / "setup.py"
    assert setup_script.exists(), "setup.py does not exist"

    res = subprocess.run(
        [sys.executable, str(setup_script), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "MetaRadar" in res.stdout
    assert "--skip-docker" in res.stdout
    assert "--skip-models" in res.stdout
    assert "--skip-frontend" in res.stdout
    assert "--skip-db-seed" in res.stdout


def test_start_py_help():
    start_script = base_dir / "start.py"
    assert start_script.exists(), "start.py does not exist"

    res = subprocess.run(
        [sys.executable, str(start_script), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "MetaRadar" in res.stdout
    assert "--no-frontend" in res.stdout
    assert "--no-backend" in res.stdout
    assert "--port-backend" in res.stdout
    assert "--port-frontend" in res.stdout
    assert "--daemon" in res.stdout


def test_start_py_module_imports():
    sys.path.insert(0, str(base_dir))
    import start
    assert hasattr(start, "cleanup_processes")
    assert hasattr(start, "check_endpoint_health")
    assert hasattr(start, "start_backend")
    assert hasattr(start, "start_frontend")
