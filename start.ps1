# RSA Question Generator — One-click launcher
# Run this once on any new PC: powershell -ExecutionPolicy Bypass -File start.ps1

$AppDir = Join-Path $PSScriptRoot "rsa_app"
$SecretsDir = Join-Path $AppDir ".streamlit"
$SecretsFile = Join-Path $SecretsDir "secrets.toml"
$EnvFile = Join-Path $PSScriptRoot ".env"
$CloudflaredPath = "C:\cloudflared\cloudflared.exe"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  RSA Question Generator — Launcher  " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check Python ────────────────────────────────────────────────────
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "      OK: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Python not found. Install from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ── Step 2: Install requirements ───────────────────────────────────────────
Write-Host "[2/4] Installing requirements..." -ForegroundColor Yellow
pip install -r (Join-Path $AppDir "requirements.txt") -q
Write-Host "      OK" -ForegroundColor Green

# ── Step 3: API key setup ───────────────────────────────────────────────────
Write-Host "[3/4] Checking API key..." -ForegroundColor Yellow
$ApiKey = ""
if (Test-Path $EnvFile) {
    $envLine = Get-Content $EnvFile | Where-Object { $_ -match "^ANTHROPIC_API_KEY=" }
    if ($envLine) { $ApiKey = $envLine -replace "^ANTHROPIC_API_KEY=", "" }
}
if (-not $ApiKey) {
    Write-Host ""
    Write-Host "      First time setup — enter the Anthropic API key:" -ForegroundColor Magenta
    $ApiKey = Read-Host "      API Key"
    Set-Content -Path $EnvFile -Value "ANTHROPIC_API_KEY=$ApiKey" -Encoding utf8
    Write-Host "      Saved to .env (won't ask again)" -ForegroundColor Green
} else {
    Write-Host "      OK: key loaded from .env" -ForegroundColor Green
}
New-Item -ItemType Directory -Path $SecretsDir -Force | Out-Null
Set-Content -Path $SecretsFile -Value "ANTHROPIC_API_KEY = `"$ApiKey`"" -Encoding utf8

# ── Step 4: Check cloudflared ───────────────────────────────────────────────
Write-Host "[4/4] Checking Cloudflare tunnel..." -ForegroundColor Yellow
$cfInstalled = $false
if (Test-Path $CloudflaredPath) {
    $cfInstalled = $true
} elseif (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    $CloudflaredPath = "cloudflared"
    $cfInstalled = $true
}

if (-not $cfInstalled) {
    Write-Host ""
    Write-Host "      cloudflared not found. Downloading..." -ForegroundColor Magenta
    New-Item -ItemType Directory -Path "C:\cloudflared" -Force | Out-Null
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $CloudflaredPath
    Write-Host "      Downloaded to C:\cloudflared\cloudflared.exe" -ForegroundColor Green
}

# ── Launch ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Starting app..." -ForegroundColor Cyan

# Kill any existing instances
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

# Start Streamlit
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$AppDir'; streamlit run app.py --server.port 8501 --server.headless true"
Start-Sleep -Seconds 4

# Start Cloudflare tunnel and capture URL
$tunnelLog = Join-Path $env:TEMP "cf_tunnel.log"
Start-Process -FilePath $CloudflaredPath -ArgumentList "tunnel --url http://localhost:8501 --logfile `"$tunnelLog`"" -WindowStyle Hidden

# Wait for tunnel URL to appear
Write-Host ""
Write-Host "Waiting for tunnel URL..." -ForegroundColor Yellow
$url = ""
$attempts = 0
while ($url -eq "" -and $attempts -lt 30) {
    Start-Sleep -Seconds 2
    $attempts++
    if (Test-Path $tunnelLog) {
        $logContent = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
        if ($logContent -match "https://[a-z0-9\-]+\.trycloudflare\.com") {
            $url = $Matches[0]
        }
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  APP IS LIVE!" -ForegroundColor Green
Write-Host ""
if ($url -ne "") {
    Write-Host "  Share this link:" -ForegroundColor White
    Write-Host "  $url" -ForegroundColor Cyan
} else {
    Write-Host "  Local: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "  (Check tunnel window for public URL)" -ForegroundColor Gray
}
Write-Host ""
Write-Host "  Keep this window open while using the app." -ForegroundColor Gray
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Open browser
Start-Process "http://localhost:8501"

Read-Host "Press Enter to stop everything and exit"

# Cleanup
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Stopped." -ForegroundColor Gray
