<#
  stack.ps1 - one command to run the SalesIntel_AI stack (local or shared).

  From the repo root:
    .\stack.ps1                 # start LOCAL (backend :8000 + frontend :5173), localhost only
    .\stack.ps1 start           # same as above
    .\stack.ps1 share           # start in SHARE mode + open a public tunnel, print the URL
    .\stack.ps1 stop            # stop everything (servers + tunnel), free the ports
    .\stack.ps1 restart         # stop then start (local)
    .\stack.ps1 status          # show what's up (incl. the share URL, if any)

  `share` extras:
    .\stack.ps1 share -Provider cloudflare   # force a random Cloudflare tunnel
    .\stack.ps1 share -Domain my.ngrok-free.dev

  Everything runs detached in the background, logging to .logs\. PIDs are tracked in
  .logs\*.pid so `stop` tree-kills them (no orphaned servers or tunnels). Windows /
  PowerShell only (macOS/Linux: ./stack.sh, local only). First-time setup: RUNBOOK section 2.
  Sharing details (fixed URL, providers, troubleshooting): docs\SHARING.md.
#>
param(
    [ValidateSet("start", "share", "stop", "restart", "status")]
    [string]$Action = "start",
    [string]$Domain,
    [ValidateSet("auto", "ngrok", "cloudflare")]
    [string]$Provider = "auto"
)

