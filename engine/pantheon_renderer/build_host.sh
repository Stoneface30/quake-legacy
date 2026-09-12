#!/usr/bin/env bash
# Build the PANTHEON native renderer host.
#
# This recipe was missing from the repository -- the executable existed and
# the sources existed, but nothing on disk said how to turn one into the
# other. A renderer nobody else can rebuild is not a deliverable.
#
#   ./build_host.sh                 -> build/pantheon_frame.exe
#   ./build_host.sh oracle          -> oracle/oracle.exe + oracle/oracle_anim.exe
#
# 32-bit mingw, because the Mesa staged in gl_software/bin is i686. The
# NVIDIA ICD crash documented in gl_software/README.md is a driver problem,
# not a bitness one: an x64 MSVC build failed identically.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The WolfcamQL source is a pinned dependency, not a checked-in tree
# (third_party/wolfcamql/SOURCE.json). Absent or unstamped: bootstrap it.
if [ ! -f "$HERE/wolfcamql-11.3-src/.bootstrap.json" ]; then
    "${PYTHON:-python}" "$HERE/../../scripts/bootstrap_wolfcamql.py" || {
        echo "WolfcamQL source unavailable -- see third_party/wolfcamql/SOURCE.json" >&2; exit 2; }
fi
SRC="$HERE/wolfcamql-11.3-src/wolfcamql-src/code"
OUT="$HERE/build"
CC=${CC:-gcc}

# -w is NOT used on our own host code. It was, once, and it hid three real
# porting bugs -- a cast that was not a conversion among them. Warnings on
# the vendored engine tree are noise; warnings on host/ are evidence.
# -mmmx: tr_mme.c builds its blur weights with MMX intrinsics, which gcc
# refuses to inline unless the target allows them.
VENDOR_FLAGS="-m32 -O2 -w -mmmx -DBOTLIB -DUSE_LOCAL_HEADERS=0"
HOST_FLAGS="-m32 -O2 -Wall -Wextra -Wno-unused-parameter -Werror=implicit-function-declaration"
INC="-I$SRC/qcommon -I$SRC/renderer -I$SRC/game -I$SRC/client -I$SRC/jpeg-6b -I$SRC/SDL12/include"

build_oracle() {
    cd "$HERE/oracle"
    for pair in "oracle oracle_main" "oracle_anim oracle_anim_main"; do
        set -- $pair
        $CC -m32 -w -o "$1.exe" "$2.c" oracle_generated.c \
            "$SRC/qcommon/q_math.c" "$SRC/qcommon/q_shared.c" \
            -I. -I"$SRC/qcommon" -I"$SRC/game" -lm
        echo "built oracle/$1.exe"
    done
}

if [ "${1:-host}" = "oracle" ]; then
    build_oracle
    exit 0
fi

mkdir -p "$OUT"
cd "$OUT"

# tr_font.c needs freetype. The host stubs RE_RegisterFont and friends
# instead: a PANTHEON frame has no HUD and draws no text.
RENDERER=$(ls "$SRC"/renderer/*.c | grep -v tr_font)

# jpeg-6b ships alternative memory managers (DOS, Mac, named temp files) and
# standalone tool mains. Exactly ONE memory manager may be linked, and
# jmemnobs is the one Quake uses.
JPEG=$(ls "$SRC"/jpeg-6b/*.c \
       | grep -vE 'jmemdos|jmemmac|jmemansi|jmemname|jload|jpegtran|cjpeg|djpeg|rdjpgcom|wrjpgcom|ckconfig|example')

QCOMMON=$(ls "$SRC"/qcommon/*.c | grep -v -e 'vm_x86' -e 'vm_powerpc' -e 'vm_sparc')

# The platform layer. pantheon_sys.c replaces sys_main.c only; the Win32
# services (timing, random bytes, the console) are the engine's own.
SYSFILES="$SRC/sys/sys_win32.c $SRC/sys/con_win32.c $SRC/sys/con_log.c"
# C fallbacks for the hand-written float->int and snapvector asm.
ASMFILES="$SRC/asm/ftola.c $SRC/asm/snapvector.c"
# zlib, vendored: files.c reads pk3 archives with it.
ZLIB=$(ls "$SRC"/zlib/*.c)

# shellcheck disable=SC2086
$CC $VENDOR_FLAGS $INC -c $RENDERER $JPEG $QCOMMON $SYSFILES $ZLIB
# ftola.c and snapvector.c carry SSE inline asm and will not assemble without
# -msse2. It is applied to THESE TWO FILES ONLY: -mfpmath stays 387 for the
# rest of the tree, because changing how the engine's float arithmetic is
# generated would quietly change what a fidelity claim is a claim about.
# shellcheck disable=SC2086
$CC $VENDOR_FLAGS -msse2 -mfpmath=387 $INC -c $ASMFILES

# shellcheck disable=SC2086
$CC $HOST_FLAGS $INC -c "$HERE"/host/pantheon_frame.c "$HERE"/host/pantheon_actor.c \
    "$HERE"/host/pantheon_sys.c "$HERE"/host/pantheon_glimp_wgl.c \
    "$HERE"/host/pantheon_host_stubs.c
# One binary: build_cgame.sh links these objects into pantheon_cgame.exe.
# The standalone pantheon_frame.exe stopped linking on 2026-09-08.
echo "built objects in $OUT (link with ./build_cgame.sh)"
