#!/usr/bin/env bash
# render_supervisor.sh — single-part render with auto-retry (Fix #3, 2026-04-20).
#
# Usage: render_supervisor.sh <part> <output_path> [max_attempts=3]
#
# Between attempts:
#   - rotates fresh stems with a new seed (part*13 + attempt)
#   - scrubs normalize cache (deletes any mp4s poisoned by a killed ffmpeg)
#
# Exits:
#   0  success
#   1  all attempts failed
#   2  disk watchdog tripped (<10GB free)
#   3  bad args
set -uo pipefail

PART="${1:-}"
OUT="${2:-}"
MAX_ATTEMPTS="${3:-3}"

if [[ -z "$PART" || -z "$OUT" ]]; then
    echo "usage: $0 <part> <output_path> [max_attempts=3]" >&2
    exit 3
fi

ROOT="G:/QUAKE_LEGACY"
PP=$(printf "%02d" "$PART")
LOG_DIR="$ROOT/output"
LOG="$LOG_DIR/_supervisor_part${PP}_$(date +%Y%m%d_%H%M%S).log"

echo "=== SUPERVISOR Part $PART → $OUT (max $MAX_ATTEMPTS attempts) ===" | tee "$LOG"
date | tee -a "$LOG"

cd "$ROOT" || exit 3

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    # Disk watchdog — abort the part if we're below 10GB
    free_gb=$(df -BG "$ROOT" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    if [[ "${free_gb:-99}" -lt 10 ]] 2>/dev/null; then
        echo "[supervisor] DISK <10GB (${free_gb}GB) — aborting" | tee -a "$LOG"
        exit 2
    fi

    echo "" | tee -a "$LOG"
    echo "[$(date +%H:%M:%S)] --- Part $PART attempt $attempt/$MAX_ATTEMPTS ---" | tee -a "$LOG"

    # Fresh stems with a seed that varies per attempt
    seed=$((PART * 13 + attempt * 97))
    PYTHONIOENCODING=utf-8 python -u phase1/music/rotate_fresh_stems.py \
        --part "$PART" --seed "$seed" >> "$LOG" 2>&1 || {
            echo "[supervisor] rotate_fresh_stems failed (non-fatal, continuing)" | tee -a "$LOG"
        }

    t0=$(date +%s)
    PYTHONIOENCODING=utf-8 python -u -m phase1.render_part_v6 \
        --part "$PART" --profile preview \
        --output "$OUT" >> "$LOG" 2>&1
    rc=$?
    t1=$(date +%s)
    elapsed=$((t1 - t0))

    if [[ "$rc" -eq 0 && -f "$OUT" ]]; then
        sz=$(stat -c%s "$OUT" 2>/dev/null || echo 0)
        sz_mb=$((sz / 1024 / 1024))
        if [[ "$sz_mb" -ge 10 ]]; then
            echo "[supervisor] OK Part $PART (${sz_mb}MB, ${elapsed}s, attempt $attempt)" | tee -a "$LOG"
            exit 0
        fi
        echo "[supervisor] output suspicious (${sz_mb}MB < 10MB threshold)" | tee -a "$LOG"
    fi

    echo "[supervisor] attempt $attempt FAIL rc=$rc elapsed=${elapsed}s" | tee -a "$LOG"

    # Scrub normalize cache — any partial/corrupt write from this attempt
    # becomes a poison pill for future attempts (L154).
    PYTHONIOENCODING=utf-8 python phase1/scrub_normalize_cache.py >> "$LOG" 2>&1 || true
done

echo "[supervisor] Part $PART FAILED after $MAX_ATTEMPTS attempts" | tee -a "$LOG"
exit 1
