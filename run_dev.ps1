<#
run_dev.ps1

Opens two PowerShell windows:
  - window 1: activates the venv and runs the FastAPI server (uvicorn)
  - window 2: activates the venv and runs the interactive CLI (cli.py)

Usage:
  Right-click -> Run with PowerShell, or from an elevated terminal:
    .\run_dev.ps1

Notes:
  - This script assumes the project root contains a .venv created with
    `python -m venv .venv` and that `cli.py` exists in the repo root.
  - If you prefer not to use the reloader, remove the `--reload` flag.
#>

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$activate = Join-Path $root ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $activate)) {
    Write-Host "Activate script not found at $activate" -ForegroundColor Yellow
    Write-Host "Create the venv with: python -m venv .venv" -ForegroundColor Yellow
    pause
    exit 1
}

# Server window
$serverCmd = "& '$activate'; uvicorn server.main:app --reload"
Start-Process -FilePath powershell -ArgumentList '-NoExit', '-Command', $serverCmd

# CLI window
$cliCmd = "& '$activate'; python '$root\cli.py'"
Start-Process -FilePath powershell -ArgumentList '-NoExit', '-Command', $cliCmd

Write-Host "Opened server and CLI windows." -ForegroundColor Green
