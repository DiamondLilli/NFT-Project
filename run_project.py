"""run_project.py

Automates common setup and runs the NFT-Project on Windows (cmd.exe).

What it does:
- Verifies Python version and presence of requirements.txt
- Optionally creates a virtual environment directory `.venv` (does NOT activate it in the current shell)
- Optionally installs requirements into the current Python interpreter (will ask before running pip)
- Checks if ports 5000 and 8000 are free
- Starts backend (`app.py`) and frontend (`serve.py`) as subprocesses and streams their output
- Polls backend `/api/status` until ready or times out

Notes:
- This script attempts to be helpful but can't activate a venv in your current interactive shell. If you prefer to run in a venv, create and activate it first, then run this script from inside the venv.
- Run this from cmd.exe in the project root.

Usage (cmd.exe):
  python run_project.py

If you want the script to auto-install missing requirements pass `--install`.
"""
from __future__ import annotations

import sys
import os
import subprocess
import time
import socket
import threading
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BACKEND_PORT = 5000
FRONTEND_PORT = 8000
BACKEND_CMD = [sys.executable, str(PROJECT_ROOT / 'app.py')]
FRONTEND_CMD = [sys.executable, str(PROJECT_ROOT / 'serve.py')]


def check_python_version(min_major=3, min_minor=8):
    major, minor = sys.version_info[:2]
    if (major, minor) < (min_major, min_minor):
        print(f"ERROR: Python {min_major}.{min_minor}+ is required. Found {major}.{minor}.")
        return False
    return True


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def create_venv(venv_dir: Path):
    if venv_dir.exists():
        print(f"Virtual environment directory '{venv_dir}' already exists. Skipping creation.")
        return True
    print(f"Creating virtual environment at '{venv_dir}'...")
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', str(venv_dir)])
        print("Virtual environment created.")
        return True
    except subprocess.CalledProcessError as e:
        print("ERROR: Failed to create virtual environment:", e)
        return False


def pip_install_requirements(requirements_file: Path) -> bool:
    if not requirements_file.exists():
        print("ERROR: requirements.txt not found.")
        return False
    print(f"Installing packages from {requirements_file} into the current Python environment...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)])
        print("Dependencies installed.")
        return True
    except subprocess.CalledProcessError as e:
        print("ERROR: pip install failed:", e)
        return False


def stream_subprocess_output(proc: subprocess.Popen, name: str):
    """Stream stdout from a subprocess in a background thread and return the thread."""
    def _stream():
        try:
            for raw in proc.stdout:  # type: ignore
                try:
                    line = raw.decode(errors='replace').rstrip()
                except Exception:
                    line = str(raw)
                print(f"[{name}] " + line)
        except Exception:
            # If proc.stdout is closed while reading, just exit the thread
            return

    t = threading.Thread(target=_stream, daemon=True)
    t.start()
    return t


def start_process(cmd: list[str], name: str) -> subprocess.Popen | None:
    try:
        # Ensure child Python processes run with UTF-8 enabled to avoid
        # UnicodeEncodeError when the child prints emojis on Windows consoles.
        env = os.environ.copy()
        # PYTHONUTF8 enables the UTF-8 mode (works on Python 3.7+)
        env.setdefault('PYTHONUTF8', '1')
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        stream_subprocess_output(proc, name)
        return proc
    except Exception as e:
        print(f"ERROR: Failed to start {name}: {e}")
        return None


def poll_backend_ready(timeout: int = 20) -> bool:
    import urllib.request

    url = f'http://127.0.0.1:{BACKEND_PORT}/api/status'
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    print("Backend is ready (api/status returned 200).")
                    return True
        except Exception:
            time.sleep(1)
    print(f"ERROR: Backend did not become ready within {timeout} seconds.")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true', help='Install requirements into current Python environment')
    parser.add_argument('--create-venv', action='store_true', help='Create a .venv directory (won\'t activate it)')
    parser.add_argument('--no-frontend', action='store_true', help='Do not start the frontend serve.py')
    args = parser.parse_args()

    # Basic checks
    if not check_python_version():
        sys.exit(2)

    req_file = PROJECT_ROOT / 'requirements.txt'

    if args.create_venv:
        venv_dir = PROJECT_ROOT / '.venv'
        if not create_venv(venv_dir):
            sys.exit(1)

    if args.install:
        ok = pip_install_requirements(req_file)
        if not ok:
            print("One or more packages failed to install. See errors above. You can try to fix platform-specific packages (PyAudio, librosa) manually.")
            # Continue: the backend may still run with available packages

    # Port checks
    print(f"Checking port {BACKEND_PORT} (backend) and {FRONTEND_PORT} (frontend)...")
    if not port_is_free(BACKEND_PORT):
        print(f"ERROR: Port {BACKEND_PORT} appears to be in use. Stop any process listening on that port or change the backend port in app.py.")
        sys.exit(3)
    if not args.no_frontend and not port_is_free(FRONTEND_PORT):
        print(f"ERROR: Port {FRONTEND_PORT} appears to be in use. Stop any process listening on that port or change the frontend port in serve.py.")
        sys.exit(3)

    # Start backend
    print("Starting backend (app.py)...")
    backend_proc = start_process(BACKEND_CMD, 'backend')
    if backend_proc is None:
        sys.exit(4)

    # Wait for backend readiness
    if not poll_backend_ready(timeout=25):
        print("Check backend logs above for errors. Exiting and terminating started processes.")
        backend_proc.terminate()
        sys.exit(5)

    # Start frontend
    frontend_proc = None
    if not args.no_frontend:
        print("Starting frontend (serve.py)...")
        frontend_proc = start_process(FRONTEND_CMD, 'frontend')
        if frontend_proc is None:
            print("WARNING: frontend failed to start. You can still open index.html directly in a browser, but use a server to avoid CORS/file issues.")

    print("\nAll processes started. Backend: http://127.0.0.1:5000  Frontend: http://127.0.0.1:8000")
    print("Press Ctrl+C in this console to stop both servers.")

    stream_threads = []
    if backend_proc:
        stream_threads.append(stream_subprocess_output(backend_proc, 'backend'))
    if frontend_proc:
        stream_threads.append(stream_subprocess_output(frontend_proc, 'frontend'))

    try:
        # Wait while subprocesses run; if any exit, break and clean up
        while True:
            time.sleep(1)
            if backend_proc and backend_proc.poll() is not None:
                print("Backend process exited. Terminating frontend (if running).")
                if frontend_proc and frontend_proc.poll() is None:
                    frontend_proc.terminate()
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print("Frontend process exited. Backend will continue running until you stop it.")
                break
    except KeyboardInterrupt:
        print("Received Ctrl+C, terminating processes...")
    finally:
        # Terminate processes politely
        for p in (backend_proc, frontend_proc):
            try:
                if p and p.poll() is None:
                    p.terminate()
            except Exception:
                pass

        # Give processes a moment to exit
        deadline = time.time() + 5
        for p in (backend_proc, frontend_proc):
            try:
                if p:
                    while p.poll() is None and time.time() < deadline:
                        time.sleep(0.1)
                    if p.poll() is None:
                        p.kill()
            except Exception:
                pass

        # Close stdout pipes (this will cause stream threads to exit)
        for p in (backend_proc, frontend_proc):
            try:
                if p and p.stdout:
                    p.stdout.close()
            except Exception:
                pass

        # Wait for stream threads to finish
        for t in stream_threads:
            try:
                if t and t.is_alive():
                    t.join(timeout=2)
            except Exception:
                pass


if __name__ == '__main__':
    main()
