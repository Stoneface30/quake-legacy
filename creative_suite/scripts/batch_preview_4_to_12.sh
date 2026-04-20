#!/usr/bin/env bash
# ============================================================================
#  Batch preview render — Parts 4 → 12 (LOW QUALITY, Rule P1-J v2)
# ----------------------------------------------------------------------------
#  User mandate 2026-04-19:
#    "first pass LOW quality so we also have enough space"
#    "we wasted 24 min again" ← full-quality review renders are banned
#
#  Target: ~2-5 min render wall-clock per Part, ~300 MB each, ~3 GB total
#          vs the prior 20 min / 8 GB per Part.
#
#  Invalidations before firing:
#    * All stale _slow/_fast/_zoom normalized clips (built with old
#      atempo-based audio; the new pipeline uses video-only speed change)
#    * All body chunk caches (they were assembled from stale clips)
#    * Does NOT touch the base _cfr60.mp4 clips (still valid)
#    * Does NOT touch music_plan.json / beats.json (analysis survives)
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
echo "[batch] project root: $PROJECT_ROOT"

# --- Step 1: Invalidate stale effect variants (new audio semantics) ---------
NORM_DIR="$PROJECT_ROOT/output/normalized"
if [ -d "$NORM_DIR" ]; then
    stale_count=$(find "$NORM_DIR" -maxdepth 1 -type f \
                    \( -name "*_cfr60_slow.mp4" \
                    -o -name "*_cfr60_fast.mp4" \
                    -o -name "*_cfr60_zoom.mp4" \) | wc -l)
    echo "[batch] invalidating $stale_count stale effect variants..."
    find "$NORM_DIR" -maxdepth 1 -type f \
        \( -name "*_cfr60_slow.mp4" \
        -o -name "*_cfr60_fast.mp4" \
        -o -name "*_cfr60_zoom.mp4" \) -delete
fi

# --- Step 2: Invalidate stale body chunks for each Part ---------------------
for p in 04 05 06 07 08 09 10 11 12; do
    CHUNK_DIR="$PROJECT_ROOT/output/_part${p}_v6_body_chunks"
    if [ -d "$CHUNK_DIR" ]; then
        echo "[batch] clearing body chunks for Part $p..."
        rm -f "$CHUNK_DIR"/chunk_*.mp4 "$CHUNK_DIR"/_body_xfaded.mp4 || true
    fi
done

# --- Step 3: Render each Part as LOW-QUALITY PREVIEW ------------------------
RESULTS_DIR="/tmp/batch_preview_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"
echo "[batch] logs + output list → $RESULTS_DIR"

SUMMARY="$RESULTS_DIR/summary.txt"
: > "$SUMMARY"

for p_num in 4 5 6 7 8 9 10 11 12; do
    p_zero=$(printf "%02d" "$p_num")
    out_file="$PROJECT_ROOT/output/Part${p_zero}_v13_PREVIEW_$(date +%Y%m%d_%H%M).mp4"
    log_file="$RESULTS_DIR/part${p_zero}.log"
    echo ""
    echo "=================================================================="
    echo "[batch] PART $p_num  →  $(basename "$out_file")"
    echo "=================================================================="
    start=$(date +%s)
    if python -m phase1.render_part_v6 \
            --part "$p_num" \
            --profile preview \
            --output "$out_file" \
            > "$log_file" 2>&1; then
        elapsed=$(( $(date +%s) - start ))
        size_mb=$(du -m "$out_file" 2>/dev/null | cut -f1 || echo "?")
        echo "[batch] Part $p_num PASS — ${elapsed}s, ${size_mb} MB"
        echo "PART $p_num  PASS  ${elapsed}s  ${size_mb}MB  $out_file" >> "$SUMMARY"
    else
        elapsed=$(( $(date +%s) - start ))
        echo "[batch] Part $p_num FAIL — see $log_file  (tail below)"
        tail -20 "$log_file" || true
        echo "PART $p_num  FAIL  ${elapsed}s  -        $log_file" >> "$SUMMARY"
        # Keep going — one Part failing shouldn't block the rest
    fi
done

echo ""
echo "=================================================================="
echo "[batch] DONE — summary:"
cat "$SUMMARY"
echo "=================================================================="
echo "[batch] all logs in: $RESULTS_DIR"
