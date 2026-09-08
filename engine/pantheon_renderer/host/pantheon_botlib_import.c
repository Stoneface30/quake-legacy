/*
 * THE PARSER, WITHOUT THE BOTS.
 *
 * cgame reads its .menu and HUD definition files through botlib's
 * PRECOMPILER -- PC_LoadSourceHandle, PC_ReadTokenHandle and three more. Those
 * five functions are the entirety of what cgame wants from botlib, and they
 * are pure text processing: a tokeniser, a #define pass, an include stack.
 *
 * They arrive attached to the bot AI only because id shipped them in the same
 * library. l_precomp.c and l_script.c reach the world through one struct,
 * `botimport`, filled by the engine in be_interface.c -- a file that also
 * drags in area-awareness, navigation meshes, chat and goal selection, none of
 * which draws a single pixel.
 *
 * PANTHEON supplies that struct itself, with the four fields the parser
 * actually touches: print, memory, files. Every navigation and bot-AI entry
 * is NULL, deliberately -- if some path ever reaches one, it crashes here with
 * a name on it rather than working by accident on a library we did not mean to
 * link.
 *
 * This is what owning the tree buys: taking the five functions that are needed
 * instead of the ninety that come in the same box.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/botlib/botlib.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/botlib/be_interface.h"

#include <stdarg.h>

botlib_globals_t botlibglobals;

static void QDECL PANTHEON_BotPrint(int type, char *fmt, ...)
{
    char    text[1024];
    va_list ap;

    va_start(ap, fmt);
    Q_vsnprintf(text, sizeof(text), fmt, ap);
    va_end(ap);

    switch (type) {
    case PRT_MESSAGE: Com_Printf("%s", text); break;
    case PRT_WARNING: Com_Printf("^3%s", text); break;
    case PRT_ERROR:   Com_Printf("^1%s", text); break;
    /* PRT_FATAL and PRT_EXIT are the parser giving up on a file. A HUD that
     * silently failed to parse draws nothing and explains nothing, so this
     * stops loudly. */
    case PRT_FATAL:
    case PRT_EXIT:    Com_Error(ERR_DROP, "botlib parser: %s", text); break;
    default:          Com_Printf("%s", text); break;
    }
}

static void *PANTHEON_BotGetMemory(int size) { return Z_TagMalloc(size, TAG_BOTLIB); }
static void  PANTHEON_BotFreeMemory(void *p) { Z_Free(p); }
static int   PANTHEON_BotAvailableMemory(void) { return Com_TouchMemory(), 0x7fffffff; }
static void *PANTHEON_BotHunkAlloc(int size) { return Hunk_Alloc(size, h_high); }

botlib_import_t botimport = {
    PANTHEON_BotPrint,
    NULL, NULL, NULL, NULL,      /* Trace, EntityTrace, PointContents, inPVS */
    NULL, NULL, NULL,            /* BSPEntityData, BSPModelMinsMaxsOrigin,
                                    BotClientCommand */
    PANTHEON_BotGetMemory,
    PANTHEON_BotFreeMemory,
    PANTHEON_BotAvailableMemory,
    PANTHEON_BotHunkAlloc,
    FS_FOpenFileByMode,
    FS_Read,
    FS_Write,
    FS_FCloseFile,
    FS_Seek,
    NULL, NULL, NULL,            /* DebugLine* */
    NULL, NULL,                  /* DebugPolygon* */
};
