#!/usr/bin/env bash
# Link the CLIENT-GAME layer into the PANTHEON host.
#
# WHAT THIS PROVES. The whole cgame -- effects, HUD, entities, weapons,
# marks, particles, the lot -- compiles and links into our own binary with
# NO missing code. 43 of 44 files build unmodified; the 44th is dead Q3
# legacy that upstream does not build either. The result is 2.2 MB against
# 1.0 MB without it, carrying 658 CG_* symbols.
#
# It is NOT yet wired: nothing calls CG_Init or CG_DrawActiveFrame, and the
# host feeds cgame no snapshots. That is the next piece of work, and it is
# real work. What this script settles is that the work is WIRING, not
# writing -- there is nothing missing to author.
#
#   ./build_cgame.sh   -> build/pantheon_cgame.exe
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The WolfcamQL source is a pinned dependency (third_party/wolfcamql/SOURCE.json).
if [ ! -f "$HERE/wolfcamql-11.3-src/.bootstrap.json" ]; then
    "${PYTHON:-python}" "$HERE/../../scripts/bootstrap_wolfcamql.py" || {
        echo "WolfcamQL source unavailable -- see third_party/wolfcamql/SOURCE.json" >&2; exit 2; }
fi
SRC="$HERE/wolfcamql-11.3-src/wolfcamql-src/code"
OUT="$HERE/build"
OBJ="$OUT/cgame_obj"
CC=${CC:-gcc}
mkdir -p "$OBJ"

INC="-I$SRC/qcommon -I$SRC/renderer -I$SRC/game -I$SRC/client -I$SRC/cgame -I$SRC/ui"

# WOLFCAM_VERSION is normally injected by upstream's Makefile, not a header.
# Com_Printf/Com_Error are renamed because cgame carries its OWN copies -- it
# had to, as a VM with no host to call. Statically linked, the host's win.
CGFLAGS="-m32 -O2 -w -DBOTLIB -DUSE_LOCAL_HEADERS=0 -DWOLFCAM_VERSION=\"11.3\""
# Our own host/ files: a call with no prototype is an error, never a guess --
# the narrow cgame interface (host/pantheon_cgame.h) is only a boundary if
# reaching past it fails to build. The vendored tree would not build with it.
HOSTCG="$CGFLAGS -Werror=implicit-function-declaration"

# cg_particles.c calls trap_R_AddPolyToScene with three arguments where it
# takes four. Upstream does not build it either -- it is Q3 legacy that has
# rotted. Excluded rather than patched, so we stay byte-faithful to a file
# nobody ships.
for f in $(ls "$SRC"/cgame/*.c | grep -v cg_particles); do
    extra=""
    [ "$(basename "$f")" = "cg_main.c" ] && \
        extra="-DCom_Printf=CGVM_Com_Printf -DCom_Error=CGVM_Com_Error"
    # shellcheck disable=SC2086
    $CC $CGFLAGS $extra $INC -c "$f" -o "$OBJ/$(basename "${f%.c}").o"
done
# shellcheck disable=SC2086
$CC $CGFLAGS $INC -c "$SRC"/game/bg_*.c --output-dir "$OBJ" 2>/dev/null || \
    for f in "$SRC"/game/bg_*.c; do $CC $CGFLAGS $INC -c "$f" -o "$OBJ/$(basename "${f%.c}").o"; done
# ui_shared.c supplies Menu_*/Display_*/PC_*_Parse, which cgame's HUD uses.
$CC $CGFLAGS -DCGAME $INC -c "$SRC/ui/ui_shared.c" -o "$OBJ/ui_shared.o"

# cgame parses .menu files with botlib's PRECOMPILER. Only the parser is
# needed -- l_precomp/l_script/l_memory/l_libvar/l_log -- not the bot AI it
# ships attached to.
for f in l_precomp l_script l_memory l_libvar l_log; do
    $CC $CGFLAGS -DBOTLIB $INC -I"$SRC/botlib" -c "$SRC/botlib/$f.c" -o "$OBJ/$f.o"
done
# ...reaching the world through OUR botimport, not be_interface.c and the AI.
$CC $HOSTCG -DBOTLIB $INC -I"$SRC/botlib" -c "$HERE/host/pantheon_botlib_import.c" -o "$OBJ/pantheon_botlib_import.o"

# THE SEAM. cg_syscalls.c is kept verbatim and calls syscall(); this supplies
# it, dispatching straight into the renderer with no VM in between.
$CC $HOSTCG $INC -c "$HERE/host/pantheon_cg_syscall.c" -o "$OBJ/pantheon_cg_syscall.o"
# The feed: cgame's world comes from snapshots WE supply -- a demo is one
# source of them, FrameTruth is another, a composed scenario is a third.
$CC $HOSTCG $INC -c "$HERE/host/pantheon_cg_feed.c" -o "$OBJ/pantheon_cg_feed.o"
# A .dm_73 is one source of that world, decoded with the engine's own msg.c.
$CC $HOSTCG $INC -c "$HERE/host/pantheon_demo_feed.c" -o "$OBJ/pantheon_demo_feed.o"
# Calls cgame: CG_INIT inside the registration window, then
# CG_DRAW_ACTIVE_FRAME per frame.
$CC $HOSTCG $INC -c "$HERE/host/pantheon_cg_run.c" -o "$OBJ/pantheon_cg_run.o"
# A probe compiled against cgame own headers: statically linked, cg and cgs
# are globals we can simply read.
$CC $HOSTCG $INC -c "$HERE/host/pantheon_cg_probe.c" -o "$OBJ/pantheon_cg_probe.o"
# The host gains --cgame, so it is rebuilt here and this object must
# WIN over build/pantheon_frame.o from the non-cgame build.
$CC $HOSTCG $INC -c "$HERE/host/pantheon_frame.c" -o "$OBJ/pantheon_frame.o"
rm -f "$OUT/pantheon_frame.o"

$CC -m32 -o "$OUT/pantheon_cgame.exe" "$OUT"/*.o "$OBJ"/*.o \
    -lopengl32 -lgdi32 -lwinmm -lws2_32 -lole32 -luser32 -ladvapi32 \
    -lshell32 -lm
echo "built $OUT/pantheon_cgame.exe"
