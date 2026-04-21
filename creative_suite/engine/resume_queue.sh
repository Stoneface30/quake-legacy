#!/usr/bin/env bash
# resume_queue.sh — drive render_supervisor.sh across a list of parts.
#
# Usage: resume_queue.sh <part1> [part2 ...]
#   or:  resume_queue.sh all     # parts 4-12
#
# For each part:
#   - output path: output/PartNN_v{99}_PREVIEW_resume.mp4
#   - calls render_supervisor.sh with default 3 attempts
#   - collects result, appends to OVERNIGHT_REPORT.md
set -uo pipefail

ROOT="G:/QUAKE_LEGACY"
cd "$ROOT" || exit 3

if [[ "${1:-}" == "all" ]]; then
    PARTS=(4 5 6 7 8 9 10 11 12)
else
    PARTS=("$@")
fi

if [[ "${#PARTS[@]}" -eq 0 ]]; then
    echo "usage: $0 <part1> [part2 ...] | all" >&2
    exit 3
fi

LOG="$ROOT/output/_resume_$(date +%Y%m%d_%H%M%S).log"
REPORT="$ROOT/OVERNIGHT_REPORT.md"

echo "=== RESUME QUEUE: ${PARTS[*]} ===" | tee "$LOG"
date | tee -a "$LOG"

declare -A RESULTS

for PART in "${PARTS[@]}"; do
    PP=$(printf "%02d" "$PART")
    OUT="$ROOT/output/Part${PP}_v99_PREVIEW_resume.mp4"

    echo "" | tee -a "$LOG"
    echo "[$(date +%H:%M:%S)] === Part $PART ===" | tee -a "$LOG"

    bash phase1/render_supervisor.sh "$PART" "$OUT" 3 >> "$LOG" 2>&1
    rc=$?

    case "$rc" in
        0)
            sz=$(stat -c%s "$OUT" 2>/dev/null || echo 0)
            sz_mb=$((sz / 1024 / 1024))
            dur=$("$ROOT/tools/ffmpeg/ffprobe.exe" -v error \
                -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
                "$OUT" 2>/dev/null || echo "?")
            RESULTS[$PART]="OK_${sz_mb}MB_${dur}s"
            ;;
        2) RESULTS[$PART]="HALT_DISK" ;;
        *) RESULTS[$PART]="FAIL_rc${rc}" ;;
    esac

    echo "  => Part $PART: ${RESULTS[$PART]}" | tee -a "$LOG"

    # Disk abort is global — bail out of the queue
    [[ "$rc" -eq 2 ]] && break
done

{
    echo ""
    echo "---"
    echo ""
    echo "## Resume Queue"
    echo ""
    echo "**When:** $(date)"
    echo "**Log:** \`$LOG\`"
    echo ""
    echo "| Part | Output | Status |"
    echo "|------|--------|--------|"
    for PART in "${PARTS[@]}"; do
        PP=$(printf "%02d" "$PART")
        echo "| $PART | \`Part${PP}_v99_PREVIEW_resume.mp4\` | ${RESULTS[$PART]:-NOT_RUN} |"
    done
} >> "$REPORT"

echo "[$(date +%H:%M:%S)] === RESUME DONE ===" | tee -a "$LOG"
