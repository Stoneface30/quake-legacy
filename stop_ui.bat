@echo off
REM ============================================================
REM  Creative Suite UI stopper
REM  Kills whatever process is holding port 8765 (the uvicorn
REM  server). Use this if Ctrl+C didn't release the port or the
REM  server is running detached.
REM ============================================================

setlocal

echo.
echo [creative_suite] stopping server on 127.0.0.1:8765...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$conns = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue;" ^
    "if (-not $conns) { Write-Host '[creative_suite] nothing listening on 8765 -- already stopped.'; exit 0 }" ^
    "foreach ($c in $conns) {" ^
    "  $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue;" ^
    "  if ($p) {" ^
    "    Write-Host ('[creative_suite] killing ' + $p.ProcessName + ' pid=' + $p.Id);" ^
    "    Stop-Process -Id $p.Id -Force" ^
    "  }" ^
    "};" ^
    "Start-Sleep -Seconds 1;" ^
    "if (Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue) {" ^
    "  Write-Host '[creative_suite] WARNING: port still bound after kill attempt'; exit 1" ^
    "} else {" ^
    "  Write-Host '[creative_suite] port 8765 is free.'; exit 0" ^
    "}"

endlocal
