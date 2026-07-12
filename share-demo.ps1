<#
  share-demo.ps1  -  One-command demo sharing for SalesIntel AI.

  Starts the backend (:8000) and the frontend (:5173, in shared-demo mode so all
  API calls ride the same origin), then opens a public https tunnel and prints a
  URL you can send to non-technical peers.

  QUICK START
      npm run share      (from frontend\)   -or-   .\share-demo.ps1   (from repo root)

  FIXED URL and full details: see docs\SHARING.md.
  Briefs need a real LLM key in backend\.env (LLM_API_KEY=...) or they error.
#>
param(
    [string]$Domain,                                  # override the ngrok static domain
    [ValidateSet("auto", "ngrok", "cloudflare")]
    [string]$Provider = "auto"                         # force a tunnel provider
)

$ErrorActionPreference = "Stop"
$root      = $PSScriptRoot
$backend   = Join-Path $root "backend"
$frontend  = Join-Path $root "frontend"
$cf        = Join-Path $env:USERPROFILE "bin\cloudflared.exe"
$ngrok     = Join-Path $env:USERPROFILE "bin\ngrok.exe"
$cfgFile   = Join-Path $root "share.config"

function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m)   { Write-Host $m -ForegroundColor Green }
function Rule()   { Write-Host ("-" * 66) -ForegroundColor DarkGray }

# --- resolve the ngrok static domain (param > env > share.config) ------------
if (-not $Domain) { $Domain = $env:NGROK_DOMAIN }
if (-not $Domain -and (Test-Path $cfgFile)) {
    $line = Get-Content $cfgFile | Where-Object { $_ -match "^\s*NGROK_DOMAIN\s*=" } | Select-Object -First 1
    if ($line) { $Domain = ($line -split "=", 2)[1].Trim() }
}
$Domain = ($Domain -replace "^https?://", "").TrimEnd("/")   # tolerate a pasted full URL

$ngrokReady = (Test-Path $ngrok) -and (Test-Path (Join-Path $env:LOCALAPPDATA "ngrok\ngrok.yml"))

# --- decide provider ---------------------------------------------------------
$useNgrok = $false
switch ($Provider) {
    "ngrok"      { $useNgrok = $true }
    "cloudflare" { $useNgrok = $false }
    default {
        if ($Domain -and $ngrokReady) { $useNgrok = $true }
        elseif ($Domain -and -not $ngrokReady) {
            Warn "NGROK_DOMAIN is set ($Domain) but ngrok is not authenticated yet."
            Warn "Run once:  ngrok config add-authtoken <YOUR_TOKEN>   (see docs\SHARING.md)."
            Warn "Falling back to a random Cloudflare URL for now.`n"
        }
    }
}

# --- sanity checks -----------------------------------------------------------
if ($useNgrok) {
    if (-not $Domain) { throw "Provider 'ngrok' needs a domain. Set NGROK_DOMAIN in share.config or pass -Domain." }
    if (-not (Test-Path $ngrok)) { throw "ngrok not found at $ngrok. Re-download it (see docs\SHARING.md)." }
} else {
    if (-not (Test-Path $cf)) { throw "cloudflared not found at $cf. Re-download it (see docs\SHARING.md)." }
}

$envFile = Join-Path $backend ".env"
if (-not (Test-Path $envFile)) {
    Warn "WARNING: backend\.env not found. Copy .env.example to .env and set LLM_API_KEY, or briefs will error."
} else {
    $envText = Get-Content $envFile -Raw
    if ($envText -notmatch "(?m)^\s*LLM_API_KEY\s*=\s*\S" -or $envText -match "PASTE") {
        Warn "WARNING: LLM_API_KEY looks unset in backend\.env - briefs will land in status=error until you set a real key."
    }
}

# --- start backend (new window) ----------------------------------------------
Info "Starting backend on http://localhost:8000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
) -WindowStyle Normal

# --- start frontend in shared-demo mode (new window) -------------------------
Info "Starting frontend on http://localhost:5173 (shared-demo mode: vite --mode share) ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$frontend'; npm run dev:share"
) -WindowStyle Normal

# --- wait for the frontend to answer -----------------------------------------
Info "Waiting for servers to come up ..."
$ready = $false
foreach ($i in 1..40) {
    try {
        if ((Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $ready = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if ($ready) { Ok "Frontend is up." } else { Warn "Frontend did not answer in time - the tunnel may 502 until it finishes booting." }
Write-Host ""

# --- open the tunnel ---------------------------------------------------------
if ($useNgrok) {
    $publicUrl = "https://$Domain"
    try { Set-Clipboard -Value $publicUrl } catch {}
    Rule
    Ok  "  SHARE THIS URL (fixed, same every run):"
    Ok  "      $publicUrl"
    Info "  (copied to your clipboard)"
    Rule
    Info "Opening ngrok tunnel ... leave this window open for the demo. Ctrl+C to stop."
    Write-Host ""
    & $ngrok http 5173 --url "https://$Domain"
} else {
    Info "Opening Cloudflare tunnel ..."
    Info "Tip: set up a fixed ngrok URL to skip this - see docs\SHARING.md."
    # NOTE: cloudflared prints to stderr; piping it with 2>&1 under
    # ErrorActionPreference='Stop' would wrap that as a terminating error and kill
    # this script. So we run it detached to a logfile, read the URL from there,
    # then wait on the process (keeps the tunnel alive until you close this window).
    $log = Join-Path $env:TEMP "salesintel-cloudflared.log"
    "" | Set-Content -Path $log
    $proc = Start-Process $cf -ArgumentList "tunnel","--url","http://localhost:5173","--logfile",$log -PassThru -WindowStyle Hidden
    $u = $null
    foreach ($i in 1..30) {
        if (Test-Path $log) {
            $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
            if ($m) { $u = $m.Matches[0].Value; break }
        }
        Start-Sleep -Seconds 1
    }
    if ($u) {
        try { Set-Clipboard -Value $u } catch {}
        Write-Host ""
        Rule
        Ok  "  SHARE THIS URL (random this run, copied to clipboard):"
        Ok  "      $u"
        Rule
        Info "  Leave this window open for the demo. Close it (or Ctrl+C) to stop."
        Write-Host ""
    } else {
        Warn "Could not read the tunnel URL from $log - check that file, or re-run."
    }
    Wait-Process -Id $proc.Id
}
