# Breezy F&O — Desktop build

Run the F&O Trading app on a laptop as a native desktop app — no Render, no
cloud. The FastAPI backend and the Streamlit UI both run locally on `127.0.0.1`,
wrapped in a native window.

**Prerequisite:** Python 3.10+ installed and on `PATH`. On Windows 11 the
WebView2 runtime (used for the native window) is already present.

## One-time setup

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File desktop\setup.ps1
```

This creates a virtualenv at `%LOCALAPPDATA%\BreezyFO\venv`, installs
`desktop\requirements-desktop.txt`, and adds a **Breezy F&O** shortcut to your
Desktop.

> The venv lives under `%LOCALAPPDATA%` (not inside the project) on purpose:
> deep OneDrive paths plus Streamlit's deeply-nested bundled files exceed the
> Windows 260-character path limit and break `pip install` inside the project.

## Running

Double-click the **Breezy F&O** Desktop shortcut. A window opens on the app's
login screen — register (with the app's registration code, if configured) or log
in, then enter your ICICI Breeze credentials as usual. Closing the window shuts
down both local services.

### Running with a visible console (for troubleshooting)

```powershell
& "$env:LOCALAPPDATA\BreezyFO\venv\Scripts\python.exe" desktop\launcher.py
```

This prints backend/Streamlit logs so you can see any startup errors.

## What the launcher does

- Locates the FastAPI app (`app.main` under `backend/`) and starts it with
  **uvicorn** on a background thread, bound to `127.0.0.1:8000` (falls back to a
  free port if 8000 is busy).
- Writes `API_BASE_URL` into `frontend/.streamlit/secrets.toml` so the Streamlit
  UI talks to this local backend (the frontend reads `st.secrets["API_BASE_URL"]`,
  default `http://localhost:8000`).
- Starts the Streamlit UI as a child process (from the `frontend/` dir, so its
  theme and secrets load) on a free port.
- Opens a native window (pywebview). If the window can't be created it falls back
  to your default browser and keeps running until you close it.

## Notes & known limitations

- **Local database:** the backend uses SQLite (`users.db`) created next to where
  the app is launched — user accounts and auth live there, on your machine only.
- **Credentials:** your ICICI Breeze credentials are handled by the app exactly
  as in the web version; nothing extra is stored by the launcher.
- **QuotaGuard proxy is not used.** It was a Render-only workaround for rotating
  IPs; on a laptop it stays disabled (unset), which is a no-op in the code.
- **WebView2:** if the window is blank, install the WebView2 Evergreen Runtime
  from https://developer.microsoft.com/microsoft-edge/webview2/ and relaunch.

## Files

| File | Purpose |
|------|---------|
| `launcher.py` | Boots backend + Streamlit + native window; handles shutdown. |
| `requirements-desktop.txt` | Dependency set for the local venv (backend + frontend + pywebview). |
| `setup.ps1` | One-time venv + install + Desktop shortcut. |
