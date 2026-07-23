"""
launcher.py — Desktop launcher for the Covered Call Analyser (Breezy F&O).

Runs the whole app locally on a laptop, no Render / cloud required:

    * FastAPI backend  -> uvicorn in a background daemon thread
    * Streamlit UI     -> a child `python -m streamlit run` process
    * Native window    -> pywebview on the main thread (falls back to the
                          default browser if pywebview / WebView2 is missing)

Both local services bind to 127.0.0.1 on automatically-chosen free ports, so
nothing is exposed to the network. Closing the window shuts everything down.

Run it two ways:
    python  desktop/launcher.py     # console visible — use while testing
    pythonw desktop/launcher.py     # no console — used by the Desktop shortcut
"""

from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DESKTOP_DIR = Path(__file__).resolve().parent          # .../covered-call-analyser/desktop
APP_ROOT = DESKTOP_DIR.parent                          # .../covered-call-analyser
FRONTEND_APP = APP_ROOT / "frontend" / "app.py"

# Make `import backend.main` resolvable regardless of the current working dir.
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

WINDOW_TITLE = "Breezy F&O"
HOST = "127.0.0.1"

# Populated in main(); referenced by the shutdown helpers.
_st_proc: subprocess.Popen | None = None
_server = None  # uvicorn.Server


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------
def _free_port() -> int:
    """Ask the OS for an unused TCP port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def _wait_http(url: str, timeout: float = 45.0, proc: subprocess.Popen | None = None) -> bool:
    """Poll `url` until it answers HTTP 200, the timeout elapses, or `proc` dies.

    Returns True on success. If `proc` is supplied and exits early, returns
    False immediately so we can surface the failure instead of hanging.
    """
    import requests

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            return False
        try:
            if requests.get(url, timeout=2).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.4)
    return False


def _webview2_available() -> bool:
    """Best-effort check for the WebView2 Evergreen Runtime (Windows only).

    Returns True on non-Windows or if we cannot tell — we only use a negative
    result to warn the user, never to block launch.
    """
    if os.name != "nt":
        return True
    try:
        import winreg
    except ImportError:
        return True

    client_id = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"  # WebView2 Evergreen
    keys = [
        (winreg.HKEY_LOCAL_MACHINE,
         rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{client_id}"),
        (winreg.HKEY_LOCAL_MACHINE,
         rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{client_id}"),
        (winreg.HKEY_CURRENT_USER,
         rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{client_id}"),
    ]
    for root, path in keys:
        try:
            with winreg.OpenKey(root, path) as k:
                version, _ = winreg.QueryValueEx(k, "pv")
                if version:
                    return True
        except OSError:
            continue
    return False


# ---------------------------------------------------------------------------
# Backend (uvicorn in a thread)
# ---------------------------------------------------------------------------
def _start_backend(api_port: int):
    """Start the FastAPI backend on a background daemon thread. Returns the Server."""
    import uvicorn

    from backend.main import app  # imported after APP_ROOT is on sys.path

    config = uvicorn.Config(app, host=HOST, port=api_port, log_level="warning")
    server = uvicorn.Server(config)
    # Signal handlers can only be installed on the main thread; disable them so
    # the server can run happily on a worker thread.
    server.install_signal_handlers = lambda: None

    threading.Thread(target=server.run, name="uvicorn", daemon=True).start()
    return server


# ---------------------------------------------------------------------------
# Frontend (Streamlit child process)
# ---------------------------------------------------------------------------
def _start_streamlit(st_port: int, env: dict) -> subprocess.Popen:
    """Launch the Streamlit UI as a child process using the current interpreter."""
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(FRONTEND_APP),
        "--server.address", HOST,
        "--server.port", str(st_port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none",
    ]
    return subprocess.Popen(cmd, cwd=str(APP_ROOT), env=env)


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------
def _shutdown() -> None:
    """Stop the Streamlit child and signal the uvicorn server to exit. Idempotent."""
    global _st_proc, _server
    if _st_proc is not None and _st_proc.poll() is None:
        _st_proc.terminate()
        try:
            _st_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _st_proc.kill()
    _st_proc = None
    if _server is not None:
        _server.should_exit = True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    global _st_proc, _server

    api_port = _free_port()
    st_port = _free_port()

    # Environment for both services. The Streamlit child inherits this via env=.
    env = os.environ.copy()
    env["CLAUDE_INTEL_BYPASS"] = "true"
    env["BACKEND_URL"] = f"http://{HOST}:{api_port}"
    env["PING_URL"] = f"http://{HOST}:{api_port}/health"
    # Apply to our own process too, so anything the backend reads matches.
    os.environ.update(env)

    atexit.register(_shutdown)

    # 1) Backend
    print(f"[launcher] starting backend on {HOST}:{api_port} ...", flush=True)
    _server = _start_backend(api_port)
    if not _wait_http(f"http://{HOST}:{api_port}/health", timeout=45):
        print("[launcher] ERROR: backend did not become ready.", file=sys.stderr, flush=True)
        _shutdown()
        return 1

    # 2) Frontend
    print(f"[launcher] starting Streamlit on {HOST}:{st_port} ...", flush=True)
    _st_proc = _start_streamlit(st_port, env)
    st_url = f"http://{HOST}:{st_port}"
    if not _wait_http(f"{st_url}/_stcore/health", timeout=90, proc=_st_proc):
        print("[launcher] ERROR: Streamlit did not become ready.", file=sys.stderr, flush=True)
        _shutdown()
        return 1

    # 3) Window
    if not _webview2_available():
        print(
            "[launcher] WARNING: WebView2 Runtime not detected. The native window "
            "may not render. Install it from https://developer.microsoft.com/microsoft-edge/webview2/",
            file=sys.stderr, flush=True,
        )

    try:
        import webview  # pywebview

        print(f"[launcher] opening window -> {st_url}", flush=True)
        webview.create_window(WINDOW_TITLE, st_url, width=1280, height=860)
        webview.start()  # blocks on the main thread until the window is closed
    except Exception as exc:
        # Fall back to the default browser and keep the services alive.
        print(
            f"[launcher] native window unavailable ({exc}); opening in browser instead. "
            "Close this window to quit.",
            file=sys.stderr, flush=True,
        )
        import webbrowser

        webbrowser.open(st_url)
        try:
            while _st_proc.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    # 4) Clean up
    print("[launcher] shutting down ...", flush=True)
    _shutdown()
    return 0


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()  # harmless here; safe if ever frozen
    sys.exit(main())
