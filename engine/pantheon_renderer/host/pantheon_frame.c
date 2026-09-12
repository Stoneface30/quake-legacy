/*
 * PANTHEON native renderer -- the host.
 *
 * An image rasterised by a PANTHEON-owned executable, from PANTHEON state,
 * with no wolfcamql.exe process anywhere.
 *
 * WHAT IT REFUSES TO DO. It does not parse a demo, does not decide where an
 * actor was, does not choose a camera, and does not invent a transform. All of
 * that arrives as a RenderFrame from upstream; if it is absent the frame is
 * not produced. The renderer is downstream of game truth and stays there.
 *
 * Two modes, one code path:
 *
 *   pantheon_frame --basepath <dir> --map <name> --origin x y z --angles p y r
 *                  [--actor-model <md3> --actor-origin x y z ...] --out f.tga
 *
 *   pantheon_frame --basepath <dir> --shot <script>
 *
 * The second is the real one. A shot script is the wire form of the
 * RenderFrame DTO (engine/pantheon/render_frame.py) -- deliberately flat and
 * boring so that parsing it in C cannot become a place where meaning is
 * invented. The map is loaded ONCE and every frame is rendered from it, which
 * is the only way a sequence is affordable.
 */
#include <windows.h>
#include <GL/gl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_public.h"
#include "pantheon_actor.h"

void PANTHEON_SetInstallPath(const char *p);
#include "../wolfcamql-11.3-src/wolfcamql-src/code/game/bg_public.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/cgame/cg_public.h"

refexport_t *GetRefAPI(int apiVersion, refimport_t *rimp);

/* cgame, linked statically. See host/pantheon_cg_syscall.c for the seam and
 * host/pantheon_cg_feed.c for where its view of the world comes from. The host
 * talks to it through ONE narrow interface; the composing helpers are proofs. */
#include "pantheon_cgame.h"
#include "pantheon_cg_compose.h"
#include "pantheon_demo_feed.h"
static int s_cgame;
/* A rocket and an explosion the host can put in the snapshot. Not a feature of
 * the renderer -- a PROOF that a composed snapshot reaches every effect cgame
 * owns, and the shape FrameTruth fills in for real. */
static int    cliRocket, cliBoom;
static vec3_t cliRocketOrg, cliRocketVel, cliBoomOrg;
static vec3_t cliBoomNormal = {0, 0, 1};
/* Motion blur and the depth pass. Both are consequences of owning the frame
 * loop rather than features bolted onto it -- see PANTHEON_BlurFrame and
 * WritePGM16. */
static int   cliBlur;              /* sub-frames per output frame, 0 = off */
static float cliShutter = 0.5f;    /* fraction of the frame interval open */
static int   cliDepth;             /* also write a 16-bit depth map */
static glconfig_t s_glconfig;
void CON_Init(void);
extern CRITICAL_SECTION printCriticalSection;

#define PA_MAX_PLAYERS 8
#define PA_MAX_FRAMES  4096
#define PA_MAX_ACTORS  8

#define PA_MAX_MODELS  16
#define PA_MAX_MISSILES 8
#define PA_MAX_SHOTS   512

typedef struct {
    int      player;                 /* index into the declared players */
    vec3_t   origin;
    vec3_t   angles;
    int      legs, torso;            /* recorded animation numbers */
    /* frame/oldframe/backlerp per part, evaluated by PANTHEON with the
     * engine's own stateful lerp-frame rule. The host does no animation
     * maths: the closed form it used to run was disproved by the oracle. */
    int      legsFrame, legsOldFrame;
    float    legsBacklerp;
    int      torsoFrame, torsoOldFrame;
    float    torsoBacklerp;
    vec3_t   legsAngles, torsoAngles, headAngles;  /* composed upstream */
    int      weaponModel;            /* index into declared models, -1 none */
} shotActor_t;

typedef struct {
    int      model;                  /* index into declared models */
    vec3_t   origin;
    vec3_t   angles;
} shotMissile_t;

typedef struct {
    int         index;
    int         server_time_ms;
    vec3_t      cam_origin;
    vec3_t      cam_angles;
    float       fov;
    char        out[MAX_OSPATH];
    int         numActors;
    shotActor_t actors[PA_MAX_ACTORS];
    int           numMissiles;
    shotMissile_t missiles[PA_MAX_MISSILES];
} shotFrame_t;

typedef struct {
    char        map[MAX_QPATH];
    int         width, height;
    char        provenance[64];
    char        demo[64];
    char        lighting[32];
    int         numPlayers;
    char        playerModel[PA_MAX_PLAYERS][MAX_QPATH];
    char        playerSkin[PA_MAX_PLAYERS][MAX_QPATH];
    int         numModels;
    char        modelPath[PA_MAX_MODELS][MAX_QPATH];
    qhandle_t   modelHandle[PA_MAX_MODELS];
    int         numFrames;
    shotFrame_t *frames;
} shot_t;

static shot_t     s_shot;
static paPlayer_t s_players[PA_MAX_PLAYERS];
static qboolean   s_noWorld;
static const char *s_dumpModel;   /* --dump-model: asset query, no render */
static const char *s_demoScan;    /* --demo-scan: read a .dm_73, no render */
static const char *s_dumpSnapshots; /* --dump-snapshots: gate G1, no render */
static int         s_selfTestRings; /* --self-test-rings: gate G1 4c, no render */

/* ── TGA out ────────────────────────────────────────────────────────────── */
#ifndef GL_FRAMEBUFFER_BINDING_EXT
#define GL_FRAMEBUFFER_BINDING_EXT 0x8CA6
#endif
#ifndef GL_COLOR_ATTACHMENT0_EXT
#define GL_COLOR_ATTACHMENT0_EXT 0x8CE0
#endif

/*
 * EVERY FRAME COMES FROM THE FRAMEBUFFER OBJECT, OR NO FRAME COMES AT ALL.
 *
 * This replaces PANTHEON_MatchClientArea, which grew a hidden window until its
 * client area matched the request. That was a fix for the wrong problem: the
 * picture should never have been in a window. A window's pixels are subject
 * to GL's pixel-ownership rule and are undefined wherever the desktop does
 * not give them to it, so a window-bound renderer is capped by the monitor
 * -- measured: 5120x2880 asked, 3004x1421 delivered.
 *
 * The renderer now draws into its own FBO, sized from glConfig (see
 * pantheon_glimp_wgl.c). This checks that one is actually bound. If it is
 * not, the frame would come from a window again, so the run stops.
 */
static void PANTHEON_RequireOffscreenTarget(void)
{
    GLint fb = 0;
    glGetIntegerv(GL_FRAMEBUFFER_BINDING_EXT, &fb);
    if (!fb)
        Com_Error(ERR_FATAL, "PANTHEON: no framebuffer object is bound; "
                  "refusing to render into a window (r_useFbo off, or the "
                  "FBO failed to complete -- see the log above)");
}

/*
 * THE BRIDGE: a shot frame IS a snapshot.
 *
 * A RenderFrame and a snapshot_t are the same statement in two vocabularies --
 * a time, a camera, and what existed. Composing one from the other is all that
 * stands between "PANTHEON knows what happened" and "cgame draws it".
 *
 * `n` is 1-based so that it matches the snapshot number cgame will ask for.
 */
static void PANTHEON_ShotSnapshot(int n)
{
    shotFrame_t *sf = &s_shot.frames[n - 1];
    snapshot_t   snap;
    int          a;

    PANTHEON_CG_ComposeSnapshot(&snap, sf->server_time_ms, n,
                                sf->cam_origin, sf->cam_angles);

    for (a = 0; a < sf->numActors; a++) {
        vec3_t ang;
        /* cgame turns the body from ONE angle set: it derives the legs and
         * the torso itself, from the movement direction and the aim, with its
         * own swing rules. Handing it three pre-composed sets would be handing
         * it the answer to a question it is about to ask, and would mean
         * maintaining a second animation system whose only job is to agree
         * with the first. The aim is the truth; the rest is cgame's. */
        ang[PITCH] = 0;
        ang[YAW]   = sf->actors[a].torsoAngles[YAW];
        ang[ROLL]  = 0;
        PANTHEON_CG_AddPlayer(&snap, sf->actors[a].player + 1,
                              sf->actors[a].origin, ang,
                              sf->actors[a].legs, sf->actors[a].torso,
                              WP_ROCKET_LAUNCHER);
    }

    for (a = 0; a < sf->numMissiles; a++) {
        vec3_t vel;
        /* A recorded projectile has a position per frame, not a velocity. The
         * direction it FACES is what the trace measured, and 900 u/s is the
         * rocket's own speed -- so the trail is laid along the path the rocket
         * actually flew, rather than differentiated from two samples that were
         * never meant to be differentiated. */
        AngleVectors(sf->missiles[a].angles, vel, NULL, NULL);
        VectorScale(vel, 900.0f, vel);
        PANTHEON_CG_AddRocket(&snap, 32 + a, sf->missiles[a].origin, vel,
                              sf->server_time_ms);
    }

    PANTHEON_CG_SetSnapshot(n, &snap);
}

