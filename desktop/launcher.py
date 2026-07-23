"""
launcher.py — Desktop launcher for the F&O Trading app (Breezy F&O).

Runs the whole app locally on a laptop, no Render / cloud required:

    * FastAPI backend  -> uvicorn in a background daemon thread
    * Streamlit UI     -> a child `python -m streamlit run` process
    * Native window    -> pywebview on the main thread (falls back to the
                          default browser if pywebview / WebView2 is missing)

The backend binds to 127.0.0.1:8000 (the frontend's default API_BASE_URL);
the launcher also writes that URL into the frontend's Streamlit secrets so the
UI always talks to this local backend. Closing the window shuts everything down.

Run it two ways:
    python  desktop/launcher.py     # console visible — use while testing
    pythonw desktop/launcher.py     # no console — used by the Desktop shortcut
"""

from __future__ import annotations

import atexit
import importlib
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
DESKTOP_DIR = Path(__file__).resolve().parent          # <repo>/desktop
APP_ROOT = DESKTOP_DIR.parent                          # <repo> (has backend/ + frontend/)
FRONTEND_DIR = APP_ROOT / "frontend"
FRONTEND_APP = FRONTEND_DIR / "app.py"

WINDOW_TITLE = "Breezy F&O"
HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000                                # frontend's default API_BASE_URL port

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


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, port))
            return True
        except OSError:
            return False


def _wait_http(url: str, timeout: float = 45.0, proc: subprocess.Popen | None = None) -> bool:
    """Poll `url` until it answers HTTP 200, the timeout elapses, or `proc` dies."""
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


def _ensure_api_base(port: int) -> None:
    """Point the Streamlit frontend at our local backend via its secrets file.

    The frontend reads `st.secrets.get("API_BASE_URL", "http://localhost:8000")`.
    We write/replace API_BASE_URL in <frontend>/.streamlit/secrets.toml (the file
    Streamlit reads when run from the frontend dir), preserving any other keys.
    """
    sdir = FRONTEND_DIR / ".streamlit"
    sdir.mkdir(parents=True, exist_ok=True)
    sfile = sdir / "secrets.toml"
    line = f'API_BASE_URL = "http://{HOST}:{port}"'
    if sfile.exists():
        out, found = [], False
        for ln in sfile.read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith("API_BASE_URL"):
                out.append(line)
                found = True
            else:
                out.append(ln)
        if not found:
            out.append(line)
        sfile.write_text("\n".join(out) + "\n", encoding="utf-8")
    else:
        sfile.write_text(line + "\n", encoding="utf-8")


def _webview2_available() -> bool:
    """Best-effort check for the WebView2 Evergreen Runtime (Windows only)."""
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
# Backend discovery (works across layouts)
# ---------------------------------------------------------------------------
def _load_fastapi_app():
    """Import and return the FastAPI `app`, tolerating different repo layouts.

    * breezyfo2:            backend/app/main.py, imported as `app.main`
                            (needs <repo>/backend on sys.path so its own
                            `from app.db import ...` imports resolve).
    * covered-call layout:  backend/main.py, imported as `backend.main`.
    """
    candidates = [
        ("app.main", [APP_ROOT / "backend", APP_ROOT]),   # breezyfo2 (backend/app package)
        ("backend.main", [APP_ROOT]),                     # covered-call-analyser layout
        ("backend.app.main", [APP_ROOT]),                 # defensive
    ]
    last_err: Exception | None = None
    for module_name, paths in candidates:
        for p in paths:
            sp = str(p)
            if sp not in sys.path:
                sys.path.insert(0, sp)
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            top = module_name.split(".")[0]
            # Only skip to the next candidate when it's the layout that's absent
            # (the top package is missing). A missing *dependency* (e.g. sqlalchemy)
            # is a real error and must surface, not be masked as "wrong layout".
            if exc.name and (exc.name == top or module_name.startswith(f"{exc.name}.")):
                last_err = exc
                continue
            raise
        if hasattr(mod, "app"):
            return mod.app
        last_err = RuntimeError(f"{module_name} has no `app` attribute")
    raise RuntimeError(
        f"Could not locate the FastAPI app (tried app.main / backend.main). "
        f"Last error: {last_err}"
    )


def _start_backend(app_obj, api_port: int):
    """Start the FastAPI backend on a background daemon thread. Returns the Server."""
    import uvicorn

    config = uvicorn.Config(app_obj, host=HOST, port=api_port, log_level="warning")
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
    """Launch the Streamlit UI as a child process using the current interpreter.

    cwd is the frontend dir so Streamlit picks up frontend/.streamlit/config.toml
    (theme) and secrets.toml, and so `import components`/`pages` resolve.
    """
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.address", HOST,
        "--server.port", str(st_port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none",
    ]
    return subprocess.Popen(cmd, cwd=str(FRONTEND_DIR), env=env)


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

    # Backend port: prefer 8000 (frontend default); fall back to a free port.
    api_port = DEFAULT_API_PORT if _port_is_free(DEFAULT_API_PORT) else _free_port()
    st_port = _free_port()

    # Point the frontend at our local backend regardless of any prior config.
    _ensure_api_base(api_port)

    env = os.environ.copy()
    atexit.register(_shutdown)

    # 1) Backend
    print("[launcher] loading FastAPI app ...", flush=True)
    try:
        app_obj = _load_fastapi_app()
    except Exception as exc:
        print(f"[launcher] ERROR: {exc}", file=sys.stderr, flush=True)
        return 1
    print(f"[launcher] starting backend on {HOST}:{api_port} ...", flush=True)
    _server = _start_backend(app_obj, api_port)
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
