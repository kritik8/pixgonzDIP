<#
setup-and-run.ps1

Small helper to create a virtual environment, install dependencies, and run the backend.
Usage examples (PowerShell):
  # create venv, install FastAPI deps, and run the FastAPI server on port 8000
  .\setup-and-run.ps1 -Framework fastapi -Mode all -Port 8000

  # only install Flask deps (no run)
  .\setup-and-run.ps1 -Framework flask -Mode install

  # only run (assumes .venv already exists)
  .\setup-and-run.ps1 -Framework fastapi -Mode run -Port 8000

Notes:
- This script calls the venv python directly (no persistent Activate.ps1). That avoids activation issues inside CI or other shells.
- If PowerShell blocks script execution, run in the same shell first:
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
#>

param(
    [ValidateSet("fastapi","flask")]
    [string]$Framework = "fastapi",

    [ValidateSet("install","run","all")]
    [string]$Mode = "all",

    [int]$Port = 8000
)

# Make path absolute to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$venvPath = Join-Path $ScriptDir ".venv"

function Ensure-Venv {
    if (-Not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment at $venvPath..."
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { throw "Failed to create venv (exit $LASTEXITCODE)" }
    }
    else {
        Write-Host "Virtual environment already exists at $venvPath"
    }
}

function Install-Dependencies {
    Write-Host "Upgrading pip, setuptools, wheel..."
    & "$venvPath\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip/setuptools/wheel" }

    if ($Framework -eq 'fastapi') {
        Write-Host "Installing FastAPI requirements..."
        & "$venvPath\Scripts\python.exe" -m pip install -r requirements-fastapi.txt
    }
    else {
        Write-Host "Installing Flask requirements..."
        & "$venvPath\Scripts\python.exe" -m pip install -r requirements-flask.txt
    }

    if ($LASTEXITCODE -ne 0) { throw "pip install failed (exit $LASTEXITCODE)" }
}

function Run-Server {
    if ($Framework -eq 'fastapi') {
        Write-Host "Starting FastAPI (uvicorn) on port $Port..."
        & "$venvPath\Scripts\python.exe" -m uvicorn main:app --reload --port $Port
    }
    else {
        Write-Host "Starting Flask app on port 5000..."
        & "$venvPath\Scripts\python.exe" app_flask.py
    }
}

try {
    if ($Mode -in @('install','all')) {
        Ensure-Venv
        Install-Dependencies
    }

    if ($Mode -in @('run','all')) {
        Run-Server
    }
}
catch {
    Write-Error "Error: $_"
    exit 1
}