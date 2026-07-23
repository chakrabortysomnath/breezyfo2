# setup.ps1 - one-time setup for the Covered Call Analyser desktop build.
#
# Creates a local virtualenv, installs dependencies, and puts a "Breezy F&O"
# shortcut on your Desktop that launches the app in a native window.
#
# Run from anywhere:
#     powershell -ExecutionPolicy Bypass -File desktop\setup.ps1
#
# Re-running is safe: it reuses the existing venv and refreshes dependencies.

$ErrorActionPreference = "Stop"

$DesktopDir = $PSScriptRoot                       # ...\covered-call-analyser\desktop
$AppRoot    = Split-Path $DesktopDir -Parent      # ...\covered-call-analyser

# The venv lives OUTSIDE the project tree, under %LOCALAPPDATA%, on purpose:
# deep OneDrive paths + Streamlit's deeply-nested bundled asset files exceed the
# Windows 260-char MAX_PATH limit and break `pip install` inside the project.
$VenvDir    = Join-Path $env:LOCALAPPDATA "BreezyFO\venv"
$Reqs       = Join-Path $DesktopDir "requirements-desktop.txt"
$Launcher   = Join-Path $DesktopDir "launcher.py"
$IconPath   = Join-Path $DesktopDir "assets\icon.ico"

Write-Host "Covered Call Analyser - desktop setup" -ForegroundColor Cyan
Write-Host "App root: $AppRoot"

# --- 1. Locate a Python interpreter ---------------------------------------
$PythonCmd = $null
foreach ($candidate in @("python", "py")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) { $PythonCmd = $cmd.Source; break }
}
if (-not $PythonCmd) {
    throw "Python was not found on PATH. Install Python 3.10+ and re-run this script."
}
Write-Host "Using Python: $PythonCmd"

# --- 2. Create the virtualenv ---------------------------------------------
$VenvPython  = Join-Path $VenvDir "Scripts\python.exe"
$VenvPythonW = Join-Path $VenvDir "Scripts\pythonw.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtualenv at $VenvDir ..."
    $VenvParent = Split-Path $VenvDir -Parent
    if (-not (Test-Path $VenvParent)) { New-Item -ItemType Directory -Force -Path $VenvParent | Out-Null }
    & $PythonCmd -m venv $VenvDir
} else {
    Write-Host "Reusing existing virtualenv at $VenvDir"
}

# --- 3. Install dependencies ----------------------------------------------
Write-Host "Installing dependencies (this can take a few minutes) ..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r $Reqs

# --- 4. Create the Desktop shortcut ---------------------------------------
$DesktopPath  = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Breezy F&O.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath       = $VenvPythonW          # pythonw = no console window
$Shortcut.Arguments        = "`"$Launcher`""
$Shortcut.WorkingDirectory = $AppRoot
$Shortcut.Description       = "Covered Call Analyser (Breezy F&O)"
if (Test-Path $IconPath) { $Shortcut.IconLocation = $IconPath }
$Shortcut.Save()

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Launch from the 'Breezy F&O' shortcut on your Desktop."
Write-Host "To test with a visible console, run:"
Write-Host "    `"$VenvPython`" `"$Launcher`""
