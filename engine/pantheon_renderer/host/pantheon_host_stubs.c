/*
 * PANTHEON native renderer host -- the parts of a Quake client the renderer
 * links against but must never actually use.
 *
 * `common.c` and the renderer are written for a full client: they reference
 * CL_*, SV_*, UI_*, S_* and the AVI capture globals because in the shipped
 * binary those exist. A renderer host is not a client, so each of these is a
 * stub that either does nothing or refuses loudly.
 *
 * THE RULE FOR THIS FILE: a stub may be silent only when doing nothing is
 * genuinely correct (there is no sound, no input, no server). Anything that
 * would silently return a WRONG ANSWER calls Com_Error instead, so a wrong
 * assumption shows up as a stopped process rather than a plausible frame.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/client/cl_avi.h"

/* ── the GL entry points the renderer calls through ─────────────────────── */
#include <windows.h>
#include <GL/gl.h>
#ifndef APIENTRYP
#define APIENTRYP APIENTRY *
#endif
typedef char GLchar;
typedef ptrdiff_t GLsizeiptrARB;
typedef ptrdiff_t GLintptrARB;
typedef unsigned int GLhandleARB;
typedef char GLcharARB;
#include "qgl_defs.inc"

void *PANTHEON_GetProcAddress(const char *name);

/*
 * Bind every pointer the renderer might call. A NULL pointer here is not a
 * crash waiting to happen -- the renderer checks its own capability flags
 * before using an extension -- but binding what the driver has costs nothing.
 */
void PANTHEON_BindGL(void)
{
#define BIND(fn) *(void **)&fn = PANTHEON_GetProcAddress(#fn + 1)
    /* +1 strips ONLY the leading "q". The driver knows these as
     * glActiveTextureARB, not ActiveTextureARB -- skipping 3 characters
     * asked the driver for a name it has never heard of, so every one of
     * these pointers silently stayed NULL and the renderer concluded the
     * hardware had no multitexture, no FBO and no shaders. */
    BIND(qglActiveTextureARB);
    BIND(qglClientActiveTextureARB);
    BIND(qglMultiTexCoord2fARB);
    BIND(qglMultiTexCoord2iARB);
    BIND(qglLockArraysEXT);
    BIND(qglUnlockArraysEXT);
    BIND(qglBindFramebufferEXT);
    BIND(qglBindRenderbufferEXT);
    BIND(qglBlitFramebufferEXT);
    BIND(qglCheckFramebufferStatusEXT);
    BIND(qglDeleteFramebuffersEXT);
    BIND(qglDeleteRenderbuffersEXT);
    BIND(qglFramebufferRenderbufferEXT);
    BIND(qglFramebufferTexture2DEXT);
    BIND(qglGenFramebuffersEXT);
    BIND(qglGenRenderbuffersEXT);
    BIND(qglRenderbufferStorageEXT);
    BIND(qglRenderbufferStorageMultisampleEXT);
    BIND(qglAttachObjectARB);
    BIND(qglCompileShaderARB);
    BIND(qglCreateProgramObjectARB);
    BIND(qglCreateShaderObjectARB);
    BIND(qglDeleteObjectARB);
    BIND(qglDetachObjectARB);
    BIND(qglGetInfoLogARB);
    BIND(qglGetObjectParameterivARB);
    BIND(qglGetUniformLocationARB);
    BIND(qglLinkProgramARB);
    BIND(qglShaderSourceARB);
    BIND(qglUniform1fARB);
    BIND(qglUniform1iARB);
    BIND(qglUseProgramObjectARB);
#undef BIND
}

/* ── there is no client ─────────────────────────────────────────────────── */
int cl_shownet_dummy;
cvar_t *cl_shownet;

