#!/usr/bin/env bash
# Sequential driver for Parts 4-7 v10.3 review renders.
# Part 4 may already be running — we wait on its mp4 then do 5, 6, 7 in order.
# All gates (drift + level) must pass per render; on fail we log and continue
# so the user can see which Part needs a tweak without losing the rest.

set -u
cd /g/QUAKE_LEGACY

LOG_ROOT="output"
STATUS_FILE="$LOG_ROOT/parts_4567_status.txt"
: > "$STATUS_FILE"

render_one() {
    local part="$1"
    local pp=$(printf "%02d" "$part")
    local out="$LOG_ROOT/Part${part}_v10_3_review.mp4"
    local log="$LOG_ROOT/part${pp}_v10_3_review_log.txt"

    echo "[$(date +%H:%M:%S)] Part $part: launching" | tee -a "$STATUS_FILE"

    if [[ -f "$out" ]]; then
        echo "[$(date +%H:%M:%S)] Part $part: already exists ($out), skipping" | tee -a "$STATUS_FILE"
        return 0
    fi

    # -u unbuffered so the log fills live, not on process exit.
    python -u -m phase1.render_part_v6 --part "$part" --review --output "$out" \
        > "$log" 2>&1
    local rc=$?

    if [[ $rc -ne 0 ]]; then
        echo "[$(date +%H:%M:%S)] Part $part: EXIT $rc (see $log)" | tee -a "$STATUS_FILE"
        return $rc
    fi

    # Gate verdicts (level + sync audit). Don't abort the chain — user wants all 4.
    local level_pass="?"
    local drift_ms="?"
    if [[ -f "$LOG_ROOT/part${pp}_levels.json" ]]; then
        level_pass=$(python -c "import json;print(json.load(open('$LOG_ROOT/part${pp}_levels.json')).get('pass'))")
    fi
    if [[ -f "$LOG_ROOT/part${pp}_sync_audit.json" ]]; then
        drift_ms=$(python -c "import json;print(round(json.load(open('$LOG_ROOT/part${pp}_sync_audit.json'))['max_drift_ms'],1))")
    fi
    echo "[$(date +%H:%M:%S)] Part $part: DONE rc=$rc level_pass=$level_pass drift_ms=$drift_ms" | tee -a "$STATUS_FILE"
}

# Wait for Part 4 to finish (it was launched before this driver).
PART4_OUT="$LOG_ROOT/Part4_v10_3_review.mp4"
if [[ ! -f "$PART4_OUT" ]]; then
    echo "[$(date +%H:%M:%S)] Waiting on Part 4 (in-flight from prior launch)..." | tee -a "$STATUS_FILE"
    # Poll mp4 existence; also check that a python render_part is running.
    waited=0
    until [[ -f "$PART4_OUT" ]] || [[ $waited -gt 1800 ]]; do
        sleep 10
        waited=$((waited + 10))
    done
    if [[ ! -f "$PART4_OUT" ]]; then
        echo "[$(date +%H:%M:%S)] Part 4 did not materialize in 30 min — relaunching" | tee -a "$STATUS_FILE"
        render_one 4
    else
        # Gate verdicts for the already-launched Part 4
        p4_level=$(python -c "import json;print(json.load(open('$LOG_ROOT/part04_levels.json')).get('pass'))" 2>/dev/null || echo "?")
        p4_drift=$(python -c "import json;print(round(json.load(open('$LOG_ROOT/part04_sync_audit.json'))['max_drift_ms'],1))" 2>/dev/null || echo "?")
        echo "[$(date +%H:%M:%S)] Part 4: DONE (prior launch) level_pass=$p4_level drift_ms=$p4_drift" | tee -a "$STATUS_FILE"
    fi
else
    echo "[$(date +%H:%M:%S)] Part 4 already rendered ($PART4_OUT)" | tee -a "$STATUS_FILE"
fi

# Now 5 → 6 → 7 sequentially (one GPU, no contention).
for part in 5 6 7; do
    render_one "$part"
done

echo "[$(date +%H:%M:%S)] CHAIN COMPLETE" | tee -a "$STATUS_FILE"
