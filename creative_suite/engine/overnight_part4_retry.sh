#!/usr/bin/env bash
# overnight_part4_retry.sh — runs AFTER overnight_queue finishes.
# Waits for orchestrator PID to die, then retries Part 4 preview, then
# appends to OVERNIGHT_REPORT.md.
set -uo pipefail

ROOT="G:/QUAKE_LEGACY"
LOG="$ROOT/output/_overnight_part4_retry_$(date +%Y%m%d_%H%M%S).log"
REPORT="$ROOT/OVERNIGHT_REPORT.md"
ORCH_PID="${ORCH_PID:-7046}"

echo "=== PART 4 RETRY ===" | tee "$LOG"
date | tee -a "$LOG"
echo "Waiting for orchestrator PID $ORCH_PID..." | tee -a "$LOG"

while kill -0 "$ORCH_PID" 2>/dev/null; do
    sleep 120
done
echo "[$(date +%H:%M:%S)] Orchestrator finished" | tee -a "$LOG"

# Rotate fresh stems for Part 4
cd "$ROOT"
PYTHONIOENCODING=utf-8 python -u phase1/music/rotate_fresh_stems.py --part 4 >> "$LOG" 2>&1

# Render Part 4 preview
OUT="$ROOT/output/Part04_v14_PREVIEW_freshstems.mp4"
t0=$(date +%s)
PYTHONIOENCODING=utf-8 python -u -m phase1.render_part_v6 \
    --part 4 --profile preview \
    --output "output/Part04_v14_PREVIEW_freshstems.mp4" \
    >> "$LOG" 2>&1
rc=$?
t1=$(date +%s)
elapsed=$((t1 - t0))

result="FAIL_rc${rc}"
if [ -f "$OUT" ]; then
    sz=$(stat -c%s "$OUT" 2>/dev/null)
    dur=$("$ROOT/tools/ffmpeg/ffprobe.exe" -v error -show_entries \
        format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" 2>&1)
    sz_mb=$((sz / 1024 / 1024))
    result="OK_${sz_mb}MB_${dur}s_${elapsed}s"
fi

# Append to report
{
    echo ""
    echo "---"
    echo ""
    echo "## Part 4 Retry"
    echo ""
    echo "- Output: \`Part04_v14_PREVIEW_freshstems.mp4\`"
    echo "- Result: $result"
    echo "- Elapsed: ${elapsed}s"
    echo "- Log: \`$LOG\`"
    M="$ROOT/phase1/music/part04_fresh_stems.json"
    if [ -f "$M" ]; then
        echo ""
        echo "### Stems used"
        echo '```json'
        cat "$M"
        echo '```'
    fi
} >> "$REPORT"

echo "[$(date +%H:%M:%S)] Part 4 retry done: $result" | tee -a "$LOG"
