#!/usr/bin/env bash
# Fetch Part 4's 5 canonical HOOK tracks via SoundCloud and overwrite
# the truncated part04_music_0N.mp3 stems. Runs while the full bulk_sc
# continues downloading the rest of the library in parallel.
#
# Track set (per CURATED_PICKS + RESERVE_PICKS, Part 4 HOOK — rave-pop-techno):
#   01 MAKEBA - TECHNO          BASSTON, STRÖBE           ~3:08 spotify
#   02 BELLAKEO                 Peso Pluma, Anitta        ~3:17
#   03 Calabria (BASSTON remix) BASSTON                   ~3:18
#   04 Nonsense                 Sabrina Carpenter         ~2:45
#   05 Hips Don't Lie - Techno  Shakira/techno remix      ~3:20
set -euo pipefail

cd "$(dirname "$0")/.."
OUT_DIR="$(pwd)/music"
FFMPEG="$(pwd)/../tools/ffmpeg/ffmpeg.exe"
FFPROBE="$(pwd)/../tools/ffmpeg/ffprobe.exe"

download_one() {
    local slot="$1"    # 01..05
    local query="$2"
    local min_dur="${3:-150}"
    local max_dur="${4:-300}"
    local dst="$OUT_DIR/part04_music_${slot}.mp3"
    local tmp_stem="$OUT_DIR/.part04_dl_${slot}"
    echo ""
    echo "[part4-hooks] slot $slot: $query"
    rm -f "${tmp_stem}".* 2>/dev/null || true
    yt-dlp "scsearch5:${query}" \
        --ffmpeg-location "$FFMPEG" \
        -x --audio-format mp3 --audio-quality 0 \
        -o "${tmp_stem}.%(ext)s" \
        --no-playlist \
        --match-filter "duration>=${min_dur} & duration<=${max_dur}" \
        --playlist-items "1-5" --break-on-existing \
        --no-warnings --quiet --no-progress 2>&1 | tail -5
    local got="${tmp_stem}.mp3"
    if [ ! -f "$got" ]; then
        echo "[part4-hooks] slot $slot FAILED — no file"
        return 1
    fi
    local dur=$("$FFPROBE" -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$got" 2>&1)
    echo "[part4-hooks] slot $slot downloaded: ${dur}s"
    mv -f "$got" "$dst"
    # clean any leftovers
    rm -f "${tmp_stem}".* 2>/dev/null || true
}

echo "=== Part 4 HOOK track refresh (5 tracks via SoundCloud) ==="
echo "Target dir: $OUT_DIR"

download_one "01" "MAKEBA TECHNO BASSTON STROBE"          180 260
download_one "02" "BELLAKEO Peso Pluma Anitta"            180 260
download_one "03" "Calabria BASSTON techno remix"         170 260
download_one "04" "Nonsense Sabrina Carpenter"            140 260
download_one "05" "Hips Don't Lie Techno remix Shakira"   180 280

echo ""
echo "=== Final part04_music_*.mp3 state ==="
for i in 01 02 03 04 05; do
    f="$OUT_DIR/part04_music_${i}.mp3"
    if [ -f "$f" ]; then
        dur=$("$FFPROBE" -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f" 2>&1)
        size=$(du -h "$f" | cut -f1)
        printf "  part04_music_%s.mp3  %6.1fs  %s\n" "$i" "$dur" "$size"
    else
        printf "  part04_music_%s.mp3  MISSING\n" "$i"
    fi
done
echo "=== done ==="
