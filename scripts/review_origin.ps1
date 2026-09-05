# Supervised launcher for the review origin.
#
# WHY THIS EXISTS. The reviewer went down twice in one day. Once because
# nothing was running it, and once because it had been started with
# `nohup ... &` from an agent's tool shell -- which dies with that shell. The
# public hostname gives no warning either way: Cloudflare Access answers a
# request with a 302 to its login page whether or not the origin behind it is
# alive, so the site looks healthy right up until you finish signing in.
#
# This is deliberately a supervised loop rather than a Windows service: no
# admin rights, no installer, and the log is a plain file the user can read.
# Register it with scripts/install_review_task.ps1 to have it start at logon.
#
# BINDS TO LOOPBACK ON PURPOSE. cloudflared runs on this machine and connects
# to http://localhost:8766, so the origin never needs to listen on the LAN.
# The Cloudflare Access guard keys on the Host header, so an origin reachable
# at a raw LAN address would be reachable without signing in. Do not change
# 127.0.0.1 to 0.0.0.0.

$ErrorActionPreference = 'Stop'

$Root    = 'G:\QUAKE_LEGACY'
$Python  = 'E:\PersonalAI\venv\Scripts\python.exe'
$Port    = 8766
$LogDir  = Join-Path $Root 'output'
$Log     = Join-Path $LogDir 'review_origin.log'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log([string]$Message) {
    $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -Path $Log -Value $line -Encoding utf8
}

Write-Log "supervisor starting (pid $PID)"

# Restart backoff. A crash loop caused by a genuine defect must not spin the
# CPU or fill the disk with identical tracebacks; it should be visibly slow
# and obviously wrong in the log.
$delay = 2
while ($true) {
    try {
        $probe = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" `
            -TimeoutSec 4 -UseBasicParsing -ErrorAction Stop
        if ($probe.StatusCode -eq 200) {
            # Somebody else is serving this port. Do not start a second one.
            $delay = 2
            Start-Sleep -Seconds 15
            continue
        }
    } catch {
        # Not answering: ours to start.
    }

    Write-Log "starting uvicorn on 127.0.0.1:$Port"
    $args = @('-m', 'uvicorn', 'creative_suite.app:create_app', '--factory',
              '--host', '127.0.0.1', '--port', "$Port")
    $started = Get-Date
    $proc = Start-Process -FilePath $Python -ArgumentList $args `
        -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $LogDir 'review_origin.out.log') `
        -RedirectStandardError  (Join-Path $LogDir 'review_origin.err.log')
    $proc.WaitForExit()
    # A process that served for a while and then stopped is a RESTART, not a
    # crash loop, so it must not inherit the previous backoff. Without this
    # the delay ratchets up across ordinary deploys until the reviewer is
    # down for a minute every time it is restarted.
    $ranFor = (Get-Date) - $started
    if ($ranFor.TotalSeconds -gt 60) { $delay = 2 }
    Write-Log "uvicorn exited after $([int]$ranFor.TotalSeconds)s; restarting in ${delay}s"
    Start-Sleep -Seconds $delay
    $delay = [Math]::Min($delay * 2, 60)
}
