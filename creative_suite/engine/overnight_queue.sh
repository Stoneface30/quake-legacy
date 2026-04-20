#!/usr/bin/env bash
# overnight_queue.sh — wait for Part 4 in flight, then render Parts 5-12
# sequentially with fresh stems, preview profile, self-check, report.
set -uo pipefail

ROOT="G:/QUAKE_LEGACY"
LOG="$ROOT/output/_overnight_$(date +%Y%m%d_%H%M%S).log"
REPORT="$ROOT/OVERNIGHT_REPORT.md"
P4_PID="${P4_PID:-97604}"

mkdir -p "$ROOT/output"

echo "=== OVERNIGHT QUEUE ===" | tee "$LOG"
date | tee -a "$LOG"
echo "Part 4 in-flight PID: $P4_PID" | tee -a "$LOG"

# -------- wait for Part 4 to complete --------
while kill -0 "$P4_PID" 2>/dev/null; do
    echo "[$(date +%H:%M:%S)] Part 4 PID $P4_PID still alive, sleeping 120s" >> "$LOG"
    sleep 120
done
echo "[$(date +%H:%M:%S)] Part 4 finished" | tee -a "$LOG"

# Verify Part 4 output exists
P4_OUT="$ROOT/output/Part04_v13_PREVIEW_freshstems.mp4"
if [ -f "$P4_OUT" ]; then
    P4_SIZE=$(du -h "$P4_OUT" | cut -f1)
    P4_DUR=$("$ROOT/tools/ffmpeg/ffprobe.exe" -v error -show_entries \
        format=duration -of default=noprint_wrappers=1:nokey=1 "$P4_OUT" 2>&1)
    echo "  part04: $P4_SIZE, ${P4_DUR}s" | tee -a "$LOG"
else
    echo "  part04: MISSING — continuing anyway" | tee -a "$LOG"
fi

# -------- Parts 5-12 queue --------
declare -A RESULTS
for PART in 5 6 7 8 9 10 11 12; do
    PP=$(printf "%02d" "$PART")
    OUT="$ROOT/output/Part${PP}_v1_PREVIEW_freshstems.mp4"
    echo "" | tee -a "$LOG"
    echo "[$(date +%H:%M:%S)] === PART $PART ===" | tee -a "$LOG"

    # 1. rotate fresh stems
    echo "  rotating fresh stems..." >> "$LOG"
    cd "$ROOT"
    PYTHONIOENCODING=utf-8 python -u phase1/music/rotate_fresh_stems.py \
        --part "$PART" >> "$LOG" 2>&1
    rc_rot=$?
    if [ "$rc_rot" -ne 0 ]; then
        echo "  ROTATE FAIL rc=$rc_rot — skip part $PART" | tee -a "$LOG"
        RESULTS[$PART]="ROTATE_FAIL"
        continue
    fi

    # 2. render preview
    echo "  rendering preview..." >> "$LOG"
    t0=$(date +%s)
    cd "$ROOT"
    PYTHONIOENCODING=utf-8 python -u -m phase1.render_part_v6 \
        --part "$PART" \
        --profile preview \
        --output "output/Part${PP}_v1_PREVIEW_freshstems.mp4" \
        >> "$LOG" 2>&1
    rc_render=$?
    t1=$(date +%s)
    elapsed=$((t1 - t0))

    if [ "$rc_render" -ne 0 ]; then
        echo "  RENDER FAIL rc=$rc_render elapsed=${elapsed}s" | tee -a "$LOG"
        RESULTS[$PART]="RENDER_FAIL_rc${rc_render}_${elapsed}s"
        continue
    fi

    # 3. self-check: file exists, size > 10MB, duration > 60s
    if [ ! -f "$OUT" ]; then
        echo "  OUTPUT MISSING: $OUT" | tee -a "$LOG"
        RESULTS[$PART]="NO_OUTPUT"
        continue
    fi
    sz=$(stat -c%s "$OUT" 2>/dev/null)
    dur=$("$ROOT/tools/ffmpeg/ffprobe.exe" -v error -show_entries \
        format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" 2>&1)
    sz_mb=$((sz / 1024 / 1024))
    pass="OK"
    [ "$sz_mb" -lt 10 ] && pass="TOO_SMALL"
    dur_int=${dur%.*}
    [ "${dur_int:-0}" -lt 60 ] 2>/dev/null && pass="TOO_SHORT"
    echo "  self-check: ${sz_mb}MB  ${dur}s  ${pass}  elapsed=${elapsed}s" \
        | tee -a "$LOG"
    RESULTS[$PART]="${pass}_${sz_mb}MB_${dur}s_${elapsed}s"

    # disk watchdog: if <10GB free, stop queue
    free_gb=$(df -BG "$ROOT" | tail -1 | awk '{print $4}' | tr -d 'G')
    if [ "${free_gb:-99}" -lt 10 ] 2>/dev/null; then
        echo "  DISK <10GB — halting queue" | tee -a "$LOG"
        RESULTS[$PART]="${RESULTS[$PART]}_DISK_HALT"
        break
    fi
done

# -------- final report --------
{
    echo "# QUAKE LEGACY — Overnight Render Report"
    echo ""
    echo "**Generated:** $(date)"
    echo "**Log:** \`$LOG\`"
    echo ""
    echo "## Results"
    echo ""
    echo "| Part | Output | Status |"
    echo "|------|--------|--------|"
    if [ -f "$P4_OUT" ]; then
        echo "| 4 | \`Part04_v13_PREVIEW_freshstems.mp4\` | $(du -h "$P4_OUT" | cut -f1) |"
    else
        echo "| 4 | (missing) | FAIL |"
    fi
    for PART in 5 6 7 8 9 10 11 12; do
        PP=$(printf "%02d" "$PART")
        echo "| $PART | \`Part${PP}_v1_PREVIEW_freshstems.mp4\` | ${RESULTS[$PART]:-NOT_RUN} |"
    done
    echo ""
    echo "## Disk"
    df -h "$ROOT" | tail -1
    echo ""
    echo "## Library"
    echo "- total mp3: $(ls "$ROOT/phase1/music/library/"*.mp3 2>/dev/null | wc -l)"
    echo "- hardtek:   $(ls "$ROOT/phase1/music/library/HARDTEK_"*.mp3 2>/dev/null | wc -l)"
    echo ""
    echo "## Fresh Stems Used"
    for PART in 5 6 7 8 9 10 11 12; do
        PP=$(printf "%02d" "$PART")
        M="$ROOT/phase1/music/part${PP}_fresh_stems.json"
        if [ -f "$M" ]; then
            echo "### Part $PART"
            echo '```json'
            cat "$M"
            echo '```'
        fi
    done
} > "$REPORT"

echo "" | tee -a "$LOG"
echo "[$(date +%H:%M:%S)] === OVERNIGHT COMPLETE ===" | tee -a "$LOG"
echo "Report: $REPORT" | tee -a "$LOG"
