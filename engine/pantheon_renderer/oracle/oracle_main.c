/*
 * The oracle harness.
 *
 * Reads a state sequence on stdin, runs the ENGINE'S OWN CG_PlayerAngles /
 * CG_SwingAngles over it, and prints the resulting swing state and part axes.
 * PANTHEON is fed the identical sequence and the two are diffed. Nothing here
 * consults PANTHEON.
 *
 * Input, one step per line:
 *   <frametime_ms> <viewYaw> <viewPitch> <legsAnim> <torsoAnim> <moveDir>
 *   <eFlags> <velX> <velY> <velZ> <cgTime> <painTime> <painDir>
 *   <fixedLegs> <fixedTorso>
 *
 * Output, one line per step:
 *   <legsYaw> <torsoYaw> <torsoPitch> <legsAxis 0..8> <torsoAxis 0..8>
 *   <headAxis 0..8>
 */
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>

#include "oracle_context.h"

oracleCg_t   cg;
oracleCgs_t  cgs;
oracleCvar_t cg_swingSpeed      = { 0.3f, 0 };   /* cg_swingSpeed default */
oracleCvar_t cg_playerLeanScale = { 1.0f, 1 };   /* cg_playerLeanScale default */

qboolean CG_FreezeTagFrozen(int clientNum) { (void)clientNum; return qfalse; }

void QDECL CG_Error(const char *msg, ...)
{
    va_list ap;
    fprintf(stderr, "ORACLE CG_Error: ");
    va_start(ap, msg);
    vfprintf(stderr, msg, ap);
    va_end(ap);
    fprintf(stderr, "\n");
    exit(3);
}

/* q_shared/q_math reach for these. The oracle prints and exits rather than
 * continuing, so a shared-code complaint cannot pass unnoticed. */
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
    centity_t cent;
    int first = 1;

    memset(&cent, 0, sizeof(cent));
    memset(&cgs, 0, sizeof(cgs));

    while (fgets(line, sizeof(line), stdin)) {
        float ft, yaw, pitch, vx, vy, vz;
        int legsAnim, torsoAnim, moveDir, eFlags, i;
        int cgTime, painTime, painDir, fixedLegs, fixedTorso;
        vec3_t legs[3], torso[3], head[3];

        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        if (sscanf(line, "%f %f %f %d %d %d %d %f %f %f %d %d %d %d %d",
                   &ft, &yaw, &pitch, &legsAnim, &torsoAnim, &moveDir,
                   &eFlags, &vx, &vy, &vz, &cgTime, &painTime, &painDir,
                   &fixedLegs, &fixedTorso) != 15) {
            fprintf(stderr, "ORACLE: bad input line: %s", line);
            return 2;
        }

        cg.frametime = (int)ft;
        cg.time = cgTime;
        cent.pe.painTime = painTime;
        cent.pe.painDirection = painDir;
        cgs.clientinfo[0].fixedlegs = fixedLegs ? qtrue : qfalse;
        cgs.clientinfo[0].fixedtorso = fixedTorso ? qtrue : qfalse;
        cent.lerpAngles[PITCH] = pitch;
        cent.lerpAngles[YAW] = yaw;
        cent.lerpAngles[ROLL] = 0.0f;
        cent.currentState.legsAnim = legsAnim;
        cent.currentState.torsoAnim = torsoAnim;
        cent.currentState.angles2[YAW] = (float)moveDir;
        cent.currentState.eFlags = eFlags;
        cent.currentState.clientNum = 0;
        cent.currentState.pos.trDelta[0] = vx;
        cent.currentState.pos.trDelta[1] = vy;
        cent.currentState.pos.trDelta[2] = vz;

        if (first) {
            /* CG_NewClientInfo/CG_ResetPlayerEntity centre a newly seen
             * player rather than swinging in from zero. The harness does the
             * same, once, so both sides start from the same state. */
            cent.pe.legs.yawAngle = yaw;
            cent.pe.torso.yawAngle = yaw;
            cent.pe.torso.pitchAngle = pitch * 0.75f;
            cent.pe.legs.yawing = qfalse;
            cent.pe.torso.yawing = qfalse;
            cent.pe.torso.pitching = qfalse;
            first = 0;
        }

        CG_PlayerAngles(&cent, legs, torso, head);

        printf("%.6f %.6f %.6f", cent.pe.legs.yawAngle,
               cent.pe.torso.yawAngle, cent.pe.torso.pitchAngle);
        for (i = 0; i < 3; i++)
            printf(" %.6f %.6f %.6f", legs[i][0], legs[i][1], legs[i][2]);
        for (i = 0; i < 3; i++)
            printf(" %.6f %.6f %.6f", torso[i][0], torso[i][1], torso[i][2]);
        for (i = 0; i < 3; i++)
            printf(" %.6f %.6f %.6f", head[i][0], head[i][1], head[i][2]);
        printf("\n");
    }
    return 0;
}