/*
 * THE DEPTH PASS.
 *
 * A colour frame says what the shot looks like. A depth frame says how far
 * away each pixel is, which is what lets depth of field, fog, atmospheric
 * haze and compositing be decided in the edit rather than baked into the
 * render -- and re-decided later without re-rendering.
 *
 * Written as 16-bit binary PGM: one channel, big-endian, no compression, and
 * read by ffmpeg, ImageMagick, Nuke and Resolve without a plugin. The values
 * are the raw depth buffer, which is NOT linear -- precision is crowded near
 * the camera by the projection. The near and far planes are written into the
 * PGM comment so the reader can linearise as
 *
 *     z = 2*n*f / (f + n - (2*d - 1)*(f - n))
 *
 * rather than guess. A depth map with no planes recorded is a picture of a
 * gradient, not a measurement.
 */
/*
 * MOTION BLUR THAT IS NOT A CHEAT.
 *
 * A real camera's shutter is open for a slice of each frame, and everything
 * that moves during that slice smears. Every offline approximation of this
 * either blends the neighbouring OUTPUT frames -- which smears the wrong
 * distance and ghosts, because the frames are too far apart -- or warps pixels
 * along a guessed velocity field, which invents geometry at silhouettes.
 *
 * PANTHEON does not have to approximate. The renderer is fed a snapshot and
 * asked for the world at an INSTANT, so a frame at t can be built from N real
 * renders spread across the shutter interval and averaged. Each sub-frame is
 * an actual world state: the rocket really was there, the torso really had
 * turned that far, the explosion really was that many milliseconds old. The
 * average of real samples is what a shutter does.
 *
 * This is the thing an engine that PLAYS a demo cannot do -- it can only show
 * you the frames the playback clock lands on. It falls out of the snapshot
 * feed for free.
 *
 * Accumulated in 32-bit so that 64 sub-frames cannot overflow, and averaged
 * only at the end: averaging as you go loses the low bits N times over.
 */
static void PANTHEON_BlurAccumulate(unsigned *acc, const byte *rgb, int n)
{
    int i;
    for (i = 0; i < n; i++) acc[i] += rgb[i];
}

static void PANTHEON_BlurResolve(byte *rgb, const unsigned *acc, int n,
                                 int samples)
{
    int i;
    for (i = 0; i < n; i++)
        rgb[i] = (byte)((acc[i] + samples / 2) / samples);
}

static void WritePGM16(const char *path, const float *depth, int w, int h,
                       float zNear, float zFar)
{
    FILE  *f = fopen(path, "wb");
    byte  *row;
    int    x, y;

    if (!f) Com_Error(ERR_FATAL, "cannot write %s", path);
    fprintf(f, "P5\n# PANTHEON depth znear=%.6f zfar=%.6f nonlinear=1\n"
               "%d %d\n65535\n", zNear, zFar, w, h);
    row = malloc((size_t)w * 2);
    /* GL hands back bottom-up; PGM is top-down. */
    for (y = h - 1; y >= 0; y--) {
        for (x = 0; x < w; x++) {
            float    d = depth[y * w + x];
            unsigned v;
            if (d < 0.0f) d = 0.0f;
            if (d > 1.0f) d = 1.0f;
            v = (unsigned)(d * 65535.0f + 0.5f);
            row[x * 2 + 0] = (byte)(v >> 8);
            row[x * 2 + 1] = (byte)(v & 255);
        }
        fwrite(row, 1, (size_t)w * 2, f);
    }
    free(row);
    fclose(f);
}

static void WriteTGA(const char *path, const byte *rgb, int w, int h)
{
    FILE *f = fopen(path, "wb");
    byte hdr[18];
    int i, n = w * h;
    byte *bgr;

    if (!f) Com_Error(ERR_FATAL, "cannot write %s", path);
    memset(hdr, 0, sizeof(hdr));
    hdr[2] = 2;                       /* uncompressed true-colour */
    hdr[12] = w & 255;  hdr[13] = (w >> 8) & 255;
    hdr[14] = h & 255;  hdr[15] = (h >> 8) & 255;
    hdr[16] = 24;
    fwrite(hdr, 1, sizeof(hdr), f);
    /* GL gives bottom-up RGB; TGA wants bottom-up BGR. */
    bgr = malloc((size_t)n * 3);
    for (i = 0; i < n; i++) {
        bgr[i * 3 + 0] = rgb[i * 3 + 2];
        bgr[i * 3 + 1] = rgb[i * 3 + 1];
        bgr[i * 3 + 2] = rgb[i * 3 + 0];
    }
    fwrite(bgr, 1, (size_t)n * 3, f);
    free(bgr);
    fclose(f);
}

/* ── shot script ────────────────────────────────────────────────────────── */
/*
 * Parsed with sscanf against a fixed grammar. Anything unrecognised is a hard
 * error rather than a skipped line: a silently ignored actor is a frame that
 * renders happily while being wrong about history.
 */
/*
 * ParseShot runs BEFORE Com_Init, because the shot declares the resolution the
 * window has to be created at. Com_Error at that point walks into Cvar_Set,
 * CopyString and Z_TagMalloc with no zone allocator behind them and takes the
 * process down with a segfault -- so a shot script one column out of date is
 * indistinguishable from a crash in the renderer, which is exactly how an
 * afternoon gets spent. Parse failures report themselves and exit instead.
 */
static void ShotError(const char *fmt, ...)
{
    char    msg[1024];
    va_list ap;

    va_start(ap, fmt);
    vsnprintf(msg, sizeof(msg), fmt, ap);
    va_end(ap);
    fprintf(stderr, "PANTHEON shot script: %s\n", msg);
    exit(2);
}

