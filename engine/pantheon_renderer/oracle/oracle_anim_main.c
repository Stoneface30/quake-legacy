/*
 * ANIMATION_PHASE oracle harness.
 *
 * Runs the ENGINE'S OWN CG_RunLerpFrame / CG_SetLerpFrameAnimation /
 * CG_SetAnimFrame / CG_ClearLerpFrame over a state sequence and prints the
 * resulting lerpFrame_t. PANTHEON is fed the identical sequence and diffed.
 *
 * Input:
 *   line 1:  "anims <count>"
 *   then <count> lines: <first> <num> <loop> <frameLerp> <initialLerp>
 *                       <reversed> <flipflop>
 *   then:    "clear <animationNumber> <time>"      (optional, once)
 *   then N:  "step <animationNumber> <speedScale> <time>"
 *
 * Output, one line per step:
 *   <animationNumber> <animationTime> <frameTime> <oldFrameTime>
 *   <oldFrame> <frame> <backlerp>
 */
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>

#include "oracle_context.h"

oracleCg_t   cg;
oracleCgs_t  cgs;
oracleCvar_t cg_swingSpeed      = { 0.3f, 0 };
oracleCvar_t cg_playerLeanScale = { 1.0f, 1 };
oracleCvar_t cg_animSpeed       = { 1.0f, 1 };
oracleCvar_t cg_debugAnim       = { 0.0f, 0 };

qboolean CG_FreezeTagFrozen(int clientNum) { (void)clientNum; return qfalse; }

void QDECL CG_Error(const char *msg, ...)
{
    va_list ap;
    fprintf(stderr, "ORACLE CG_Error: ");
    va_start(ap, msg); vfprintf(stderr, msg, ap); va_end(ap);
    fprintf(stderr, "\n");
    exit(3);
}

void QDECL CG_Printf(const char *msg, ...)
{
    va_list ap;
    va_start(ap, msg); vfprintf(stderr, msg, ap); va_end(ap);
}

void QDECL Com_Printf(const char *msg, ...)
{
    va_list ap;
    va_start(ap, msg); vfprintf(stderr, msg, ap); va_end(ap);
}

void QDECL Com_Error(int level, const char *msg, ...)
{
    va_list ap;
    (void)level;
    fprintf(stderr, "ORACLE Com_Error: ");
    va_start(ap, msg); vfprintf(stderr, msg, ap); va_end(ap);
    fprintf(stderr, "\n");
    exit(3);
}

int main(void)
{
    char line[512];
    clientInfo_t ci;
    lerpFrame_t lf;
    int cleared = 0;

    memset(&ci, 0, sizeof(ci));
    memset(&lf, 0, sizeof(lf));

    while (fgets(line, sizeof(line), stdin)) {
        char kw[32];
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        if (sscanf(line, "%31s", kw) != 1) continue;

        if (!strcmp(kw, "anims")) {
            int n, i;
            if (sscanf(line, "%*s %d", &n) != 1) return 2;
            for (i = 0; i < n; i++) {
                if (!fgets(line, sizeof(line), stdin)) return 2;
                if (sscanf(line, "%d %d %d %d %d %d %d",
                           &ci.animations[i].firstFrame,
                           &ci.animations[i].numFrames,
                           &ci.animations[i].loopFrames,
                           &ci.animations[i].frameLerp,
                           &ci.animations[i].initialLerp,
                           &ci.animations[i].reversed,
                           &ci.animations[i].flipflop) != 7) {
                    fprintf(stderr, "ORACLE: bad anim line: %s", line);
                    return 2;
                }
            }
        } else if (!strcmp(kw, "clear")) {
            int anim, t;
            if (sscanf(line, "%*s %d %d", &anim, &t) != 2) return 2;
            CG_ClearLerpFrame(&ci, &lf, anim, t);
            cleared = 1;
        } else if (!strcmp(kw, "step")) {
            int anim, t;
            float scale;
            if (sscanf(line, "%*s %d %f %d", &anim, &scale, &t) != 3) return 2;
            CG_RunLerpFrame(&ci, &lf, anim, scale, t);
            printf("%d %d %d %d %d %d %.6f\n",
                   lf.animationNumber, lf.animationTime, lf.frameTime,
                   lf.oldFrameTime, lf.oldFrame, lf.frame, lf.backlerp);
        } else {
            fprintf(stderr, "ORACLE: unknown keyword %s\n", kw);
            return 2;
        }
    }
    (void)cleared;
    return 0;
}
