/*
 * Minimal engine context for the extracted cgame presentation functions.
 *
 * The functions in oracle_generated.c are the engine's own, byte for byte.
 * They reach for a handful of cgame globals, and this header supplies the
 * smallest honest stand-in for each. NOTHING HERE MAY CHANGE AN ALGORITHM --
 * if a stub had to make a decision the original makes, the oracle would stop
 * being independent evidence and become a second opinion of my own.
 */
#ifndef ORACLE_CONTEXT_H
#define ORACLE_CONTEXT_H

#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/game/bg_public.h"

/* ── the cgame types the two functions touch ────────────────────────────── */
/* animation_t and MAX_TOTALANIMATIONS come from bg_public.h, included above. */
typedef struct {
    const animation_t *animation;   /* what CG_SetLerpFrameAnimation resolves */
    int       oldFrame;
    int       frame;
    float     backlerp;
    float     yawAngle;
    qboolean  yawing;
    float     pitchAngle;
    qboolean  pitching;
    int       animationNumber;
    int       animationTime;
    int       frameTime;
    int       oldFrameTime;
} oracleLerpFrame_t;

typedef struct {
    oracleLerpFrame_t legs, torso;
    int      painTime;       /* cg.time of the last EV_PAIN */
    int      painDirection;  /* alternates 0/1 on each pain */
} oraclePlayerEntity_t;

typedef struct {
    entityState_t        currentState;
    vec3_t               lerpAngles;
    oraclePlayerEntity_t pe;
} oracleCentity_t;

#define centity_t      oracleCentity_t
#define lerpFrame_t    oracleLerpFrame_t
#define playerEntity_t oraclePlayerEntity_t

typedef struct {
    qboolean fixedtorso;
    qboolean fixedlegs;
    animation_t animations[MAX_TOTALANIMATIONS];
} oracleClientInfo_t;
#define clientInfo_t oracleClientInfo_t

/* cvar_t as the engine's code reads it: some sites use .value, some .integer.
 * Both are provided so a lifted function needs no editing. */
typedef struct { float value; int integer; } oracleCvar_t;

/* ── the globals, as plain data the harness sets ────────────────────────── */
typedef struct { int frametime; int time; } oracleCg_t;
typedef struct { oracleClientInfo_t clientinfo[MAX_CLIENTS]; } oracleCgs_t;

extern oracleCg_t   cg;
extern oracleCgs_t  cgs;
extern oracleCvar_t cg_swingSpeed;
extern oracleCvar_t cg_playerLeanScale;

/* Freeze-tag state is not part of what is under test, and the engine's own
 * body for that branch is empty anyway. */
qboolean CG_FreezeTagFrozen(int clientNum);

/* cg_local.h. The twitch runs for 200 ms and decays linearly. */
#define PAIN_TWITCH_TIME 200

/* CG_AddPainTwitch is now LIFTED from the source, not declared here as a
 * stub -- its body arrives in oracle_generated.c with everything it needs
 * (cg.time and cent->pe.painTime/painDirection). */

void QDECL CG_Error(const char *msg, ...);
void QDECL CG_Printf(const char *msg, ...);
extern oracleCvar_t cg_animSpeed;
extern oracleCvar_t cg_debugAnim;

void CG_RunLerpFrame(const clientInfo_t *ci, lerpFrame_t *lf,
                     int newAnimation, float speedScale, int time);
void CG_ClearLerpFrame(const clientInfo_t *ci, lerpFrame_t *lf,
                       int animationNumber, int time);

void CG_PlayerAngles(centity_t *cent, vec3_t legs[3], vec3_t torso[3],
                     vec3_t head[3]);

#endif