static void ParseShot(const char *path)
{
    FILE *f = fopen(path, "r");
    char line[1024];
    shotFrame_t *cur = NULL;
    int lineno = 0;

    if (!f) ShotError("cannot open shot script %s", path);

    s_shot.width = 1280;
    s_shot.height = 720;
    s_shot.frames = calloc(PA_MAX_FRAMES, sizeof(shotFrame_t));

    while (fgets(line, sizeof(line), f)) {
        char kw[64];
        lineno++;
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        if (sscanf(line, "%63s", kw) != 1) continue;

        if (!strcmp(kw, "map")) {
            sscanf(line, "%*s %63s", s_shot.map);
        } else if (!strcmp(kw, "size")) {
            sscanf(line, "%*s %d %d", &s_shot.width, &s_shot.height);
        } else if (!strcmp(kw, "provenance")) {
            sscanf(line, "%*s %63s", s_shot.provenance);
        } else if (!strcmp(kw, "demo")) {
            sscanf(line, "%*s %63s", s_shot.demo);
        } else if (!strcmp(kw, "lighting")) {
            sscanf(line, "%*s %31s", s_shot.lighting);
        } else if (!strcmp(kw, "player")) {
            int i = s_shot.numPlayers;
            if (i >= PA_MAX_PLAYERS)
                ShotError("too many players in shot");
            if (sscanf(line, "%*s %63s %63s",
                       s_shot.playerModel[i], s_shot.playerSkin[i]) != 2)
                ShotError("bad player line %d", lineno);
            s_shot.numPlayers++;
        } else if (!strcmp(kw, "model")) {
            int i = s_shot.numModels;
            if (i >= PA_MAX_MODELS)
                ShotError("too many models in shot");
            if (sscanf(line, "%*s %63s", s_shot.modelPath[i]) != 1)
                ShotError("bad model line %d", lineno);
            s_shot.numModels++;
        } else if (!strcmp(kw, "frame")) {
            if (s_shot.numFrames >= PA_MAX_FRAMES)
                ShotError("too many frames in shot");
            cur = &s_shot.frames[s_shot.numFrames++];
            memset(cur, 0, sizeof(*cur));
            if (sscanf(line, "%*s %d %d %f %f %f %f %f %f %f %255s",
                       &cur->index, &cur->server_time_ms,
                       &cur->cam_origin[0], &cur->cam_origin[1],
                       &cur->cam_origin[2],
                       &cur->cam_angles[0], &cur->cam_angles[1],
                       &cur->cam_angles[2], &cur->fov, cur->out) != 10)
                ShotError("bad frame line %d", lineno);
        } else if (!strcmp(kw, "actor")) {
            shotActor_t *a;
            if (!cur) Com_Error(ERR_FATAL,
                                "PANTHEON: actor before frame, line %d", lineno);
            if (cur->numActors >= PA_MAX_ACTORS)
                ShotError("too many actors, line %d", lineno);
            a = &cur->actors[cur->numActors];
            if (sscanf(line,
                       "%*s %d %f %f %f %d %d "
                       "%d %d %f %d %d %f "
                       "%f %f %f %f %f %f %f %f %f %d",
                       &a->player, &a->origin[0], &a->origin[1], &a->origin[2],
                       &a->legs, &a->torso,
                       &a->legsFrame, &a->legsOldFrame, &a->legsBacklerp,
                       &a->torsoFrame, &a->torsoOldFrame, &a->torsoBacklerp,
                       &a->legsAngles[0], &a->legsAngles[1], &a->legsAngles[2],
                       &a->torsoAngles[0], &a->torsoAngles[1], &a->torsoAngles[2],
                       &a->headAngles[0], &a->headAngles[1], &a->headAngles[2],
                       &a->weaponModel) != 22)
                ShotError("bad actor line %d", lineno);
            if (a->weaponModel >= s_shot.numModels)
                Com_Error(ERR_FATAL,
                          "PANTHEON: actor names undeclared model %d, line %d",
                          a->weaponModel, lineno);
            if (a->player < 0 || a->player >= s_shot.numPlayers)
                Com_Error(ERR_FATAL,
                          "PANTHEON: actor names undeclared player %d, line %d",
                          a->player, lineno);
            cur->numActors++;
        } else if (!strcmp(kw, "projectile")) {
            shotMissile_t *m;
            if (!cur) Com_Error(ERR_FATAL,
                                "PANTHEON: projectile before frame, line %d",
                                lineno);
            if (cur->numMissiles >= PA_MAX_MISSILES)
                ShotError("too many missiles, line %d",
                          lineno);
            m = &cur->missiles[cur->numMissiles];
            if (sscanf(line, "%*s %d %f %f %f %f %f %f",
                       &m->model, &m->origin[0], &m->origin[1], &m->origin[2],
                       &m->angles[0], &m->angles[1], &m->angles[2]) != 7)
                ShotError("bad projectile line %d", lineno);
            if (m->model < 0 || m->model >= s_shot.numModels)
                Com_Error(ERR_FATAL,
                          "PANTHEON: projectile names undeclared model %d, "
                          "line %d", m->model, lineno);
            cur->numMissiles++;
        } else {
            ShotError("unknown shot keyword '%s' line %d",
                      kw, lineno);
        }
    }
    fclose(f);

    if (!s_shot.map[0])   ShotError("shot has no map");
    if (!s_shot.numFrames) ShotError("shot has no frames");
}

/*
 * The renderer's Printf takes a print LEVEL; Com_Printf does not. Casting one
 * to the other compiles silently and then passes PRINT_ALL -- which is 0 -- as
 * the format string. A cast is not a conversion.
 */
static void QDECL PANTHEON_RefPrintf(int level, const char *fmt, ...)
{
    va_list argptr;
    char text[MAX_PRINT_MSG];

    va_start(argptr, fmt);
    Q_vsnprintf(text, sizeof(text), fmt, argptr);
    va_end(argptr);

    if (level == PRINT_DEVELOPER)
        Com_DPrintf("%s", text);
    else
        Com_Printf("%s", text);
}

/* ── gate G1: every field by name, and the rings ───────────────────────────
 *
 * The field tables are generated from msg.c (engine/parser/gen_netfields.py),
 * the same source DM73Parser's tables come from, so the two sides compare the
 * same fields in the same order. Configstrings are compared by an FNV-1a 64
 * hash over "<index>\0<value>\0" for every non-empty index, ascending. */
#include <stddef.h>
typedef struct { const char *name; int offset; int isFloat; } pantheonNetField_t;
#include "pantheon_netfields.inc"
#define G1_COUNT(a) ((int)(sizeof(a) / sizeof((a)[0])))
#define G1_FNV_BASIS 1469598103934665603ULL

static unsigned long long G1_Fnv(unsigned long long h, const char *p, int n)
{
    while (n-- > 0) { h ^= (unsigned char)*p++; h *= 1099511628211ULL; }
    return h;
}

static unsigned long long G1_CsRecord(unsigned long long h, const gameState_t *gs, int i)
{
    const char *s = gs->stringData + gs->stringOffsets[i];
    char num[16];
    int  n = Com_sprintf(num, sizeof(num), "%d", i);
    h = G1_Fnv(h, num, n + 1);                 /* includes the \0 */
    return G1_Fnv(h, s, (int)strlen(s) + 1);
}

static unsigned long long G1_CsHash(const gameState_t *gs, int i)
{
    const char *s = gs->stringData + gs->stringOffsets[i];
    return s[0] ? G1_CsRecord(G1_FNV_BASIS, gs, i) : 0;
}

static unsigned long long G1_CsSetHash(const gameState_t *gs)
{
    unsigned long long h = G1_FNV_BASIS;
    int i;
    for (i = 0; i < MAX_CONFIGSTRINGS; i++)
        if ((gs->stringData + gs->stringOffsets[i])[0]) h = G1_CsRecord(h, gs, i);
    return h;
}

static void G1_Values(const void *base, const pantheonNetField_t *f, int n)
{
    int i;
    for (i = 0; i < n; i++) {
        const byte *p = (const byte *)base + f[i].offset;
        if (f[i].isFloat) printf("\t%.9g", *(const float *)p);
        else              printf("\t%d", *(const int *)p);
    }
}

static void G1_PrintFieldNames(void)
{
    int i;
    printf("F\tP");
    for (i = 0; i < G1_COUNT(pantheon_psQ3); i++) printf("\t%s", pantheon_psQ3[i].name);
    for (i = 0; i < MAX_STATS; i++)      printf("\tstats[%d]", i);
    for (i = 0; i < MAX_PERSISTANT; i++) printf("\tpersistant[%d]", i);
    for (i = 0; i < MAX_WEAPONS; i++)    printf("\tammo[%d]", i);
    for (i = 0; i < MAX_POWERUPS; i++)   printf("\tpowerups[%d]", i);
    printf("\nF\tE");
    for (i = 0; i < G1_COUNT(pantheon_es73); i++) printf("\t%s", pantheon_es73[i].name);
    printf("\n");
}

static void G1_PrintPlayerState(const playerState_t *ps, int serverTime)
{
    int i;
    printf("P\t%d", serverTime);
    G1_Values(ps, pantheon_psQ3, G1_COUNT(pantheon_psQ3));
    for (i = 0; i < MAX_STATS; i++)      printf("\t%d", ps->stats[i]);
    for (i = 0; i < MAX_PERSISTANT; i++) printf("\t%d", ps->persistant[i]);
    for (i = 0; i < MAX_WEAPONS; i++)    printf("\t%d", ps->ammo[i]);
    for (i = 0; i < MAX_POWERUPS; i++)   printf("\t%d", ps->powerups[i]);
    printf("\n");
}

static void G1_PrintEntity(const entityState_t *e, int serverTime)
{
    printf("E\t%d\t%d", serverTime, e->number);
    G1_Values(e, pantheon_es73, G1_COUNT(pantheon_es73));
    printf("\n");
}

