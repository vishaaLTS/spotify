# launch.ps1 - Start Flask + localhost.run tunnel persistently
# Run this in a PowerShell window: powershell -ExecutionPolicy Bypass -File launch.ps1

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TunnelLog = Join-Path $AppDir "tunnel_url.txt"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Spotify Recommendation Engine Launcher" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Kill any existing processes on port 5000
$existing = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[*] Stopping existing server on port 5000..." -ForegroundColor Yellow
    $existing | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}

# Start Flask in background
Write-Host "[*] Starting Flask server..." -ForegroundColor Yellow
$flask = Start-Process -NoNewWindow -FilePath "python" `
    -ArgumentList "run_server.py" `
    -WorkingDirectory $AppDir `
    -PassThru

Start-Sleep -Seconds 8  # wait for Flask + ML model load

# Check Flask is up
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 5
    Write-Host "[OK] Flask is running (HTTP $($resp.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Flask did not start. Check run_server.py" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[*] Starting public tunnel via localhost.run..." -ForegroundColor Yellow
Write-Host "    (this may take a few seconds)" -ForegroundColor Gray
Write-Host ""

# Clear log
"" | Set-Content $TunnelLog

# Run SSH tunnel - keep alive in THIS window
$sshArgs = "-o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=99999 -R 80:localhost:5000 nokey@localhost.run"

# Start SSH, capture output, display URL
$job = Start-Job -ScriptBlock {
    param($args_, $log)
    & ssh $args_.Split(' ') 2>&1 | Tee-Object -FilePath $log
} -ArgumentList $sshArgs, $TunnelLog

# Wait for URL to appear in log
$timeout = 15
$elapsed = 0
$url = $null
while ($elapsed -lt $timeout -and -not $url) {
    Start-Sleep -Seconds 1
    $elapsed++
    if (Test-Path $TunnelLog) {
        $content = Get-Content $TunnelLog -Raw -ErrorAction SilentlyContinue
        if ($content -match "https://([a-f0-9]+)\.lhr\.life") {
            $url = "https://$($Matches[1]).lhr.life"
        }
    }
}

if ($url) {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Your app is LIVE at:" -ForegroundColor White
    Write-Host ""
    Write-Host "  $url" -ForegroundColor Green -BackgroundColor Black
    Write-Host ""
    Write-Host "  Local: http://localhost:5000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Share the green URL with anyone!" -ForegroundColor White
    Write-Host "  Press CTRL+C to stop everything." -ForegroundColor Yellow
    Write-Host ""
    # Open in browser
    Start-Process $url
} else {
    Write-Host "[WARN] Could not detect public URL. Check tunnel_url.txt" -ForegroundColor Yellow
    Write-Host "       App is still running at http://localhost:5000" -ForegroundColor Gray
    Start-Process "http://localhost:5000"
}

# Keep script running so tunnel stays alive
Write-Host "[*] Keeping tunnel alive. Press CTRL+C to stop." -ForegroundColor Gray
try {
    Wait-Job $job
} catch {
    # User pressed CTRL+C
}

# Cleanup
Write-Host ""
Write-Host "[*] Stopping Flask..." -ForegroundColor Yellow
Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue
Remove-Job $job -Force -ErrorAction SilentlyContinue
Write-Host "[*] Done." -ForegroundColor Green
