/* PANTHEON player assembly -- see pantheon_actor.c. */
#ifndef PANTHEON_ACTOR_H
#define PANTHEON_ACTOR_H

#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_public.h"

#define PA_MAX_ANIMATIONS 29

typedef struct {
    int firstFrame;
    int numFrames;
    int loopFrames;
    int frameLerp;
    qboolean reversed;
} paAnim_t;

typedef struct {
    char      model[MAX_QPATH];
    qhandle_t legs, torso, head;
    qhandle_t skinLegs, skinTorso, skinHead;
    paAnim_t  anims[PA_MAX_ANIMATIONS];
    qboolean  haveAnims;
} paPlayer_t;

void     PANTHEON_ActorInit(refexport_t *re);
qboolean PANTHEON_ActorRegister(paPlayer_t *p, const char *model,
                                const char *skin);
/* One placed player. `viewAngles` are his RECORDED view (yaw+pitch); the
 * split into legs/torso/head follows CG_PlayerAngles. `moveDir` is
 * angles2[YAW], 0-7. legs and torso carry independent animation clocks. */
/* legsAngles are world space; torsoAngles and headAngles are RELATIVE to
 * their parent. All three arrive fully composed from PANTHEON's presentation
 * evaluator, which reproduces CG_PlayerAngles and is verified against the
 * engine's own code. The host poses nothing itself. */
void     PANTHEON_ActorAdd(const paPlayer_t *p, const vec3_t origin,
                           const vec3_t legsAngles, const vec3_t torsoAngles,
                           const vec3_t headAngles,
                           int legsAnim, int torsoAnim,
                           int legs_ms, int torso_ms,
                           qhandle_t weaponModel);

/* One missile, placed and lit. PANTHEON evaluated where it was; this only
 * draws it. */
void     PANTHEON_MissileAdd(qhandle_t model, const vec3_t origin,
                             const vec3_t angles);

#endif