/* The configstring set, and which indices changed since the last snapshot. */
static void G1_PrintConfigstrings(const gameState_t *gs, int serverTime,
                                  unsigned long long *prev)
{
    int i, any = 0;
    printf("C\t%d\t%016llx\t", serverTime, G1_CsSetHash(gs));
    for (i = 0; i < MAX_CONFIGSTRINGS; i++) {
        unsigned long long h = G1_CsHash(gs, i);
        if (h != prev[i]) { printf(any ? ",%d" : "%d", i); any = 1; prev[i] = h; }
    }
    printf(any ? "\n" : "-\n");
}

/* Test hooks into the feed -- NOT the host interface (pantheon_cgame.h). */
qboolean    PANTHEON_CG_GetServerCommand(int seq);
int         PANTHEON_CG_CommandSlotOwner(int seq);
const char *PANTHEON_CG_ConfigString(int index);

/*
 * The rings, wrapped on purpose (plan Task 3, step 4c). Run inside the real
 * linked binary, against the production objects, rather than in a separate
 * program that would have to re-link half the engine.
 */
static int G1_SelfTestRings(void)
{
    static gameState_t gs;
    static const int owner[][2] = { {63, 127}, {64, 128}, {65, 129},
                                    {127, 127}, {128, 128}, {129, 129} };
    static const int slot[][3] = { {8191, 0, 8191}, {8191, 1, 0},
                                   {8192, 0, 0}, {8193, 0, 1} };
    char text[64];
    int  seq, i, bad = 0;

    memset(&gs, 0, sizeof(gs));
    gs.dataCount = 1;

    /* Reliable commands: 130 queued, only the last 64 retrievable. */
    PANTHEON_CG_LoadGameState(&gs, 0);
    for (seq = 1; seq <= 130; seq++) {
        Com_sprintf(text, sizeof(text), "print \"%d\"", seq);
        PANTHEON_CG_ApplyServerCommand(seq, text);
    }
    for (seq = 1; seq <= 130; seq++) {
        qboolean want = seq > 130 - MAX_RELIABLE_COMMANDS;
        if (PANTHEON_CG_GetServerCommand(seq) != want) {
            printf("RING FAIL: command %d retrievable=%d, want %d\n", seq, !want, want);
            bad++;
        } else if (want && atoi(Cmd_Argv(1)) != seq) {
            printf("RING FAIL: command %d returned \"%s\"\n", seq, Cmd_Argv(1));
            bad++;
        }
    }
    for (i = 0; i < G1_COUNT(owner); i++)
        if (PANTHEON_CG_CommandSlotOwner(owner[i][0]) != owner[i][1]) {
            printf("RING FAIL: slot of %d owned by %d, want %d\n", owner[i][0],
                   PANTHEON_CG_CommandSlotOwner(owner[i][0]), owner[i][1]);
            bad++;
        }

    /* A big configstring in three pieces reaches cgame as ONE cs. */
    PANTHEON_CG_LoadGameState(&gs, 0);
    PANTHEON_CG_ApplyServerCommand(1, "bcs0 5 abc");
    PANTHEON_CG_ApplyServerCommand(2, "bcs1 5 def");
    PANTHEON_CG_ApplyServerCommand(3, "bcs2 5 ghi");
    if (PANTHEON_CG_GetServerCommand(1) || PANTHEON_CG_GetServerCommand(2)) {
        printf("RING FAIL: a bcs0/bcs1 piece reached cgame\n");
        bad++;
    }
    if (!PANTHEON_CG_GetServerCommand(3) || strcmp(Cmd_Argv(0), "cs") ||
        strcmp(PANTHEON_CG_ConfigString(5), "abcdefghi")) {
        printf("RING FAIL: bcs2 gave argv0=\"%s\", cs5=\"%s\"\n", Cmd_Argv(0),
               PANTHEON_CG_ConfigString(5));
        bad++;
    }

    /* The parse-entity ring: 8192 slots, wrapping at the mask. */
    for (i = 0; i < G1_COUNT(slot); i++)
        if (PANTHEON_Demo_EntSlot(slot[i][0], slot[i][1]) != slot[i][2]) {
            printf("RING FAIL: parse slot (%d,%d)=%d, want %d\n", slot[i][0],
                   slot[i][1], PANTHEON_Demo_EntSlot(slot[i][0], slot[i][1]), slot[i][2]);
            bad++;
        }

    printf(bad ? "RINGS FAIL %d\n" : "RINGS OK\n", bad);
    fflush(stdout);
    return bad ? 1 : 0;
}