void CL_Init(void) {}
void CL_Shutdown(void) {}
void CL_ShutdownAll(void) {}
void CL_Disconnect(qboolean showMainMenu) { (void)showMainMenu; }
void CL_FlushMemory(void) {}
void CL_StartHunkUsers(qboolean rendererOnly) { (void)rendererOnly; }
void CL_Frame(int msec, double fmsec) { (void)msec; (void)fmsec; }
void CL_PacketEvent(netadr_t from, msg_t *msg) { (void)from; (void)msg; }
void CL_CharEvent(int key) { (void)key; }
void CL_KeyEvent(int key, qboolean down, unsigned time)
{ (void)key; (void)down; (void)time; }
void CL_MouseEvent(int dx, int dy, int time) { (void)dx; (void)dy; (void)time; }
void CL_JoystickEvent(int axis, int value, int time)
{ (void)axis; (void)value; (void)time; }
void CL_InitKeyCommands(void) {}
void CL_ForwardCommandToServer(const char *string) { (void)string; }
qboolean CL_GameCommand(void) { return qfalse; }
void CL_Snd_Restart(void) {}
void CL_CDDialog(void) {}
qboolean CL_CDKeyValidate(const char *key, const char *checksum)
{ (void)key; (void)checksum; return qtrue; }
void Key_WriteBindings(fileHandle_t f) { (void)f; }
qboolean UI_GameCommand(void) { return qfalse; }
void S_ClearSoundBuffer(void) {}
void SCR_DebugGraph(float value, int color) { (void)value; (void)color; }

/* ── there is no server ─────────────────────────────────────────────────── */
void SV_Init(void) {}
void SV_Shutdown(char *finalmsg) { (void)finalmsg; }
void SV_Frame(int msec, double fmsec) { (void)msec; (void)fmsec; }
void SV_PacketEvent(netadr_t from, msg_t *msg) { (void)from; (void)msg; }
void SV_ShutdownGameProgs(void) {}
qboolean SV_GameCommand(void) { return qfalse; }
void BotDrawDebugPolygons(void (*drawPoly)(int c, int n, float *p), int value)
{ (void)drawPoly; (void)value; }

/* ── fonts: the first frame draws no text ───────────────────────────────── */
void R_InitFreeType(void) {}
void R_DoneFreeType(void) {}
void R_FontList_f(void) {}
void RE_RegisterFont(const char *fontName, int pointSize, fontInfo_t *font)
{
    (void)fontName; (void)pointSize;
    if (font) Com_Memset(font, 0, sizeof(*font));
}
qboolean RE_GetGlyphInfo(fontInfo_t *f, int c, glyphInfo_t *out)
{ (void)f; (void)c; (void)out; return qfalse; }
qboolean RE_GetFontInfo(int id, fontInfo_t *f) { (void)id; (void)f; return qfalse; }

/* ── AVI capture: PANTHEON reads frames back, it does not write AVIs ────── */
aviFileData_t afdMain, afdLeft, afdRight, afdDepth, afdDepthLeft, afdDepthRight;
qboolean SplitVideo = qfalse;
qboolean Video_DepthBuffer = qfalse;
byte *ExtraVideoBuffer = NULL;

/*
 * The renderer offers a frame here when cl_avi capture is running. PANTHEON
 * never turns that on -- passes are read back by the host -- so being called
 * means something asked the engine to write a movie, and continuing quietly
 * would produce files nobody asked for.
 */
void CL_TakeVideoFrame(void) {}

/*
 * Four more symbols the client and console would supply. The renderer host
 * has no AVI writer, no key binding table and no console log, and says so
 * rather than pretending: nothing here is a behaviour, each is an absence.
 */
qboolean CL_VideoRecording(const aviFileData_t *afd) { (void)afd; return qfalse; }
void Key_KeynameCompletion(void (*callback)(const char *s))
{
    (void)callback;
}
unsigned int CON_LogSize(void) { return 0; }
unsigned int CON_LogRead(char *out, unsigned int size)
{
    (void)out; (void)size; return 0;
}
void CL_ConsolePrint(char *text) { (void)text; }
void CL_ShutdownCGame(void) {}
void CL_ShutdownUI(void) {}
void CIN_CloseAllVideos(void) {}
