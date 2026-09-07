#!/bin/sh
# Rebuild pantheon_frame.exe from the banked host + the bootstrapped upstream
# renderer. RECONSTRUCTED: the original session left no build script, so this
# is derived from the flags recorded in
# docs/reference/2026-09-07-pantheon-native-renderer.md and from which symbols
# host/pantheon_host_stubs.c supplies. It fails loudly; it never reports
# success without a linked binary.
set -e
here=$(cd "$(dirname "$0")" && pwd)
SRC="$here/wolfcamql-11.3-src/wolfcamql-src/code"
OUT="$here/build"; OBJ="$OUT/obj"
[ -d "$SRC/renderer" ] || { echo "run bootstrap_source.sh first"; exit 1; }
mkdir -p "$OBJ"
CC=${CC:-i686-w64-mingw32-gcc}
# -msse2: tr_mme.c includes xmmintrin.h. -w: upstream is not warning-clean and
# its warnings are not ours to fix; the HOST is built without -w on purpose.
CFLAGS="-O2 -msse2 -DUSE_LOCAL_HEADERS=1 -DBOTLIB -I$SRC/qcommon -I$SRC/renderer -I$SRC/jpeg-6b -I$SRC/zlib -I$SRC/SDL12/include -I$SRC/freetype2/include"
n=0
# sys_win32.c supplies the platform services qcommon calls (Sys_ListFiles,
# Sys_Milliseconds, Sys_DefaultHomePath...). sys_main.c is excluded because it
# owns main() -- PANTHEON owns its entry point, and host/pantheon_sys.c
# supplies the eleven services that file would otherwise have provided.
for f in "$SRC"/renderer/*.c "$SRC"/qcommon/*.c "$SRC"/jpeg-6b/*.c "$SRC"/zlib/*.c          "$SRC"/sys/sys_win32.c "$SRC"/sys/con_passive.c          "$SRC"/asm/ftola.c "$SRC"/asm/snapvector.c; do
    case "$f" in
        */tr_font.c) continue ;;          # RE_RegisterFont & co are stubbed
        */vm_x86*.c|*/vm_powerpc*.c|*/vm_sparc*.c) continue ;;
        */example.c|*/minigzip.c|*/gzip*.c) continue ;;   # zlib demos, not the library
        */jload.c|*/jmemansi.c|*/jmemname.c|*/jmemdos.c|*/jmemmac.c|*/rdjpgcom.c|*/wrjpgcom.c|*/djpeg.c|*/cjpeg.c|*/jpegtran.c) continue ;;
    esac
    o="$OBJ/$(echo "$f" | sed "s|$SRC/||; s|/|_|g; s|\.c$|.o|")"
    $CC $CFLAGS -w -c "$f" -o "$o" || { echo "FAILED: $f"; exit 1; }
    n=$((n+1))
done
for f in "$here"/host/*.c; do
    o="$OBJ/host_$(basename "$f" .c).o"
    $CC $CFLAGS -Wall -Wextra -Wno-unused-parameter -c "$f" -o "$o" || { echo "FAILED: $f"; exit 1; }
    n=$((n+1))
done
echo "compiled $n translation units"
$CC -o "$OUT/pantheon_frame.exe" "$OBJ"/*.o -lopengl32 -lgdi32 -luser32 -lws2_32 -lwinmm -lole32
test -s "$OUT/pantheon_frame.exe"
echo "linked: $OUT/pantheon_frame.exe"
