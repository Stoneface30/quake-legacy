#!/bin/sh
# Extract the WolfcamQL 11.3 source the renderer is forked from, verifying the
# archive against SOURCE.sha256 first. The tree itself is NOT committed: it is
# 19 MB of upstream GPL-2.0 source reproducible from an archive whose hash we
# record. What IS committed is everything PANTHEON wrote (host/, oracle/) plus
# this script, so the fork is reproducible without vendoring the upstream tree.
set -e
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
# The archive is not in git (*.tar.gz is ignored repo-wide), so its location
# is explicit: $1, then $WOLFCAM_SRC_TGZ, then this checkout, then the main
# checkout it was downloaded into. A guess is never silently accepted -- the
# sha256 below decides.
tar="${1:-${WOLFCAM_SRC_TGZ:-}}"
for c in "$tar" "$repo/WOLF WHISPERER/WolfcamQL/wolfcamql-src.tar.gz"          "G:/QUAKE_LEGACY/WOLF WHISPERER/WolfcamQL/wolfcamql-src.tar.gz"; do
    [ -n "$c" ] && [ -f "$c" ] && { tar="$c"; break; }
done
[ -n "$tar" ] && [ -f "$tar" ] || { echo "MISSING wolfcamql-src.tar.gz -- pass it as \$1 or set WOLFCAM_SRC_TGZ"; exit 1; }
want=$(awk '{print $1}' "$here/SOURCE.sha256")
have=$(sha256sum "$tar" | awk '{print $1}')
[ "$want" = "$have" ] || { echo "ARCHIVE HASH MISMATCH"; echo " want $want"; echo " have $have"; exit 1; }
mkdir -p "$here/wolfcamql-11.3-src"
tar --force-local -xzf "$tar" -C "$here/wolfcamql-11.3-src"   # a Windows drive letter is not a remote host
test -f "$here/wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_main.c"
echo "source ok: $here/wolfcamql-11.3-src (sha256 verified)"
