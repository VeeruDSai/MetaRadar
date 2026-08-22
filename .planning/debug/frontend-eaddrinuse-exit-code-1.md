# Debug Session: Frontend Process Exit Code 1 (EADDRINUSE Port 3000)

**Slug:** `frontend-eaddrinuse-exit-code-1`
**Status:** `RESOLVED`
**Trigger:** Running `python start.py` failed with `[ERROR] Frontend process exited unexpectedly with code 1!`.

## Symptoms
- **Expected:** `python start.py` launches both FastAPI backend (port 8000) and Next.js frontend (port 3000) and runs live telemetry loop.
- **Actual:**
  - `start.py` launched backend and frontend.
  - Next.js frontend exited immediately with code 1.
  - `start.py` reported `[ERROR] Frontend process exited unexpectedly with code 1!` and terminated.
- **Error in `logs/frontend.log`:**
  ```
  > metaradar-frontend@5.1.0 dev
  > next dev -p 3000

  ⨯ Failed to start server
  Error: listen EADDRINUSE: address already in use :::3000
      at <unknown> (Error: listen EADDRINUSE: address already in use :::3000)
      at new Promise (<anonymous>) {
    code: 'EADDRINUSE',
    errno: -4091,
    syscall: 'listen',
    address: '::',
    port: 3000
  }
  ```

## Root Cause Analysis
1. **Windows Child Process Orphan on Termination (`cleanup_processes`)**:
   On Windows, `npm` runs as `npm.cmd`. When Python invoked `proc.terminate()` on `npm.cmd`, Windows terminated only the top-level batch script process, leaving the child `node.exe` (Next.js dev server) alive and orphaned in the background, keeping port 3000 bound.
2. **Missing Port Pre-flight Check & Auto-Recovery**:
   `start.py` launched `start_backend()` and `start_frontend()` without verifying if ports 8000 or 3000 were already in use or releasing stale connections from previous abnormal exits.
3. **Missing Crash Log Telemetry**:
   When child processes exited unexpectedly with non-zero exit codes, `start.py` exited without printing the underlying stderr/stdout from `logs/frontend.log` or `logs/backend.log`, hindering fast root cause discovery.

## Key Changes
1. **`start.py`**:
   - **Process-Tree Termination**: Updated `cleanup_processes()` to execute `taskkill /F /T /PID` on Windows, ensuring all child processes (including `node.exe` and `uvicorn`) in the process tree are cleanly terminated.
   - **Port Pre-Flight Auto-Cleanup**: Added `free_port_if_in_use(port, service_name)` before launching backend and frontend to detect and terminate any lingering orphaned process holding ports 8000 or 3000.
   - **Process Crash Diagnostics**: Added `print_recent_logs()` to immediately print the trailing lines of the log file (`logs/frontend.log` or `logs/backend.log`) to stderr whenever a process exits unexpectedly.
   - **Docker Daemon Pre-check**: Added `docker info` check before docker compose to avoid unnecessary retry timeouts if Docker Desktop is offline.
2. **`tests/test_launchers.py`**:
   - Added unit test cases verifying `free_port_if_in_use`, `print_recent_logs`, `check_socket_ready`, and module exports.

## Verification
- `pytest tests/test_launchers.py`: 5 passed in 0.95s.
- Full `pytest`: 82 passed, 1 skipped in 57.79s.
- Frontend typecheck: `npx tsc --noEmit` passed with 0 errors.
- `python start.py --help`: Verified all flags and arguments.
