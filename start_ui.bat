@echo off
REM ============================================================
REM  Creative Suite UI launcher
REM  Double-click or run from any directory — always resolves to
REM  the quake-legacy project root before starting.
REM
REM  Opens the UI in your default browser after the server is up.
REM  Press Ctrl+C in this window to shut it down gracefully (the
REM  JobQueue drain + render worker cleanup will run).
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo [creative_suite] starting server on http://127.0.0.1:8765
echo [creative_suite] press Ctrl+C to stop
echo.

REM Fire the browser ~2 seconds after we start uvicorn so the tab
REM lands on a ready server instead of "connection refused".
REM Uses PowerShell instead of `timeout` to avoid collision with the
REM git-bash coreutils `timeout` binary when this .bat is invoked from
REM a bash environment.
start "" /b powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8765/'"

python -m creative_suite

REM If we got here with a nonzero exit code, the port-check or
REM uvicorn itself complained. Pause so the user sees the message
REM before the window closes.
if errorlevel 1 (
    echo.
    echo [creative_suite] exited with error code %errorlevel%
    echo.
    pause
)

endlocal
