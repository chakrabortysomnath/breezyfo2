# Breezy F&O — Desktop build

Run the Covered Call Analyser on a laptop as a native desktop app — no Render,
no cloud. The FastAPI backend and the Streamlit UI both run locally on
`127.0.0.1` (random free ports), wrapped in a native window.

**Prerequisite:** Python 3.10+ installed and on `PATH`. On Windows 11 the
WebView2 runtime (used for the native window) is already present.

## One-time setup

From the `covered-call-analyser` folder:

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

Double-click the **Breezy F&O** Desktop shortcut. A window opens on the Breeze
login screen — paste your ICICI Breeze API key, secret, and today's session
token (regenerated daily via the ICICI login + TOTP flow). Closing the window
shuts down both local services.

### Running with a visible console (for troubleshooting)

```powershell
& "$env:LOCALAPPDATA\BreezyFO\venv\Scripts\python.exe" desktop\launcher.py
```

This prints backend/Streamlit logs so you can see any startup errors.

## What the launcher does

- Sets `CLAUDE_INTEL_BYPASS=true` (the AI "equity intel" runs in mock mode; no
  Anthropic API key needed) and points `BACKEND_URL` at the local backend.
- Starts the FastAPI backend (uvicorn) on a background thread.
- Starts the Streamlit UI as a child process.
- Opens a native window (pywebview). If the window can't be created it falls
  back to your default browser and keeps running until you close it.

## Notes & known limitations

- **Credentials are never stored** — they live only in the app session while the
  window is open, exactly as in the web version.
- **QuotaGuard proxy is not used.** It was a Render-only workaround for rotating
  IPs; on a laptop it stays disabled (unset), which is a no-op in the code.
- **yfinance is best-effort.** The 52-week stats and candlestick chart come from
  Yahoo Finance via `yfinance`. On a corporate network Yahoo may be blocked or
  rate-limited; if so, those extras simply won't appear — **the core covered-call
  / strangle analysis (from Breeze) is unaffected.** If you are behind a
  corporate proxy and want the charts, set `HTTP_PROXY` / `HTTPS_PROXY` before
  launching. If yfinance charts break after a Yahoo change, run
  `& "$env:LOCALAPPDATA\BreezyFO\venv\Scripts\python.exe" -m pip install -U yfinance`.
- **WebView2:** if the window is blank, install the WebView2 Evergreen Runtime
  from https://developer.microsoft.com/microsoft-edge/webview2/ and relaunch.

## Files

| File | Purpose |
|------|---------|
| `launcher.py` | Boots backend + Streamlit + native window; handles shutdown. |
| `requirements-desktop.txt` | Consolidated dependency set for the local venv. |
| `setup.ps1` | One-time venv + install + Desktop shortcut. |
| `assets/icon.ico` | Optional window/shortcut icon (add your own). |
