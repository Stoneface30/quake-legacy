/* PANTHEON player assembly -- see pantheon_actor.c. */
#ifndef PANTHEON_ACTOR_H
#define PANTHEON_ACTOR_H

#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_public.h"

/* MAX_ANIMATIONS / MAX_TOTALANIMATIONS from bg_public.h. The file declares
 * 31; the engine then DERIVES six more (backward-crouch, backward-walk and
 * the three flag animations), so a table sized to the file alone is short. */
#define PA_FILE_ANIMATIONS  31
#define PA_MAX_ANIMATIONS   37

typedef struct {
    int firstFrame;
    int numFrames;
    int loopFrames;
    int frameLerp;
    int initialLerp;
    qboolean reversed;
    qboolean flipflop;
} paAnim_t;

typedef struct {
    char      model[MAX_QPATH];
    qhandle_t legs, torso, head;
    qhandle_t skinLegs, skinTorso, skinHead;
    paAnim_t  anims[PA_MAX_ANIMATIONS];
    qboolean  haveAnims;
    /* Declared by the MODEL's animation.cfg, not by any configstring.
     * CG_PlayerAngles consumes them: fixedtorso holds the torso pitch at
     * zero, fixedlegs pins the legs to the torso yaw and flattens them. */
    qboolean  fixedlegs;
    qboolean  fixedtorso;
    vec3_t    headOffset;
    int       footsteps;
    int       gender;
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
                           int legsFrame, int legsOldFrame, float legsBacklerp,
                           int torsoFrame, int torsoOldFrame,
                           float torsoBacklerp,
                           qhandle_t weaponModel);

/* Print this model's parsed animation.cfg on stdout, so PANTHEON can hold the
 * animation table and the fixedlegs/fixedtorso flags itself. The host reads
 * the pak because only it can; it does not decide what the numbers mean. */
qboolean PANTHEON_ActorLoadAnimations(paPlayer_t *p, const char *model);
void     PANTHEON_ActorDumpModel(const paPlayer_t *p);

/* One missile, placed and lit. PANTHEON evaluated where it was; this only
 * draws it. */
void     PANTHEON_MissileAdd(qhandle_t model, const vec3_t origin,
                             const vec3_t angles);

#endif
