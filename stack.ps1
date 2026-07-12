<#
  stack.ps1 - one command to run the SalesIntel_AI local stack.

  From the repo root:
    .\stack.ps1            # start (default)
    .\stack.ps1 start      # start backend (:8000) + frontend (:5173), wait, print URLs
    .\stack.ps1 stop       # stop both cleanly (kills orphaned workers, frees ports)
    .\stack.ps1 restart    # stop then start
    .\stack.ps1 status     # show whether each is up

  Runs both servers detached in the background, logging to .logs\. PIDs are tracked
  in .logs\*.pid so `stop` can tree-kill the whole process (no orphaned sockets).
  Windows / PowerShell only. First-time setup: see docs\RUNBOOK.md section 2.
#>
param(
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"
$root     = $PSScriptRoot
$backend  = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$logDir   = Join-Path $root ".logs"
$py       = Join-Path $backend ".venv\Scripts\python.exe"

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m)   { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Port-Up([int]$port) {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Kill-Tree([int]$procId) {
    if ($procId) { cmd /c "taskkill /F /T /PID $procId >nul 2>&1" | Out-Null }
}

function Stop-Stack {
    # 1) tree-kill the processes we recorded at start
    foreach ($name in "backend", "frontend") {
        $pidFile = Join-Path $logDir "$name.pid"
        if (Test-Path $pidFile) {
            $procId = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
            Kill-Tree ([int]($procId -as [int]))
            Remove-Item $pidFile -ErrorAction SilentlyContinue
        }
    }
    # 2) fallback: tree-kill whatever still holds the ports (clears inherited/orphan sockets)
    foreach ($port in 8000, 5173) {
        $owners = @((Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).OwningProcess) | Sort-Object -Unique
        foreach ($procId in $owners) { Kill-Tree ([int]$procId) }
    }
    # 3) last resort: sweep our own uvicorn workers by command line
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'uvicorn' -and $_.CommandLine -match 'app\.main' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 800
}

function Start-Stack {
    if (-not (Test-Path $py)) {
        throw "Backend venv not found at $py. Run first-time setup (docs\RUNBOOK.md section 2)."
    }
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    Refresh-Path

    if ((Port-Up 8000) -or (Port-Up 5173)) {
        Warn "A stack is already running - stopping it first."
        Stop-Stack
    }

    Info "Starting backend  -> http://localhost:8000 ..."
    $be = Start-Process -FilePath $py `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000" `
        -WorkingDirectory $backend `
        -RedirectStandardOutput (Join-Path $logDir "backend.out.log") `
        -RedirectStandardError  (Join-Path $logDir "backend.err.log") `
        -WindowStyle Hidden -PassThru
    $be.Id | Out-File (Join-Path $logDir "backend.pid") -Encoding ascii

    Info "Starting frontend -> http://localhost:5173 ..."
    $fe = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "npm run dev" `
        -WorkingDirectory $frontend `
        -RedirectStandardOutput (Join-Path $logDir "frontend.out.log") `
        -RedirectStandardError  (Join-Path $logDir "frontend.err.log") `
        -WindowStyle Hidden -PassThru
    $fe.Id | Out-File (Join-Path $logDir "frontend.pid") -Encoding ascii

    $beOk = $false
    foreach ($i in 1..45) {
        try { if ((Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 2).status -eq "ok") { $beOk = $true; break } } catch { Start-Sleep -Milliseconds 700 }
    }
    $feOk = $false
    foreach ($i in 1..45) {
        try { if ((Invoke-WebRequest "http://localhost:5173" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $feOk = $true; break } } catch { Start-Sleep -Milliseconds 700 }
    }

    Write-Host ""
    if ($beOk) { Ok   "  Backend   UP    http://localhost:8000   (API docs: /docs)" }
    else       { Warn "  Backend   ...   not answering - see .logs\backend.err.log" }
    if ($feOk) { Ok   "  Frontend  UP    http://localhost:5173" }
    else       { Warn "  Frontend  ...   not answering - see .logs\frontend.out.log" }
    Write-Host ""
    Info "Open http://localhost:5173    (stop with: .\stack.ps1 stop)"
}

function Show-Status {
    $be = if (Port-Up 8000) { "UP" } else { "down" }
    $fe = if (Port-Up 5173) { "UP" } else { "down" }
    Write-Host "  backend   :8000   $be"
    Write-Host "  frontend  :5173   $fe"
}

switch ($Action) {
    "start"   { Start-Stack }
    "stop"    {
        Info "Stopping the stack ..."
        Stop-Stack
        if (-not (Port-Up 8000) -and -not (Port-Up 5173)) { Ok "Stopped - ports 8000 and 5173 are free." }
        else { Warn "Some ports still busy - run .\stack.ps1 stop again." }
    }
    "restart" { Info "Restarting ..."; Stop-Stack; Start-Stack }
    "status"  { Show-Status }
}
