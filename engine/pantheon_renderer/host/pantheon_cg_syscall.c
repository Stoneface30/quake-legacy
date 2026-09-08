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
 * one function it calls.
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

/* The feed: where cgame's view of the world comes from. A demo is one source
 * of snapshots, not the only one -- see pantheon_cg_feed.c. */
void     PANTHEON_CG_GetGameState(gameState_t *out);
void     PANTHEON_CG_GetCurrentSnapshotNumber(int *num, int *serverTime);
qboolean PANTHEON_CG_GetSnapshot(int number, snapshot_t *out);
qboolean PANTHEON_CG_GetServerCommand(int seq);

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
static int cg_sound_calls;
int PANTHEON_CG_SoundCallCount(void) { return cg_sound_calls; }

intptr_t syscall(intptr_t cmd, ...)
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
    case CG_R_LOADWORLDMAP:     cgre->LoadWorld(VMA(1)); return 0;
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

    default:
        /* Names itself, so the next piece of work is never a guess. */
        Com_Error(ERR_FATAL,
                  "PANTHEON: cgame syscall %d is not implemented yet",
                  (int)cmd);
        return 0;
    }
}