$ErrorActionPreference = "Stop"
$root     = $PSScriptRoot
$backend  = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$logDir   = Join-Path $root ".logs"
$py       = Join-Path $backend ".venv\Scripts\python.exe"
$cf       = Join-Path $env:USERPROFILE "bin\cloudflared.exe"
$ngrok    = Join-Path $env:USERPROFILE "bin\ngrok.exe"
$cfgFile  = Join-Path $root "share.config"
$urlFile  = Join-Path $logDir "tunnel.url"

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m)   { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Rule()   { Write-Host ("-" * 62) -ForegroundColor DarkGray }

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Port-Up([int]$port) {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Kill-Tree([int]$procId) {
    # taskkill returns 128 when the PID is already gone; swallow it so the script
    # doesn't exit non-zero on a clean stop.
    if ($procId) { cmd /c "taskkill /F /T /PID $procId >nul 2>&1" | Out-Null; $global:LASTEXITCODE = 0 }
}

function Stop-Stack {
    # 1) tree-kill the processes we recorded at start (servers + tunnel)
    foreach ($name in "backend", "frontend", "tunnel") {
        $pidFile = Join-Path $logDir "$name.pid"
        if (Test-Path $pidFile) {
            $procId = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
            Kill-Tree ([int]($procId -as [int]))
            Remove-Item $pidFile -ErrorAction SilentlyContinue
        }
    }
    Remove-Item $urlFile -ErrorAction SilentlyContinue
    # 2) fallback: tree-kill whatever still holds the ports (clears inherited/orphan sockets)
    foreach ($port in 8000, 5173) {
        $owners = @((Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).OwningProcess) | Sort-Object -Unique
        foreach ($procId in $owners) { Kill-Tree ([int]$procId) }
    }
    # 3) last resort: sweep our own uvicorn workers + any tunnel binaries
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'uvicorn' -and $_.CommandLine -match 'app\.main' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Get-Process -Name cloudflared, ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 800
}

# Starts backend + frontend detached; frontend in share mode when $share. Returns $true if frontend answered.
function Start-Servers([bool]$share) {
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

    $feCmd = if ($share) { "npm run dev:share" } else { "npm run dev" }
    $mode  = if ($share) { " (share mode)" } else { "" }
    Info "Starting frontend -> http://localhost:5173$mode ..."
    $fe = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", $feCmd `
        -WorkingDirectory $frontend `
        -RedirectStandardOutput (Join-Path $logDir "frontend.out.log") `
        -RedirectStandardError  (Join-Path $logDir "frontend.err.log") `
        -WindowStyle Hidden -PassThru
    $fe.Id | Out-File (Join-Path $logDir "frontend.pid") -Encoding ascii

    $beOk = $false
    foreach ($i in 1..60) {
        try { if ((Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 2).status -eq "ok") { $beOk = $true; break } } catch { Start-Sleep -Milliseconds 700 }
    }
    $feOk = $false
    foreach ($i in 1..60) {
        try { if ((Invoke-WebRequest "http://localhost:5173" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $feOk = $true; break } } catch { Start-Sleep -Milliseconds 700 }
    }
    if ($beOk) { Ok "  Backend   UP    http://localhost:8000   (API docs: /docs)" }
    else       { Warn "  Backend   ...   not answering - see .logs\backend.err.log" }
    if ($feOk) { Ok "  Frontend  UP    http://localhost:5173$mode" }
    else       { Warn "  Frontend  ...   not answering - see .logs\frontend.out.log" }
    return $feOk
}

function Start-Stack {
    Start-Servers $false | Out-Null
    Write-Host ""
    Info "Open http://localhost:5173    (stop with: .\stack.ps1 stop)"
}

function Resolve-Domain {
    $d = $Domain
    if (-not $d) { $d = $env:NGROK_DOMAIN }
    if (-not $d -and (Test-Path $cfgFile)) {
        $line = Get-Content $cfgFile | Where-Object { $_ -match "^\s*NGROK_DOMAIN\s*=" } | Select-Object -First 1
        if ($line) { $d = ($line -split "=", 2)[1].Trim() }
    }
    return ($d -replace "^https?://", "").TrimEnd("/")
}

function Start-Share {
    $dom = Resolve-Domain
    $ngrokReady = (Test-Path $ngrok) -and (Test-Path (Join-Path $env:LOCALAPPDATA "ngrok\ngrok.yml"))
    $useNgrok = $false
    switch ($Provider) {
        "ngrok"      { $useNgrok = $true }
        "cloudflare" { $useNgrok = $false }
        default {
            if ($dom -and $ngrokReady) { $useNgrok = $true }
            elseif ($dom -and -not $ngrokReady) { Warn "NGROK_DOMAIN set but ngrok not authenticated - falling back to Cloudflare. (docs\SHARING.md)" }
        }
    }
    if ($useNgrok) {
        if (-not $dom) { throw "Provider 'ngrok' needs a domain (share.config NGROK_DOMAIN or -Domain)." }
        if (-not (Test-Path $ngrok)) { throw "ngrok not found at $ngrok (see docs\SHARING.md)." }
    } elseif (-not (Test-Path $cf)) {
        throw "cloudflared not found at $cf (see docs\SHARING.md)."
    }

    $feOk = Start-Servers $true
    if (-not $feOk) { Warn "Frontend not up yet - the tunnel may 502 until it finishes booting." }

    Info "Opening $(if ($useNgrok) { 'ngrok' } else { 'Cloudflare' }) tunnel ..."
    if ($useNgrok) {
        $publicUrl = "https://$dom"
        $t = Start-Process -FilePath $ngrok `
            -ArgumentList "http", "5173", "--url", "https://$dom", "--log", (Join-Path $logDir "ngrok.log") `
            -WindowStyle Hidden -PassThru
        $t.Id | Out-File (Join-Path $logDir "tunnel.pid") -Encoding ascii
    } else {
        $cfLog = Join-Path $logDir "cloudflared.log"
        "" | Set-Content -Path $cfLog
        $t = Start-Process -FilePath $cf `
            -ArgumentList "tunnel", "--url", "http://localhost:5173", "--logfile", $cfLog `
            -WindowStyle Hidden -PassThru
        $t.Id | Out-File (Join-Path $logDir "tunnel.pid") -Encoding ascii
        $publicUrl = $null
        foreach ($i in 1..30) {
            $m = Select-String -Path $cfLog -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($m) { $publicUrl = $m.Matches[0].Value; break }
            Start-Sleep -Seconds 1
        }
    }

    Write-Host ""
    if ($publicUrl) {
        $publicUrl | Out-File $urlFile -Encoding ascii
        try { Set-Clipboard -Value $publicUrl } catch {}
        Rule
        Ok  "  SHARE THIS URL$(if ($useNgrok) { ' (fixed)' } else { ' (random this run)' }):"
        Ok  "      $publicUrl"
        Info "  (copied to your clipboard)"
        Rule
        Info "Tunnel + app run in the background. Stop everything with: .\stack.ps1 stop"
    } else {
        Warn "Could not read the tunnel URL - check .logs\cloudflared.log, or re-run."
    }
}

function Show-Status {
    $be = if (Port-Up 8000) { "UP" } else { "down" }
    $fe = if (Port-Up 5173) { "UP" } else { "down" }
    Write-Host "  backend   :8000   $be"
    Write-Host "  frontend  :5173   $fe"
    if (Test-Path $urlFile) { Write-Host ("  tunnel    (share) " + (Get-Content $urlFile | Select-Object -First 1)) }
}

switch ($Action) {
    "start"   { Start-Stack }
    "share"   { Start-Share }
    "stop"    {
        Info "Stopping the stack ..."
        Stop-Stack
        if (-not (Port-Up 8000) -and -not (Port-Up 5173)) { Ok "Stopped - ports 8000 and 5173 are free." }
        else { Warn "Some ports still busy - run .\stack.ps1 stop again." }
    }
    "restart" { Info "Restarting ..."; Stop-Stack; Start-Stack }
    "status"  { Show-Status }
}