int main(int argc, char **argv)
{
    refimport_t ri;
    refexport_t *re;
    refdef_t rd;
    byte *pixels;
    int i, fi;
    char cmdline[1024];
    /* A RUN IS A MAP, NOT A FRAG.
     *
     * Loading campgrounds costs seconds; drawing a frame of it costs
     * milliseconds. Extracting a corpus means the same handful of maps over
     * and over, so --shot is repeatable: one process loads the world once and
     * renders every take recorded on it. */
    const char *shotPath = NULL;
    const char *shotPaths[PA_MAX_SHOTS];
    int         numShots = 0, take, totalFrames = 0;
    unsigned   *blurAccum = NULL;
    float      *depthPix = NULL;
    int         blurSub, blurSamples;

    /* single-frame mode inputs */
    char  cliMap[MAX_QPATH] = {0};
    char  cliOut[MAX_OSPATH] = "pantheon_frame.tga";
    char  cliModel[MAX_QPATH] = {0}, cliSkin[MAX_QPATH] = "default";
    vec3_t cliOrigin = {0, 0, 0}, cliAngles = {0, 0, 0};
    vec3_t cliActorOrigin = {0, 0, 0}, cliActorAngles = {0, 0, 0};
    /* The one-actor CLI path is a smoke test. It names MD3 frames directly,
     * because the host no longer owns any animation maths: which frames an
     * animation number resolves to is PANTHEON's answer, evaluated with the
     * engine's stateful lerp-frame rule. --actor-anim survives only to label
     * what is being posed. */
    int   cliLegs = 0, cliTorso = 0, cliW = 1280, cliH = 720;
    int   cliLegsFrame = 0, cliLegsOldFrame = 0;
    int   cliTorsoFrame = 0, cliTorsoOldFrame = 0;
    float cliLegsBacklerp = 0.0f, cliTorsoBacklerp = 0.0f;
    float cliFov = 90.0f;
    qboolean cliActor = qfalse;

    cmdline[0] = '\0';
    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--shot") && i + 1 < argc) {
            if (numShots >= PA_MAX_SHOTS)
                ShotError("more than %d --shot scripts in one run",
                          PA_MAX_SHOTS);
            shotPaths[numShots++] = argv[++i];
            shotPath = shotPaths[0];
        } else if (!strcmp(argv[i], "--map") && i + 1 < argc)
            Q_strncpyz(cliMap, argv[++i], sizeof(cliMap));
        else if (!strcmp(argv[i], "--origin") && i + 3 < argc) {
            cliOrigin[0] = (float)atof(argv[++i]);
            cliOrigin[1] = (float)atof(argv[++i]);
            cliOrigin[2] = (float)atof(argv[++i]);
        } else if (!strcmp(argv[i], "--angles") && i + 3 < argc) {
            cliAngles[0] = (float)atof(argv[++i]);
            cliAngles[1] = (float)atof(argv[++i]);
            cliAngles[2] = (float)atof(argv[++i]);
        } else if (!strcmp(argv[i], "--dump-model") && i + 1 < argc) {
            /* Asset interrogation, not rendering. PANTHEON asks the host what
             * a model declares because the host is the only thing that can
             * open the pak; it still decides nothing about the answer. */
            s_dumpModel = argv[++i];
        } else if (!strcmp(argv[i], "--demo-scan") && i + 1 < argc) {
            /* The demo reader alone: no GL, no cgame. Its counts are what
             * gate G1 compares against DM73Parser. */
            s_demoScan = argv[++i];
        } else if (!strcmp(argv[i], "--dump-snapshots") && i + 1 < argc) {
            s_dumpSnapshots = argv[++i];
        } else if (!strcmp(argv[i], "--self-test-rings")) {
            s_selfTestRings = 1;
        } else if (!strcmp(argv[i], "--actor-model") && i + 1 < argc) {
            Q_strncpyz(cliModel, argv[++i], sizeof(cliModel));
            cliActor = qtrue;
        } else if (!strcmp(argv[i], "--actor-skin") && i + 1 < argc)
            Q_strncpyz(cliSkin, argv[++i], sizeof(cliSkin));
        else if (!strcmp(argv[i], "--actor-origin") && i + 3 < argc) {
            cliActorOrigin[0] = (float)atof(argv[++i]);
            cliActorOrigin[1] = (float)atof(argv[++i]);
            cliActorOrigin[2] = (float)atof(argv[++i]);
        } else if (!strcmp(argv[i], "--actor-angles") && i + 3 < argc) {
            cliActorAngles[0] = (float)atof(argv[++i]);
            cliActorAngles[1] = (float)atof(argv[++i]);
            cliActorAngles[2] = (float)atof(argv[++i]);
        } else if (!strcmp(argv[i], "--actor-anim") && i + 2 < argc) {
            cliLegs = atoi(argv[++i]);
            cliTorso = atoi(argv[++i]);
        } else if (!strcmp(argv[i], "--actor-frames") && i + 6 < argc) {
            cliLegsFrame     = atoi(argv[++i]);
            cliLegsOldFrame  = atoi(argv[++i]);
            cliLegsBacklerp  = (float)atof(argv[++i]);
            cliTorsoFrame    = atoi(argv[++i]);
            cliTorsoOldFrame = atoi(argv[++i]);
            cliTorsoBacklerp = (float)atof(argv[++i]);
        } else if (!strcmp(argv[i], "--fov") && i + 1 < argc)
            cliFov = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--width") && i + 1 < argc)
            cliW = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--height") && i + 1 < argc)
            cliH = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--cgame"))
            s_cgame = 1;
        else if (!strcmp(argv[i], "--blur") && i + 1 < argc)
            cliBlur = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--shutter") && i + 1 < argc)
            cliShutter = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--depth"))
            cliDepth = 1;
        else if (!strcmp(argv[i], "--rocket") && i + 6 < argc) {
            cliRocket = 1;
            cliRocketOrg[0] = (float)atof(argv[++i]);
            cliRocketOrg[1] = (float)atof(argv[++i]);
            cliRocketOrg[2] = (float)atof(argv[++i]);
            cliRocketVel[0] = (float)atof(argv[++i]);
            cliRocketVel[1] = (float)atof(argv[++i]);
            cliRocketVel[2] = (float)atof(argv[++i]);
        } else if (!strcmp(argv[i], "--explosion") && i + 3 < argc) {
            cliBoom = 1;
            cliBoomOrg[0] = (float)atof(argv[++i]);
            cliBoomOrg[1] = (float)atof(argv[++i]);
            cliBoomOrg[2] = (float)atof(argv[++i]);
        }
        else if (!strcmp(argv[i], "--no-world"))
            s_noWorld = qtrue;
        /* A cvar set BEFORE Com_Init, which is the only time some of them
         * matter. r_gamma in particular is baked into every texture at upload
         * (R_LightScaleTexture), so setting it later changes nothing. */
        else if (!strcmp(argv[i], "--set") && i + 2 < argc) {
            Q_strcat(cmdline, sizeof(cmdline),
                     va("+set %s \"%s\" ", argv[i + 1], argv[i + 2]));
            i += 2;
        }
        else if (!strcmp(argv[i], "--out") && i + 1 < argc)
            Q_strncpyz(cliOut, argv[++i], sizeof(cliOut));
        else if (!strcmp(argv[i], "--basepath") && i + 1 < argc) {
            PANTHEON_SetInstallPath(argv[i + 1]);
            Q_strcat(cmdline, sizeof(cmdline),
                     va("+set fs_basepath \"%s\" ", argv[i + 1]));
            i++;
        } else if (!strcmp(argv[i], "--home") && i + 1 < argc)
            Q_strcat(cmdline, sizeof(cmdline),
                     va("+set fs_homepath \"%s\" ", argv[++i]));
        else if (!strcmp(argv[i], "--game") && i + 1 < argc)
            Q_strcat(cmdline, sizeof(cmdline),
                     va("+set fs_game \"%s\" ", argv[++i]));
    }

    /* THE PRINT LOCK AND THE CONSOLE MUST EXIST BEFORE THE FIRST Com_Printf.
     * Com_Printf opens with EnterCriticalSection(&printCriticalSection), and
     * the only place that section is ever initialised is sys_main.c -- which
     * this host deliberately does not compile, because sys_main.c owns main().
     * Without it the first print inside Com_Init dies in ntdll with no output
     * at all, which reads like a crash before main and is not. */
    InitializeCriticalSection(&printCriticalSection);
    CON_Init();

    if (shotPath) {
        /* The script is read before Com_Init only for its dimensions; the
         * filesystem it needs is not up yet, so it must be a real OS path. */
        ParseShot(shotPath);
        Q_strcat(cmdline, sizeof(cmdline),
                 va("+set r_customwidth %d +set r_customheight %d ",
                    s_shot.width, s_shot.height));

        /* A LIGHTING PROFILE, NOT A CVAR. The director says what the picture
         * should be; the mapping to r_gamma lives here, below the boundary.
         *
         * Q3 brightens the final image with a HARDWARE gamma ramp, and
         * R_SetColorMappings disables overbright and leaves the gamma table
         * as identity when the platform reports no hardware gamma -- which a
         * headless host truthfully does. The engine's own fallback is to bake
         * the same curve into textures at upload (R_LightScaleTexture), and
         * that is what r_gamma drives. QUAKE_AUTHENTIC leaves it at the
         * engine default; CINEMATIC applies the curve a player would have
         * been running. Neither changes one byte of game truth. */
        if (!Q_stricmp(s_shot.lighting, "CINEMATIC"))
            Q_strcat(cmdline, sizeof(cmdline), "+set r_gamma 1.6 ");
        else
            Q_strcat(cmdline, sizeof(cmdline), "+set r_gamma 1.0 ");
    } else {
        /* --dump-model asks the filesystem a question; it has no world and
         * needs none. Demanding a map here would make an asset query depend
         * on naming a level it never loads. */
        if (!cliMap[0] && !s_dumpModel && !s_demoScan && !s_dumpSnapshots &&
            !s_selfTestRings) {
            fprintf(stderr, "PANTHEON: --map or --shot is required; the "
                            "renderer does not choose a world\n");
            return 2;
        }
        Q_strcat(cmdline, sizeof(cmdline),
                 va("+set r_customwidth %d +set r_customheight %d ", cliW, cliH));
    }
    Q_strcat(cmdline, sizeof(cmdline),
             /* r_useFbo 1: frames are drawn into a framebuffer object, not a
              * window -- see PANTHEON_RequireOffscreenTarget. Latched, so it
              * must be set before Com_Init.
              *
              * r_noborder used to be set here with a comment claiming it made
              * the window's client area the requested size. Our WGL platform
              * layer never read it; the claim was false. The window no longer
              * matters, so it is gone. */
             "+set r_mode -1 +set r_fullscreen 0 +set r_fboAntiAlias 0 "
             "+set r_useFbo 1 ");

    Com_Init(cmdline);

    if (s_dumpModel) {
        /* Answer the asset question and stop. No GL context is created, so
         * this runs anywhere -- including while a game is running, which the
         * RenderPermit would otherwise defer. */
        paPlayer_t q;
        if (!PANTHEON_ActorLoadAnimations(&q, s_dumpModel)) {
            Com_Printf("PANTHEON: could not parse animation.cfg for %s\n",
                       s_dumpModel);
            return 2;
        }
        PANTHEON_ActorDumpModel(&q);
        return 0;
    }

    if (s_demoScan) {
        /* Read a whole .dm_73 with the engine's own decoder and report what
         * it held. A snapshot counts once, when a message makes it the new
         * latest valid one -- what cgame would be offered. */
        static snapshot_t snap;
        int msgs = 0, snaps = 0, lastNum = -1, first = 0, last = 0, maxEnt = 0;

        if (!PANTHEON_Demo_Open(s_demoScan)) {
            Com_Printf("PANTHEON demo-scan: cannot open %s\n", s_demoScan);
            return 2;
        }
        while (PANTHEON_Demo_ReadMessage()) {
            msgs++;
            if (PANTHEON_Demo_Latest(&snap) && snap.messageNum != lastNum) {
                lastNum = snap.messageNum;
                if (!snaps) first = snap.serverTime;
                last = snap.serverTime;
                if (snap.numEntities > maxEnt) maxEnt = snap.numEntities;
                snaps++;
            }
        }
        Com_Printf("PANTHEON demo-scan: messages=%d gamestates=%d snapshots=%d "
                   "commands=%d clientNum=%d checksumFeed=%d firstServerTime=%d "
                   "lastServerTime=%d maxEntities=%d protocol=%s\n",
                   msgs, PANTHEON_Demo_GamestateCount(), snaps,
                   PANTHEON_Demo_CommandSequence(), PANTHEON_Demo_ClientNum(),
                   PANTHEON_Demo_ChecksumFeed(), first, last, maxEnt,
                   Cvar_VariableString("protocol"));
        PANTHEON_Demo_Close();
        return 0;
    }

    if (s_selfTestRings)
        return G1_SelfTestRings();

    if (s_dumpSnapshots) {
        /* G1: everything the reader hands cgame, every field by name.
         *   F  field names, once per kind       G  gamestate
         *   Q  each server command as sequenced D  every parsed frame
         *   S  snapshot header  P  playerstate  E  entity  C  configstrings
         * Tab-separated; no GL context, so it runs anywhere. */
        static snapshot_t snap;
        static unsigned long long csPrev[MAX_CONFIGSTRINGS];
        int lastNum = -1, lastGs = 0, k;

        if (!PANTHEON_Demo_Open(s_dumpSnapshots)) {
            fprintf(stderr, "PANTHEON: cannot open %s\n", s_dumpSnapshots);
            return 2;
        }
        PANTHEON_Demo_Trace(stdout);
        G1_PrintFieldNames();
        while (PANTHEON_Demo_ReadMessage()) {
            if (PANTHEON_Demo_GamestateCount() != lastGs) {
                const gameState_t *gs = PANTHEON_Demo_GameState();
                const char *proto = Cvar_VariableString("protocol");
                lastGs = PANTHEON_Demo_GamestateCount();
                /* The field tables are protocol 73's. Anything else is an
                 * unsupported profile: fail, never compare with the wrong
                 * table and call it agreement. */
                if (strcmp(proto, "73")) {
                    fprintf(stderr, "PANTHEON: --dump-snapshots supports protocol "
                                    "73 only; this demo is %s\n", proto);
                    PANTHEON_Demo_Close();
                    return 3;
                }
                printf("G\t%d\t%d\t%s\t%016llx\t%d\n", PANTHEON_Demo_ClientNum(),
                       PANTHEON_Demo_ChecksumFeed(), proto, G1_CsSetHash(gs),
                       PANTHEON_Demo_CommandSequence());
                for (k = 0; k < MAX_CONFIGSTRINGS; k++) csPrev[k] = G1_CsHash(gs, k);
            }
            if (!PANTHEON_Demo_Latest(&snap) || snap.messageNum == lastNum) continue;
            lastNum = snap.messageNum;
            printf("S\t%d\t%d\t%d\t%d\t%d\t%d\n", snap.messageNum, snap.serverTime,
                   snap.snapFlags, snap.serverCommandSequence, snap.numEntities,
                   PANTHEON_Demo_LatestParseEntities());
            G1_PrintPlayerState(&snap.ps, snap.serverTime);
            for (k = 0; k < snap.numEntities; k++)
                G1_PrintEntity(&snap.entities[k], snap.serverTime);
            G1_PrintConfigstrings(PANTHEON_Demo_GameState(), snap.serverTime, csPrev);
        }
        fflush(stdout);
        PANTHEON_Demo_Close();
        return 0;
    }

    memset(&ri, 0, sizeof(ri));
    ri.Printf = PANTHEON_RefPrintf;
    ri.Error = Com_Error;
    ri.Milliseconds = Sys_Milliseconds;
    ri.Hunk_Alloc = Hunk_Alloc;
    ri.Hunk_AllocateTempMemory = Hunk_AllocateTempMemory;
    ri.Hunk_FreeTempMemory = Hunk_FreeTempMemory;
    ri.Malloc = Z_Malloc;
    ri.Free = Z_Free;
    ri.Cvar_Get = Cvar_Get;
    ri.Cvar_Set = Cvar_Set;
    ri.Cvar_CheckRange = Cvar_CheckRange;
    ri.Cmd_AddCommand = Cmd_AddCommand;
    ri.Cmd_RemoveCommand = Cmd_RemoveCommand;
    ri.Cmd_Argc = Cmd_Argc;
    ri.Cmd_Argv = Cmd_Argv;
    ri.Cmd_ExecuteText = Cbuf_ExecuteText;
    ri.FS_ReadFile = FS_ReadFile;
    ri.FS_FreeFile = FS_FreeFile;
    ri.FS_WriteFile = FS_WriteFile;
    ri.FS_FreeFileList = FS_FreeFileList;
    ri.FS_ListFiles = FS_ListFiles;
    ri.FS_FileIsInPAK = FS_FileIsInPAK;
    ri.FS_FileExists = FS_FileExists;
    ri.CM_DrawDebugSurface = CM_DrawDebugSurface;

    re = GetRefAPI(REF_API_VERSION, &ri);
    if (!re) Com_Error(ERR_FATAL, "GetRefAPI returned NULL");
    PANTHEON_ActorInit(re);

    {   /* BeginRegistration creates the GL context via GLimp_Init. */
        memset(&s_glconfig, 0, sizeof(s_glconfig));
        re->BeginRegistration(&s_glconfig);
        PANTHEON_RequireOffscreenTarget();
    }

    /* Models and skins must register BEFORE EndRegistration closes the pass,
     * or a handle comes back 0 and the actor silently is not drawn.
     *
     * With --cgame the world is loaded by CG_Init instead. cgame owns that
     * call -- it loads the collision model alongside it and keeps its own
     * record of which map it is in -- and the renderer refuses a second load
     * outright rather than quietly doing it twice. */
    if (!s_cgame)
        re->LoadWorld(va("maps/%s.bsp",
                         shotPath ? s_shot.map : cliMap));

    /* With cgame in charge, PANTHEON's own actor renderer is not used: cgame
     * registers the player models, the weapons and the missiles itself, from
     * the configstrings, exactly as it does in a game. Registering them twice
     * here would only mean two places that can disagree about which model a
     * client is wearing. */
    if (shotPath && !s_cgame) {
        for (i = 0; i < s_shot.numModels; i++) {
            s_shot.modelHandle[i] = re->RegisterModel(s_shot.modelPath[i]);
            if (!s_shot.modelHandle[i])
                Com_Error(ERR_FATAL, "PANTHEON: model '%s' would not register; "
                          "refusing to render a frame missing it",
                          s_shot.modelPath[i]);
        }
        for (i = 0; i < s_shot.numPlayers; i++)
            if (!PANTHEON_ActorRegister(&s_players[i], s_shot.playerModel[i],
                                        s_shot.playerSkin[i]))
                Com_Error(ERR_FATAL, "PANTHEON: player '%s' would not register; "
                          "refusing to render a frame without him",
                          s_shot.playerModel[i]);
    } else if (cliActor) {
        s_shot.numPlayers = 1;
        if (!PANTHEON_ActorRegister(&s_players[0], cliModel, cliSkin))
            Com_Error(ERR_FATAL, "PANTHEON: actor '%s' would not register",
                      cliModel);
    }
    if (s_cgame) {
        /* Feed cgame BEFORE CG_Init: it reads the gamestate for the map and
         * gametype, and needs a snapshot pair to have a world at all. */
        gameState_t gs;
        snapshot_t  snap;
        int n;

        PANTHEON_CG_BindRenderer(re, &s_glconfig);
        PANTHEON_CG_BuildGameState(&gs, shotPath ? s_shot.map : cliMap, 0);
        /* Slot 0 is the camera. The shot's cast starts at slot 1, so a real
         * player is never confused with the observer. */
        for (i = 0; shotPath && i < s_shot.numPlayers; i++)
            PANTHEON_CG_AddPlayerInfo(&gs, i + 1, s_shot.playerModel[i],
                                      s_shot.playerSkin[i]);
        /* Client 0 is the camera slot the composed snapshots use. */
        PANTHEON_CG_LoadGameState(&gs, 0);

        /* A pair 50 ms apart, both holding the requested view. cgame
         * interpolates between them; identical poses mean a still camera,
         * which is what a single frame wants. The CONTENT is not identical:
         * the rocket moves between them, because a rocket at the same place
         * in both snapshots is a rocket with no velocity, and cgame draws
         * that as a stationary ball with no trail. */
        if (shotPath) {
            /* THE BRIDGE. A shot frame and a snapshot are the same statement
             * made twice: a time, a camera, and what existed. Every frame the
             * trace produced becomes snapshot n+1, in order, and cgame walks
             * them exactly as it walks a demo -- interpolating, transitioning
             * entities, firing events, laying trails.
             *
             * Two are pushed before CG_Init because cgame refuses to have a
             * world until it can interpolate between a pair; the rest are
             * pushed as the render loop reaches them, which is what keeps a
             * long sequence from having to fit in the ring at once. */
            for (n = 1; n <= 2 && n <= s_shot.numFrames; n++)
                PANTHEON_ShotSnapshot(n);
        } else
        for (n = 1; n <= 2; n++) {
            int t = 1000 + (n - 1) * 50;
            PANTHEON_CG_ComposeSnapshot(&snap, t, n, cliOrigin, cliAngles);
            if (cliRocket) {
                vec3_t org;
                VectorMA(cliRocketOrg, (t - 1000) / 1000.0f, cliRocketVel, org);
                PANTHEON_CG_AddRocket(&snap, 20, org, cliRocketVel, 1000);
            }
            /* The explosion is fed ONLY in the second snapshot. A temp event
             * fires on the transition INTO the snapshot that carries it; put
             * it in both and cgame sees one event, not two, and fires it at
             * whichever transition it happens to process. */
            if (cliBoom && n == 2)
                PANTHEON_CG_AddExplosion(&snap, 21, cliBoomOrg, cliBoomNormal);
            PANTHEON_CG_SetSnapshot(n, &snap);
        }
        /* clientNum 0, snapshot 1, no server commands: what a composed take is. */
        PANTHEON_CG_Init(0, 1, 0);
        /* CG_Init DRAWS. It paints a loading screen and calls
         * trap_UpdateScreen after every asset, and those 2D commands queue up
         * in the renderer command list. Nothing presented them, because
         * PANTHEON has no screen to update -- so without this they are still
         * queued when the real frame is flushed, and the finished image comes
         * out with the loading screen composited on top of the world. Drained
         * here into a buffer nobody reads.
         *
         * The second drain was added on the theory that a swap moves stale
         * pixels between front and back buffers. That theory was wrong --
         * GLimp_EndFrame never swaps, and the stale pixels were GL pixel
         * ownership in a window (see PANTHEON_RequireOffscreenTarget). One
         * drain flushes the queue. The second is kept only because removing
         * it has not been tested; it costs one empty frame. */
        re->EndFrame(NULL, NULL);
        re->BeginFrame(STEREO_CENTER, qfalse);
        re->EndFrame(NULL, NULL);
    }

    re->EndRegistration();

    /*
     * THE SIZE WE ASKED FOR IS NOT NECESSARILY THE SIZE WE GOT.
     *
     * r_customwidth/r_customheight are a REQUEST. The window manager, the
     * pixel format and r_mode all get a say, and glConfig reports what was
     * actually created. Reading a 1280x720 rectangle out of a drawable that
     * is not 1280x720 succeeds -- glReadPixels does not object to a rectangle
     * larger than the buffer -- and fills the surplus with whatever happens to
     * be in that memory, which in a renderer that has just uploaded a few
     * thousand textures is texture data.
     *
     * That is the "corner artefact" this project has been looking at: not a
     * corner, and not an artefact, but the frame plus a margin of somebody
     * else's memory. A shrunken world inside a black band is the same fault
     * seen from the other side.
     *
     * So the drawable is the authority. A mismatch is reported rather than
     * silently accepted, because a frame that is quietly not the resolution it
     * claims will be composited against ones that are.
     */
    if (s_glconfig.vidWidth > 0 && s_glconfig.vidHeight > 0) {
        int reqW = shotPath ? s_shot.width  : cliW;
        int reqH = shotPath ? s_shot.height : cliH;
        if (s_glconfig.vidWidth != reqW || s_glconfig.vidHeight != reqH) {
            /* A HARD STOP, NOT A WARNING. This used to adopt the smaller size
             * and carry on, which is how a 5120x2880 request quietly became
             * a 1280x720 render with one yellow line in a log nobody reads.
             * A frame that is not the resolution it was asked for is a
             * different deliverable, and it must not ship as the asked-for
             * one. */
            Com_Error(ERR_FATAL, "PANTHEON: asked for %dx%d, the render "
                      "target is %dx%d; refusing to deliver a different "
                      "resolution than the shot requested",
                      reqW, reqH, s_glconfig.vidWidth, s_glconfig.vidHeight);
        }
    }

    {
        size_t np = (size_t)(shotPath ? s_shot.width : cliW) *
                    (size_t)(shotPath ? s_shot.height : cliH);
        pixels = malloc(np * 3);
        if (cliBlur > 1) {
            blurAccum = calloc(np * 3, sizeof(unsigned));
            Com_Printf("PANTHEON: motion blur %d sub-frames, shutter %.2f of "
                       "the frame interval\n", cliBlur, cliShutter);
        }
        if (cliDepth) depthPix = malloc(np * sizeof(float));
    }

  for (take = 0; take < (numShots > 1 ? numShots : 1); take++) {

    /* Take 0 is already loaded and already inside cgame -- its CG_Init ran in
     * the registration window, which is where cgame expects to register its
     * media. Every take after it re-parses, tears cgame down and starts it
     * again on the world that is already resident. Its assets come back from
     * the renderer's cache; a genuinely new model would still register, and
     * if a handle ever came back 0 the shot refuses to render rather than
     * quietly dropping what it could not find. */
    if (take > 0) {
        gameState_t gs;
        int n;

        free(s_shot.frames);
        memset(&s_shot, 0, sizeof(s_shot));
        ParseShot(shotPaths[take]);
        if (s_shot.width != s_glconfig.vidWidth ||
            s_shot.height != s_glconfig.vidHeight)
            ShotError("%s asks for %dx%d; the run is %dx%d and the window is "
                      "created once", shotPaths[take], s_shot.width,
                      s_shot.height, s_glconfig.vidWidth, s_glconfig.vidHeight);

        PANTHEON_CG_Shutdown();
        PANTHEON_CG_BuildGameState(&gs, s_shot.map, 0);
        for (i = 0; i < s_shot.numPlayers; i++)
            PANTHEON_CG_AddPlayerInfo(&gs, i + 1, s_shot.playerModel[i],
                                      s_shot.playerSkin[i]);
        PANTHEON_CG_LoadGameState(&gs, 0);     /* a new take is a new game */
        for (n = 1; n <= 2 && n <= s_shot.numFrames; n++)
            PANTHEON_ShotSnapshot(n);
        PANTHEON_CG_Init(0, 1, 0);
        re->EndFrame(NULL, NULL);
        re->BeginFrame(STEREO_CENTER, qfalse);
        re->EndFrame(NULL, NULL);
        Com_Printf("PANTHEON: take %d/%d -- %s (%d frames)\n",
                   take + 1, numShots, s_shot.map, s_shot.numFrames);
    }

    for (fi = 0; fi < (shotPath ? s_shot.numFrames : 1); fi++) {
        int w = shotPath ? s_shot.width : cliW;
        int h = shotPath ? s_shot.height : cliH;
        const char *out;
        int time_ms;

        memset(&rd, 0, sizeof(rd));
        if (shotPath) {
            shotFrame_t *sf = &s_shot.frames[fi];
            VectorCopy(sf->cam_origin, rd.vieworg);
            AnglesToAxis(sf->cam_angles, rd.viewaxis);
            rd.fov_x = sf->fov;
            time_ms = sf->server_time_ms;
            out = sf->out;
        } else {
            VectorCopy(cliOrigin, rd.vieworg);
            AnglesToAxis(cliAngles, rd.viewaxis);
            rd.fov_x = cliFov;
            time_ms = 0;
            out = cliOut;
        }
        rd.x = 0; rd.y = 0;
        rd.width = w; rd.height = h;
        rd.fov_y = rd.fov_x * h / w;
        rd.time = time_ms;
        rd.rdflags = s_noWorld ? RDF_NOWORLDMODEL : 0;

      /* THE SHUTTER.
       *
       * Sub-frames run over (t - shutter*dt, t], i.e. the shutter closes ON
       * the frame's own timestamp. A shutter centred on t would be more
       * photographically pure and would run cg.time BACKWARDS between output
       * frames, which cgame reads as a demo rewind -- it has a whole branch
       * for that -- and would re-fire events already transitioned. Trailing
       * keeps every sub-time monotonic across the entire sequence, which is
       * the only ordering cgame's snapshot machinery accepts. */
      blurSamples = (cliBlur > 1) ? cliBlur : 1;
      if (blurAccum) memset(blurAccum, 0, (size_t)w * h * 3 * sizeof(unsigned));

      for (blurSub = 0; blurSub < blurSamples; blurSub++) {
        int subTime = time_ms;
        if (blurSamples > 1) {
            int dt = (shotPath && fi > 0)
                   ? time_ms - s_shot.frames[fi - 1].server_time_ms : 33;
            float span = (float)dt * cliShutter;
            subTime = time_ms - (int)(span * (blurSamples - 1 - blurSub)
                                      / (float)blurSamples);
        }
        rd.time = subTime;

        re->BeginFrame(STEREO_CENTER, qfalse);

        /* CLEAR WHAT THE FRAME DOES NOT COVER.
         *
         * The 3D view is not guaranteed to fill the buffer: cgame sizes it
         * from cg_viewsize and the HUD layout, and the renderer only clears
         * inside the viewport it is given. Whatever the frame does not draw
         * keeps the PREVIOUS contents of that buffer -- which, on the first
         * frame, is the loading screen cgame painted during CG_Init.
         *
         * This is the whole of the "corner artefact": a correct world with a
         * margin of the last thing that was on screen. It is an immediate GL
         * call rather than a render command because the renderer's command
         * list is not flushed until EndFrame, so this lands underneath the
         * frame instead of on top of it. */
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        if (s_cgame) {
            /* cgame owns the scene: it clears it, adds every entity and
             * effect, and calls RenderScene itself. The camera comes from the
             * snapshot's playerState, not from rd -- which is the whole
             * point, because a snapshot is something we compose. */
            /* Keep one snapshot AHEAD of the frame being drawn, so cgame
             * always has a nextSnap to interpolate toward. Without it every
             * frame is the tail of the pair and the world stops moving
             * between them -- which looks like a low frame rate rather than
             * like a bug. */
            if (shotPath && fi + 3 <= s_shot.numFrames && blurSub == 0)
                PANTHEON_ShotSnapshot(fi + 3);
            PANTHEON_CG_DrawActiveFrame(subTime, fi == 0 && blurSub == 0);
            re->EndFrame(NULL, NULL);
            goto pantheon_readback;
        }

        re->ClearScene();

        if (shotPath) {
            shotFrame_t *sf = &s_shot.frames[fi];
            int a;
            for (a = 0; a < sf->numActors; a++) {
                int wm = sf->actors[a].weaponModel;
                PANTHEON_ActorAdd(&s_players[sf->actors[a].player],
                                  sf->actors[a].origin,
                                  sf->actors[a].legsAngles,
                                  sf->actors[a].torsoAngles,
                                  sf->actors[a].headAngles,
                                  sf->actors[a].legsFrame,
                                  sf->actors[a].legsOldFrame,
                                  sf->actors[a].legsBacklerp,
                                  sf->actors[a].torsoFrame,
                                  sf->actors[a].torsoOldFrame,
                                  sf->actors[a].torsoBacklerp,
                                  wm >= 0 ? s_shot.modelHandle[wm] : 0);
            }
            for (a = 0; a < sf->numMissiles; a++)
                PANTHEON_MissileAdd(s_shot.modelHandle[sf->missiles[a].model],
                                    sf->missiles[a].origin,
                                    sf->missiles[a].angles);
        } else if (cliActor) {
            {
                vec3_t zero = {0, 0, 0};
                (void)cliLegs; (void)cliTorso;
                PANTHEON_ActorAdd(&s_players[0], cliActorOrigin,
                                  cliActorAngles, zero, zero,
                                  cliLegsFrame, cliLegsOldFrame,
                                  cliLegsBacklerp,
                                  cliTorsoFrame, cliTorsoOldFrame,
                                  cliTorsoBacklerp, 0);
            }
        }

        re->RenderScene(&rd);
        re->EndFrame(NULL, NULL);

pantheon_readback:
        /* READ FROM THE FRAMEBUFFER OBJECT.
         *
         * RB_SwapBuffers unbinds the FBO to blit the scene into the 64x64 DC
         * window, calls GLimp_EndFrame, and binds the FBO again "for video
         * and screenshots" (tr_backend.c). So at this point the FBO is the
         * read framebuffer, and its colour attachment holds exactly the frame
         * -- every pixel defined, because nothing on the desktop owns it.
         *
         * The earlier comment here explained stale output as one buffer
         * behind after a swap. That was wrong: GLimp_EndFrame never swaps. The
         * stale pixels were pixel ownership in a window, which no longer
         * applies. glFinish stays: readback must wait for the GPU. */
        glFinish();
        PANTHEON_RequireOffscreenTarget();
        glReadBuffer(GL_COLOR_ATTACHMENT0_EXT);
        glPixelStorei(GL_PACK_ALIGNMENT, 1);
        glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, pixels);
        if (blurAccum) PANTHEON_BlurAccumulate(blurAccum, pixels, w * h * 3);
        else           WriteTGA(out, pixels, w, h);

        if (cliDepth && (!blurAccum || blurSub == cliBlur - 1)) {
            /* The depth of the LAST sub-frame, not an average of them. An
             * averaged depth buffer is a surface that exists nowhere: half in
             * front of the wall and half behind it. Motion blur belongs to the
             * colour pass; depth stays a measurement of one instant. */
            char dpath[MAX_OSPATH];
            Q_strncpyz(dpath, out, sizeof(dpath));
            {
                char *dot = strrchr(dpath, '.');
                if (dot) Q_strncpyz(dot, ".depth.pgm",
                                    sizeof(dpath) - (dot - dpath));
            }
            glReadPixels(0, 0, w, h, GL_DEPTH_COMPONENT, GL_FLOAT, depthPix);
            WritePGM16(dpath, depthPix, w, h, 4.0f, 65536.0f);
        }
      }   /* sub-frame */

        if (blurAccum) {
            PANTHEON_BlurResolve(pixels, blurAccum, w * h * 3, blurSamples);
            WriteTGA(out, pixels, w, h);
        }

        if (shotPath && (fi % 10 == 0 || fi == s_shot.numFrames - 1))
            Com_Printf("PANTHEON: frame %d/%d t=%d -> %s\n",
                       fi + 1, s_shot.numFrames, time_ms, out);
    }
    totalFrames += shotPath ? s_shot.numFrames : 1;
  }

    free(pixels);
    free(blurAccum);
    free(depthPix);
    if (shotPath)
        Com_Printf("PANTHEON: wrote %d frames across %d take%s (%dx%d) "
                   "map=%s provenance=%s\n",
                   totalFrames, numShots, numShots == 1 ? "" : "s",
                   s_shot.width, s_shot.height,
                   s_shot.map, s_shot.provenance);
    else
        Com_Printf("PANTHEON: wrote %s (%dx%d) map=%s\n",
                   cliOut, cliW, cliH, cliMap);

    re->Shutdown(qtrue);
    return 0;
}
