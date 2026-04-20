#!/usr/bin/env bash
# morning_retries.sh — retry Part 4, 6, 7 (only parts with clip lists that
# failed overnight). Parts 8-12 skipped: no clip_lists/part0N_styleb.txt.
set -uo pipefail

ROOT="G:/QUAKE_LEGACY"
LOG="$ROOT/output/_morning_retries_$(date +%Y%m%d_%H%M%S).log"
REPORT="$ROOT/OVERNIGHT_REPORT.md"

echo "=== MORNING RETRIES (Parts 4, 6, 7) ===" | tee "$LOG"
date | tee -a "$LOG"

declare -A RESULTS

for PART in 4 6 7; do
    PP=$(printf "%02d" "$PART")
    OUT="$ROOT/output/Part${PP}_v$((15+PART))_PREVIEW_retry.mp4"
    echo "" | tee -a "$LOG"
    echo "[$(date +%H:%M:%S)] === PART $PART RETRY ===" | tee -a "$LOG"

    cd "$ROOT"
    PYTHONIOENCODING=utf-8 python -u phase1/music/rotate_fresh_stems.py \
        --part "$PART" --seed $((PART * 13)) >> "$LOG" 2>&1

    t0=$(date +%s)
    PYTHONIOENCODING=utf-8 python -u -m phase1.render_part_v6 \
        --part "$PART" --profile preview \
        --output "output/Part${PP}_v$((15+PART))_PREVIEW_retry.mp4" \
        >> "$LOG" 2>&1
    rc=$?
    t1=$(date +%s)
    elapsed=$((t1 - t0))

    if [ "$rc" -eq 0 ] && [ -f "$OUT" ]; then
        sz=$(stat -c%s "$OUT")
        dur=$("$ROOT/tools/ffmpeg/ffprobe.exe" -v error -show_entries \
            format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT")
        sz_mb=$((sz / 1024 / 1024))
        RESULTS[$PART]="OK_${sz_mb}MB_${dur}s_${elapsed}s"
    else
        # Scrub any corrupt normalize artifacts this render just made
        python phase1/scrub_normalize_cache.py >> "$LOG" 2>&1
        RESULTS[$PART]="FAIL_rc${rc}_${elapsed}s"
    fi
    echo "  result: ${RESULTS[$PART]}" | tee -a "$LOG"

    # Disk watchdog
    free_gb=$(df -BG "$ROOT" | tail -1 | awk '{print $4}' | tr -d 'G')
    if [ "${free_gb:-99}" -lt 15 ] 2>/dev/null; then
        echo "  DISK <15GB — halting retries" | tee -a "$LOG"
        break
    fi
done

# Append to report
{
    echo ""
    echo "---"
    echo ""
    echo "## Morning Retries"
    echo ""
    echo "**When:** $(date)"
    echo "**Log:** \`$LOG\`"
    echo ""
    echo "| Part | Output | Status |"
    echo "|------|--------|--------|"
    for PART in 4 6 7; do
        PP=$(printf "%02d" "$PART")
        echo "| $PART | \`Part${PP}_v$((15+PART))_PREVIEW_retry.mp4\` | ${RESULTS[$PART]:-NOT_RUN} |"
    done
} >> "$REPORT"

echo "[$(date +%H:%M:%S)] === MORNING DONE ===" | tee -a "$LOG"
