/*
 * THE SEAM: cgame talks to PANTHEON.
 *
 * WolfcamQL compiles cgame to a DLL and reaches it through a virtual machine.
 * Every trap_ call in cg_syscalls.c marshals its arguments and hands them to
 * syscall(), which the client dispatches in CL_CgameSystemCalls.
 *
 * PANTHEON links cgame STATICALLY. There is no VM, no DLL and no address
 * translation -- a pointer from cgame is already a pointer we can use, so the
 * VMA() macro that existed to translate VM addresses becomes a plain cast.
 * cg_syscalls.c is kept exactly as upstream wrote it; this file supplies the
 * one function it calls -- and, crucially, HANDS IT OVER the way a DLL build
 * does. `syscall` in cg_syscalls.c is not a function it links against: it is a
 * static function POINTER initialised to (void *)-1, set only by dllEntry().
 * Defining a global function called syscall() therefore linked cleanly and was
 * never called -- cgame's first trap_ jumped to 0xffffffff. The pointer must be
 * installed through dllEntry before cgame runs.
 *
 * WHAT IS NOT IMPLEMENTED CALLS Com_Error, DELIBERATELY. Returning 0 from an
 * unknown syscall is how an engine ends up drawing a frame that is quietly
 * missing a third of its content. This project has been bitten by silent
 * no-ops before -- an unregistered cvar accepted and ignored, a capture that
 * exited rc=0 having written nothing. A missing syscall here is a loud stop
 * with its own number, so the next thing to implement names itself.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_public.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/cgame/cg_public.h"

#include <stdarg.h>
#include <string.h>
#include <math.h>

/* cgame parses .menu and .cfg files with botlib's PRECOMPILER -- five
 * functions out of l_precomp.c/l_script.c. Wolfcam reaches them through
 * botlib_export because a VM cannot call across the DLL; statically linked we
 * call them directly, and PANTHEON links the parser without the bot AI it
 * normally arrives attached to. */
/* Reinterpret a float as the int a VM call returns it in. */
static ID_INLINE intptr_t FloatAsInt(float f) { floatint_t fi; fi.f = f; return fi.i; }

int PC_AddGlobalDefine(char *string);
int PC_LoadSourceHandle(const char *filename);
int PC_FreeSourceHandle(int handle);
int PC_ReadTokenHandle(int handle, void *pc_token);
int PC_SourceFileAndLine(int handle, char *filename, int *line);

/* The feed: where cgame's view of the world comes from. A demo is one source
 * of snapshots, not the only one -- see pantheon_cg_feed.c. */
void     PANTHEON_CG_GetGameState(gameState_t *out);
void     PANTHEON_CG_GetCurrentSnapshotNumber(int *num, int *serverTime);
qboolean PANTHEON_CG_GetSnapshot(int number, snapshot_t *out);
qboolean PANTHEON_CG_GetServerCommand(int seq);
int      PANTHEON_CG_ServerCommandSequence(void);
int      PANTHEON_CG_LastExecutedServerCommand(void);

/* What a whole-demo pre-scan would know and a live feed does not. */
typedef struct {
    int  gameStartTime, gameEndTime, firstServerTime, lastServerTime;
    char mapName[MAX_QPATH];
} pantheonDemoInfo_t;
const pantheonDemoInfo_t *PANTHEON_CG_DemoInfo(void);

/* Set once, by the host, before cgame runs. */
static refexport_t *cgre;
static glconfig_t   cg_glconfig;

void PANTHEON_CG_BindRenderer(refexport_t *re, const glconfig_t *cfg)
{
    cgre = re;
    if (cfg) cg_glconfig = *cfg;
}

/* No VM, so a "VM address" is just an address. */
#define VMA(x) ((void *)args[x])
#define VMF(x) (*(float *)&args[x])

/* Sound is not linked into PANTHEON: a still frame has nothing to play, and
 * the mixer would pull in the whole client. Counted rather than ignored, so
 * "cgame asked for sound" is a fact we can report instead of a silence. */
