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

$CC -m32 -o "$OUT/pantheon_cgame.exe" "$OUT"/*.o "$OBJ"/*.o \
    -lopengl32 -lgdi32 -lwinmm -lws2_32 -lole32 -luser32 -ladvapi32 \
    -lshell32 -lm
echo "built $OUT/pantheon_cgame.exe"