/* Which map is in the renderer. See CG_R_LOADWORLDMAP. */
static char cg_worldLoaded[MAX_QPATH];
const char *PANTHEON_CG_LoadedWorld(void) { return cg_worldLoaded; }

static int cg_sound_calls;
int PANTHEON_CG_SoundCallCount(void) { return cg_sound_calls; }

intptr_t PANTHEON_CG_Syscall(intptr_t cmd, ...)
{
    intptr_t args[16];
    va_list ap;
    int i;

    args[0] = cmd;
    va_start(ap, cmd);
    for (i = 1; i < 16; i++) args[i] = va_arg(ap, intptr_t);
    va_end(ap);

    switch (cmd) {

    /* ---- console, time, cvars ---------------------------------------- */
    case CG_PRINT:              Com_Printf("%s", (const char *)VMA(1)); return 0;
    case CG_ERROR:              Com_Error(ERR_DROP, "%s", (const char *)VMA(1)); return 0;
    case CG_MILLISECONDS:       return Sys_Milliseconds();
    case CG_REAL_TIME:          return Com_RealTime(VMA(1), args[2], args[3]);
    case CG_SNAPVECTOR:         Q_SnapVector(VMA(1)); return 0;
    case CG_MEMORY_REMAINING:   return Hunk_MemoryRemaining();

    case CG_CVAR_REGISTER:      Cvar_Register(VMA(1), VMA(2), VMA(3), args[4]); return 0;
    case CG_CVAR_UPDATE:        Cvar_Update(VMA(1)); return 0;
    case CG_CVAR_SET:           Cvar_SetSafe(VMA(1), VMA(2)); return 0;
    case CG_CVAR_VARIABLESTRINGBUFFER:
        Cvar_VariableStringBuffer(VMA(1), VMA(2), args[3]); return 0;

    case CG_ARGC:               return Cmd_Argc();
    case CG_ARGV:               Cmd_ArgvBuffer(args[1], VMA(2), args[3]); return 0;
    case CG_ARGS:               Cmd_ArgsBuffer(VMA(1), args[2]); return 0;

    /* ---- files -------------------------------------------------------- */
    case CG_FS_FOPENFILE:       return FS_FOpenFileByMode(VMA(1), VMA(2), args[3]);
    case CG_FS_READ:            FS_Read2(VMA(1), args[2], args[3]); return 0;
    case CG_FS_WRITE:           FS_Write(VMA(1), args[2], args[3]); return 0;
    case CG_FS_FCLOSEFILE:      FS_FCloseFile(args[1]); return 0;

    /* ---- commands ----------------------------------------------------- */
    case CG_ADDCOMMAND:         Cmd_AddCommand(VMA(1), NULL); return 0;
    case CG_REMOVECOMMAND:      Cmd_RemoveCommand(VMA(1)); return 0;
    case CG_SENDCONSOLECOMMAND: Cbuf_AddText(VMA(1)); return 0;
    /* PANTHEON has no server connection: a client command has nowhere to go,
     * and pretending otherwise would hide a cgame path we do not support. */
    case CG_SENDCLIENTCOMMAND:  return 0;
    case CG_UPDATESCREEN:       return 0;   /* we render one frame, on demand */

    /* ---- collision model ---------------------------------------------- */
    case CG_CM_LOADMAP:         CM_LoadMap(VMA(1), qtrue, &(int){0}); return 0;
    case CG_CM_NUMINLINEMODELS: return CM_NumInlineModels();
    case CG_CM_INLINEMODEL:     return CM_InlineModel(args[1]);
    case CG_CM_TEMPBOXMODEL:    return CM_TempBoxModel(VMA(1), VMA(2), qfalse);
    case CG_CM_POINTCONTENTS:   return CM_PointContents(VMA(1), args[2]);
    case CG_CM_TRANSFORMEDPOINTCONTENTS:
        return CM_TransformedPointContents(VMA(1), args[2], VMA(3), VMA(4));
    case CG_CM_BOXTRACE:
        CM_BoxTrace(VMA(1), VMA(2), VMA(3), VMA(4), VMA(5), args[6], args[7], qfalse);
        return 0;
    case CG_CM_TRANSFORMEDBOXTRACE:
        CM_TransformedBoxTrace(VMA(1), VMA(2), VMA(3), VMA(4), VMA(5),
                               args[6], args[7], VMA(8), VMA(9), qfalse);
        return 0;
    case CG_CM_MARKFRAGMENTS:
        return cgre->MarkFragments(args[1], VMA(2), VMA(3), args[4],
                                   VMA(5), args[6], VMA(7));

    /* ---- sound: absent, and counted -------------------------------- */
    case CG_S_STARTSOUND: case CG_S_STARTLOCALSOUND:
    case CG_S_CLEARLOOPINGSOUNDS: case CG_S_ADDLOOPINGSOUND:
    case CG_S_UPDATEENTITYPOSITION: case CG_S_RESPATIALIZE:
    case CG_S_STARTBACKGROUNDTRACK: case CG_S_STOPBACKGROUNDTRACK:
        cg_sound_calls++; return 0;
    case CG_S_REGISTERSOUND:
        cg_sound_calls++; return 0;   /* a handle nothing will play */

    /* ---- renderer ----------------------------------------------------- */
    /* THE WORLD IS LOADED ONCE PER PROCESS, NOT ONCE PER TAKE.
     *
     * Loading campgrounds takes seconds; drawing a frame of it takes
     * milliseconds. Extracting a few thousand frags means the same handful of
     * maps over and over, so the only way the cost is bearable is to load a
     * map once and render every moment that happens on it before moving on.
     *
     * cgame calls this from CG_Init, which runs once per take. The renderer
     * refuses a second load outright -- "attempted to redundantly load world
     * map" -- and it is right to: it cannot hold two worlds. So a repeat of
     * the SAME map is answered by doing nothing, which is exactly true, and a
     * request for a DIFFERENT map is a hard stop rather than a frame rendered
     * against the wrong geometry. */
    case CG_R_LOADWORLDMAP:
        if (cg_worldLoaded[0]) {
            if (strcmp(cg_worldLoaded, (const char *)VMA(1)))
                Com_Error(ERR_FATAL,
                          "PANTHEON: '%s' is loaded and cgame asked for '%s'; "
                          "one process renders one map",
                          cg_worldLoaded, (const char *)VMA(1));
            return 0;
        }
        Q_strncpyz(cg_worldLoaded, (const char *)VMA(1), sizeof(cg_worldLoaded));
        cgre->LoadWorld(VMA(1));
        return 0;
    case CG_R_REGISTERMODEL:    return cgre->RegisterModel(VMA(1));
    case CG_R_REGISTERSKIN:     return cgre->RegisterSkin(VMA(1));
    case CG_R_REGISTERSHADER:   return cgre->RegisterShader(VMA(1));
    case CG_R_REGISTERSHADERNOMIP: return cgre->RegisterShaderNoMip(VMA(1));
    case CG_R_REGISTERFONT:     cgre->RegisterFont(VMA(1), args[2], VMA(3)); return 0;
    case CG_R_CLEARSCENE:       cgre->ClearScene(); return 0;
    case CG_R_ADDREFENTITYTOSCENE: cgre->AddRefEntityToScene(VMA(1)); return 0;
    case CG_R_ADDPOLYTOSCENE:
        cgre->AddPolyToScene(args[1], args[2], VMA(3), 1, args[4]); return 0;
    case CG_R_ADDLIGHTTOSCENE:
        cgre->AddLightToScene(VMA(1), VMF(2), VMF(3), VMF(4), VMF(5)); return 0;
    case CG_R_LIGHTFORPOINT:
        return cgre->LightForPoint(VMA(1), VMA(2), VMA(3), VMA(4));
    case CG_R_RENDERSCENE:      cgre->RenderScene(VMA(1)); return 0;
    case CG_R_SETCOLOR:         cgre->SetColor(VMA(1)); return 0;
    case CG_R_DRAWSTRETCHPIC:
        cgre->DrawStretchPic(VMF(1), VMF(2), VMF(3), VMF(4),
                             VMF(5), VMF(6), VMF(7), VMF(8), args[9]);
        return 0;
    case CG_R_MODELBOUNDS:      cgre->ModelBounds(args[1], VMA(2), VMA(3)); return 0;
    case CG_R_LERPTAG:
        return cgre->LerpTag(VMA(1), args[2], args[3], args[4], VMF(5), VMA(6));
    case CG_R_REMAP_SHADER:
        cgre->RemapShader(VMA(1), VMA(2), VMA(3), args[4], args[5]);
        return 0;
    case CG_GETGLCONFIG:        *(glconfig_t *)VMA(1) = cg_glconfig; return 0;

    /* ---- the world cgame draws ---------------------------------------- */
    case CG_GETGAMESTATE:
        PANTHEON_CG_GetGameState(VMA(1)); return 0;
    case CG_GETCURRENTSNAPSHOTNUMBER:
        PANTHEON_CG_GetCurrentSnapshotNumber(VMA(1), VMA(2)); return 0;
    case CG_GETSNAPSHOT:
        return PANTHEON_CG_GetSnapshot(args[1], VMA(2));
    case CG_GETSERVERCOMMAND:
        return PANTHEON_CG_GetServerCommand(args[1]);
    /* PANTHEON renders a WORLD, not a player's input history. cgame uses the
     * command number only for prediction, which a composed shot never does:
     * nobody is pressing keys. Reported as "no commands" rather than faked. */
    case CG_GETCURRENTCMDNUMBER: return 0;
    case CG_GETUSERCMD:          return qfalse;

    /* ---- input: PANTHEON is not played ------------------------------- */
    case CG_KEY_ISDOWN: case CG_KEY_GETCATCHER: case CG_KEY_GETKEY:
        return 0;
    case CG_KEY_SETCATCHER:     return 0;
    case CG_SETUSERCMDVALUE:    return 0;

    /* ---- cinematics: no video playback in a frame renderer ----------- */
    case CG_CIN_PLAYCINEMATIC: case CG_CIN_STOPCINEMATIC:
    case CG_CIN_RUNCINEMATIC:  case CG_CIN_DRAWCINEMATIC:
    case CG_CIN_SETEXTENTS:
        return 0;

    /* ---- botlib text parser: what cgame reads .menu files with -------- */
    case CG_PC_ADD_GLOBAL_DEFINE:  return PC_AddGlobalDefine(VMA(1));
    case CG_PC_LOAD_SOURCE:        return PC_LoadSourceHandle(VMA(1));
    case CG_PC_FREE_SOURCE:        return PC_FreeSourceHandle(args[1]);
    case CG_PC_READ_TOKEN:         return PC_ReadTokenHandle(args[1], VMA(2));
    case CG_PC_SOURCE_FILE_AND_LINE:
        return PC_SourceFileAndLine(args[1], VMA(2), VMA(3));

    /* ---- collision model: the capsule half ---------------------------- */
    case CG_CM_LOADMODEL:        return 0;
    case CG_CM_TEMPCAPSULEMODEL: return CM_TempBoxModel(VMA(1), VMA(2), qtrue);
    case CG_CM_CAPSULETRACE:
        CM_BoxTrace(VMA(1), VMA(2), VMA(3), VMA(4), VMA(5), args[6], args[7], qtrue);
        return 0;
    case CG_CM_TRANSFORMEDCAPSULETRACE:
        CM_TransformedBoxTrace(VMA(1), VMA(2), VMA(3), VMA(4), VMA(5),
                               args[6], args[7], VMA(8), VMA(9), qtrue);
        return 0;

    /* ---- more sound that is not linked -------------------------------- */
    case CG_S_ADDREALLOOPINGSOUND: case CG_S_STOPLOOPINGSOUND:
    case CG_S_PRINTSFXFILENAME:
        cg_sound_calls++; return 0;

    /* ---- files, cvars, commands --------------------------------------- */
    case CG_FS_SEEK:            return FS_Seek(args[1], args[2], args[3]);
    case CG_CVAR_EXISTS:        return Cvar_Exists(VMA(1));
    case CG_AUTOWRITECONFIG:    return 0;   /* never rewrite the user's config */
    case CG_SENDCONSOLECOMMANDNOW: Cbuf_ExecuteText(EXEC_NOW, VMA(1)); return 0;

    /* ---- the rest of the renderer ------------------------------------- */
    case CG_R_ADDADDITIVELIGHTTOSCENE:
        cgre->AddAdditiveLightToScene(VMA(1), VMF(2), VMF(3), VMF(4), VMF(5)); return 0;
    case CG_R_ADDREFENTITYPTRTOSCENE:
        cgre->AddRefEntityPtrToScene(VMA(1)); return 0;
    case CG_R_ADDPOLYSTOSCENE:
        cgre->AddPolyToScene(args[1], args[2], VMA(3), args[4], 0); return 0;
    case CG_R_INPVS:            return cgre->inPVS(VMA(1), VMA(2));
    case CG_GET_ENTITY_TOKEN:   return cgre->GetEntityToken(VMA(1), args[2]);
    case CG_R_REGISTERSHADERLIGHTMAP:
        return cgre->RegisterShaderLightMap(VMA(1), args[2]);
    case CG_R_CLEAR_REMAPPED_SHADER: cgre->ClearRemappedShader(VMA(1)); return 0;
    case CG_R_GETSINGLESHADER:  return cgre->GetSingleShader();
    case CG_R_GETGLYPHINFO:     return cgre->GetGlyphInfo(VMA(1), args[2], VMA(3));
    case CG_R_GETFONTINFO:      return cgre->GetFontInfo(args[1], VMA(2));
    case CG_GET_ADVERTISEMENTS: cgre->Get_Advertisements(VMA(1), VMA(2), VMA(3)); return 0;
    case CG_REPLACESHADERIMAGE:
        cgre->ReplaceShaderImage(args[1], VMA(2), args[3], args[4]); return 0;
    case CG_REGISTERSHADERFROMDATA:
        return cgre->RegisterShaderFromData(VMA(1), VMA(2), args[3], args[4],
                                            args[5], args[6], args[7], args[8]);
    case CG_GETSHADERIMAGEDIMENSIONS:
        cgre->GetShaderImageDimensions(args[1], VMA(2), VMA(3)); return 0;
    case CG_GETSHADERIMAGEDATA: cgre->GetShaderImageData(args[1], VMA(2)); return 0;
    case CG_SETPATHLINES:
        cgre->SetPathLines(VMA(1), VMA(2), VMA(3), VMA(4), VMA(5)); return 0;

    /* ---- math the VM could not do for itself ---------------------------
     * A QVM has no libm, so these were real syscalls. Statically linked cgame
     * could call sin() directly, but cg_syscalls.c is kept verbatim and still
     * routes them here. */
    case CG_MEMSET:  Com_Memset(VMA(1), args[2], args[3]); return 0;
    case CG_MEMCPY:  Com_Memcpy(VMA(1), VMA(2), args[3]);  return 0;
    case CG_STRNCPY: strncpy(VMA(1), VMA(2), args[3]);     return args[1];
    case CG_SIN:     return FloatAsInt(sin(VMF(1)));
    case CG_COS:     return FloatAsInt(cos(VMF(1)));
    case CG_ATAN2:   return FloatAsInt(atan2(VMF(1), VMF(2)));
    case CG_SQRT:    return FloatAsInt(sqrt(VMF(1)));
    case CG_FLOOR:   return FloatAsInt(floor(VMF(1)));
    case CG_CEIL:    return FloatAsInt(ceil(VMF(1)));
    case CG_ACOS:    return FloatAsInt(Q_acos(VMF(1)));
    case CG_POWF:    return FloatAsInt(powf(VMF(1), VMF(2)));
    case CG_TESTPRINTINT:
        Com_Printf("%s%i\n", (const char *)VMA(1), (int)args[2]); return 0;
    case CG_TESTPRINTFLOAT:
        Com_Printf("%s%f\n", (const char *)VMA(1), VMF(2)); return 0;

    /* ---- keyboard and console: PANTHEON has neither ------------------- */
    case CG_KEY_GETBINDING:        *(char *)VMA(2) = 0; return 0;
    case CG_KEY_GETBINDINGBUF:     *(char *)VMA(2) = 0; return 0;
    case CG_KEY_KEYNUMTOSTRINGBUF: *(char *)VMA(2) = 0; return 0;
    case CG_KEY_SETBINDING:        return 0;
    case CG_KEY_GETOVERSTRIKEMODE: return 0;
    case CG_KEY_SETOVERSTRIKEMODE: return 0;
    case CG_DRAW_CONSOLE_LINES:    return 0;

    /* ---- camera splines: PANTHEON owns its own camera ------------------
     * The camera is a ShotSpec decided upstream and handed to the host as an
     * origin and angles. cgame's spline editor is a Wolfcam AUTHORING tool;
     * reading a camera back out of it would put the renderer in charge of a
     * decision that is made above the renderer. */
    case CG_LOADCAMERA:    return qfalse;
    case CG_STARTCAMERA:   return 0;
    case CG_GETCAMERAINFO: return qfalse;
    case CG_CALCSPLINE:    return 0;

    /* ---- DEMO INFO: what a whole-file pre-scan knows -------------------
     * Wolfcam reads a .dm_73 end to end before playing it, so cgame can ask
     * "when did the game start", "who dies next", "what was picked up when".
     * A FEED has no end: snapshots arrive, and the future is not a fact yet.
     *
     * The times come from a struct the host fills when it DOES know them (a
     * parsed demo does; a composed scenario knows its own bounds). Everything
     * that would require seeing the future answers -1, which is exactly what
     * cgame gets from Wolfcam during a LIVE game, and a path it handles.
     * Nothing here is invented: a wrong game-start time silently shifts every
     * clock cgame draws, and would look entirely plausible. */
    case CG_GETGAMESTARTTIME:   return PANTHEON_CG_DemoInfo()->gameStartTime;
    case CG_GETGAMEENDTIME:     return PANTHEON_CG_DemoInfo()->gameEndTime;
    case CG_GETFIRSTSERVERTIME: return PANTHEON_CG_DemoInfo()->firstServerTime;
    case CG_GETLASTSERVERTIME:  return PANTHEON_CG_DemoInfo()->lastServerTime;
    case CG_GETLEGSANIMSTARTTIME: case CG_GETTORSOANIMSTARTTIME:
        return -1;   /* cgame falls back to the entity's own animation clock */
    case CG_GETNEXTKILLER: case CG_GETNEXTVICTIM:
    case CG_GETITEMPICKUPNUMBER: case CG_GETITEMPICKUP:
        return -1;   /* no pre-scan: what comes next is not known yet */
    case CG_GETLASTEXECUTEDSERVERCOMMAND:        /* clc.lastExecutedServerCommand */
        return PANTHEON_CG_LastExecutedServerCommand();
    case CG_GET_DEMO_TIMEOUTS:   *(int *)VMA(2) = 0; return 0;
    case CG_GETROUNDSTARTTIMES:  *(int *)VMA(1) = 0; return 0;
    case CG_GETTEAMSWITCHTIME:   return 0;
    case CG_GET_NUM_PLAYER_INFO: return 0;
    case CG_GET_EXTRA_PLAYER_INFO: return 0;
    case CG_GET_REAL_MAP_NAME:
        Q_strncpyz(VMA(2), PANTHEON_CG_DemoInfo()->mapName, args[3]);
        return 0;
    case CG_PEEKSNAPSHOT:
        /* Looking AHEAD of the latest snapshot fed. Honest answer: not yet. */
        return PANTHEON_CG_GetSnapshot(args[1], VMA(2));

    default:
        /* Names itself, so the next piece of work is never a guess. */
        Com_Error(ERR_FATAL,
                  "PANTHEON: cgame syscall %d is not implemented yet",
                  (int)cmd);
        return 0;
    }
}
