/*
 * PANTHEON native renderer host -- Quake player assembly.
 *
 * A Quake player is three models bolted together: legs carry the torso at
 * "tag_torso", the torso carries the head at "tag_head". cgame normally does
 * this; the host has no cgame, so it does it here, using the renderer's own
 * LerpTag rather than a reimplementation of tag maths.
 *
 * WHAT COMES FROM WHERE. The animation NUMBERS (legs_anim, torso_anim) are
 * recorded game truth and arrive from PANTHEON. The mapping from an animation
 * number to actual MD3 frames is ASSET data, and lives in the model's own
 * animation.cfg -- so it is parsed here, from the pak, exactly as the shipped
 * client parses it. Neither is invented: this file joins truth to assets and
 * decides nothing about either.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_public.h"

#include "pantheon_actor.h"

/* animNumber_t, in bg_public.h order. Only the entries the host needs to
 * index by number; the table is read positionally from animation.cfg. */
/* animNumber_t indices, READ OFF bg_public.h rather than counted by eye.
 * LEGS_WALKCR is 13. It was 14 here, and that one-off wrecked every leg
 * animation: the skip was computed from the wrong entry AND applied to the
 * wrong range, so each leg animation played the frames of its neighbour.
 * LEGS_JUMP played LEGS_SWIM's frames -- which is exactly why the airborne
 * character looked like he was paddling. */
#define PA_LEGS_WALKCR   13
#define PA_TORSO_GESTURE  6
#define PA_TORSO_GETFLAG 25

static refexport_t *pa_re;

void PANTHEON_ActorInit(refexport_t *re) { pa_re = re; }

/*
 * animation.cfg, parsed the way cg_players.c parses it -- including the
 * correction that matters: leg animations index a DIFFERENT model whose frames
 * do not include the torso-only animations, so every leg animation's first
 * frame is shifted down by the gap. Skipping that correction does not fail
 * loudly; it silently plays the wrong animation, which is worse.
 */
static qboolean PA_ParseAnimations(paPlayer_t *p)
{
    char path[MAX_QPATH];
    char *buf = NULL;
    const char *tp;
    int len, i, skip = 0;

    Com_sprintf(path, sizeof(path), "models/players/%s/animation.cfg", p->model);
    len = FS_ReadFile(path, (void **)&buf);
    if (len <= 0 || !buf) {
        Com_Printf("PANTHEON: no %s\n", path);
        return qfalse;
    }

    tp = buf;
    for (i = 0; i < PA_MAX_ANIMATIONS; i++) {
        const char *tok;
        int fps;

        /* Skip the header keywords (sex/footsteps/headoffset) and comments by
         * only accepting a token that starts a number. */
        for (;;) {
            tok = COM_Parse((char **)&tp);
            if (!tok[0]) break;
            if ((tok[0] >= '0' && tok[0] <= '9') || tok[0] == '-') break;
        }
        if (!tok[0]) break;

        p->anims[i].firstFrame = atoi(tok);
        if (i == PA_LEGS_WALKCR)
            skip = p->anims[PA_LEGS_WALKCR].firstFrame
                 - p->anims[PA_TORSO_GESTURE].firstFrame;
        if (i >= PA_LEGS_WALKCR && i < PA_TORSO_GETFLAG)
            p->anims[i].firstFrame -= skip;

        tok = COM_Parse((char **)&tp); if (!tok[0]) break;
        p->anims[i].numFrames = atoi(tok);
        p->anims[i].reversed = qfalse;
        if (p->anims[i].numFrames < 0) {
            p->anims[i].numFrames = -p->anims[i].numFrames;
            p->anims[i].reversed = qtrue;
        }

        tok = COM_Parse((char **)&tp); if (!tok[0]) break;
        p->anims[i].loopFrames = atoi(tok);

        tok = COM_Parse((char **)&tp); if (!tok[0]) break;
        fps = atoi(tok);
        if (fps == 0) fps = 1;
        p->anims[i].frameLerp = 1000 / fps;
    }

    FS_FreeFile(buf);
    p->haveAnims = qtrue;
    return qtrue;
}

/*
 * Register one player. Every piece must exist: a player missing his legs is
 * not a player, and continuing would put a floating torso in a frame that
 * claims to be historical.
 */
qboolean PANTHEON_ActorRegister(paPlayer_t *p, const char *model,
                                const char *skin)
{
    char buf[MAX_QPATH];

    Q_strncpyz(p->model, model, sizeof(p->model));

    Com_sprintf(buf, sizeof(buf), "models/players/%s/lower.md3", model);
    p->legs = pa_re->RegisterModel(buf);
    Com_sprintf(buf, sizeof(buf), "models/players/%s/upper.md3", model);
    p->torso = pa_re->RegisterModel(buf);
    Com_sprintf(buf, sizeof(buf), "models/players/%s/head.md3", model);
    p->head = pa_re->RegisterModel(buf);

    if (!p->legs || !p->torso || !p->head) {
        Com_Printf("PANTHEON: player '%s' incomplete (legs=%d torso=%d head=%d)\n",
                   model, p->legs, p->torso, p->head);
        return qfalse;
    }

    Com_sprintf(buf, sizeof(buf), "models/players/%s/lower_%s.skin", model, skin);
    p->skinLegs = pa_re->RegisterSkin(buf);
    Com_sprintf(buf, sizeof(buf), "models/players/%s/upper_%s.skin", model, skin);
    p->skinTorso = pa_re->RegisterSkin(buf);
    Com_sprintf(buf, sizeof(buf), "models/players/%s/head_%s.skin", model, skin);
    p->skinHead = pa_re->RegisterSkin(buf);

    PA_ParseAnimations(p);
    return qtrue;
}

/* Loop or clamp one frame index, the way CG_SetAnimFrame does. */
static int PA_WrapFrame(const paAnim_t *a, int f)
{
    if (f >= a->numFrames) {
        if (a->loopFrames > 0) {
            f -= a->numFrames;
            f %= a->loopFrames;
            f += a->numFrames - a->loopFrames;
        } else {
            f = a->numFrames - 1;      /* a one-shot holds its last frame */
        }
    }
    if (f < 0) f = 0;
    if (a->reversed)
        f = a->numFrames - 1 - f;
    return f;
}


/*
 * Which MD3 frames an animation shows, and how far between them.
 *
 * This is CG_RunLerpFrame/CG_SetAnimFrame in closed form. The shipped client
 * keeps a lerpFrame_t and walks it forward one frame at a time; the same
 * result is a pure function of (time since the animation started), which is
 * what PANTHEON knows. Closed form also means frame N does not depend on
 * having rendered frame N-1, so a sequence is reproducible and seekable.
 *
 * backlerp is the ORIGINAL's convention: 1.0 means show oldFrame, 0.0 means
 * show frame. Leaving it at 0 with oldFrame == frame -- as this host did --
 * snaps between poses at the animation's own rate instead of interpolating,
 * which reads as a stutter no matter how smooth the camera is.
 */
static void PA_Frames(const paPlayer_t *p, int anim, int time_ms,
                      int *frame, int *oldFrame, float *backlerp)
{
    const paAnim_t *a;
    float u;
    int lo, hi;

    *frame = *oldFrame = 0;
    *backlerp = 0.0f;

    if (anim < 0 || anim >= PA_MAX_ANIMATIONS || !p->haveAnims)
        return;
    a = &p->anims[anim];
    if (a->numFrames <= 0 || a->frameLerp <= 0)
        return;

    if (time_ms < 0) time_ms = 0;
    u = (float)time_ms / (float)a->frameLerp;
    lo = (int)u;                       /* the frame we are coming from */
    hi = lo + 1;                       /* the frame we are going to */
    *backlerp = 1.0f - (u - (float)lo);

    *oldFrame = a->firstFrame + PA_WrapFrame(a, lo);
    *frame    = a->firstFrame + PA_WrapFrame(a, hi);
}

/* CG_PositionRotatedEntityOnTag, without cgame. */
static void PA_OnTag(refEntity_t *ent, const refEntity_t *parent,
                     qhandle_t parentModel, const char *tagName)
{
    int i;
    orientation_t lerped;
    vec3_t tmp;

    VectorCopy(parent->origin, ent->origin);
    pa_re->LerpTag(&lerped, parentModel, parent->oldframe, parent->frame,
                   1.0f - parent->backlerp, tagName);

    for (i = 0; i < 3; i++)
        VectorMA(ent->origin, lerped.origin[i], parent->axis[i], ent->origin);

    VectorCopy(ent->origin, ent->oldorigin);

    MatrixMultiply(lerped.axis, ((refEntity_t *)parent)->axis, ent->axis);
    ent->backlerp = parent->backlerp;
    (void)tmp;
}

/*
 * Re-orient a tagged part by the difference between its own angles and its
 * parent's. The tag already carries the parent's orientation; what it does
 * not carry is the extra turn the part has of its own -- the torso twisting
 * away from the hips, the head off the torso.
 */
/* The angles arrive ALREADY relative to the parent (CG_PlayerAngles does the
 * AnglesSubtract), so the host only composes them onto the tag orientation.
 * Computing the difference here as well would apply it twice. */
static void PA_RotateRelative(refEntity_t *ent, const vec3_t relAngles)
{
    vec3_t relAxis[3], result[3];

    AnglesToAxis(relAngles, relAxis);
    MatrixMultiply(relAxis, ent->axis, result);
    AxisCopy(result, ent->axis);
}


/*
 * Place one player into the scene.
 *
 * `anim_time_ms` is how long the actor has been in this animation. PANTHEON
 * knows when each animation started because it observed the change; the host
 * does not guess it.
 */
void PANTHEON_ActorAdd(const paPlayer_t *p, const vec3_t origin,
                       const vec3_t legsAngles, const vec3_t torsoAngles,
                       const vec3_t headAngles,
                       int legsAnim, int torsoAnim,
                       int legs_ms, int torso_ms, qhandle_t weaponModel)
{
    refEntity_t legs, torso, head, weapon;

    memset(&legs, 0, sizeof(legs));
    memset(&torso, 0, sizeof(torso));
    memset(&head, 0, sizeof(head));

    legs.reType = RT_MODEL;
    legs.hModel = p->legs;
    legs.customSkin = p->skinLegs;
    VectorCopy(origin, legs.origin);
    VectorCopy(origin, legs.oldorigin);
    VectorCopy(origin, legs.lightingOrigin);
    AnglesToAxis(legsAngles, legs.axis);
    PA_Frames(p, legsAnim, legs_ms, &legs.frame, &legs.oldframe,
              &legs.backlerp);
    legs.shaderRGBA[0] = legs.shaderRGBA[1] =
    legs.shaderRGBA[2] = legs.shaderRGBA[3] = 255;
    pa_re->AddRefEntityToScene(&legs);

    torso.reType = RT_MODEL;
    torso.hModel = p->torso;
    torso.customSkin = p->skinTorso;
    VectorCopy(origin, torso.lightingOrigin);
    PA_Frames(p, torsoAnim, torso_ms, &torso.frame, &torso.oldframe,
              &torso.backlerp);
    torso.shaderRGBA[0] = torso.shaderRGBA[1] =
    torso.shaderRGBA[2] = torso.shaderRGBA[3] = 255;
    PA_OnTag(&torso, &legs, p->legs, "tag_torso");
    PA_RotateRelative(&torso, torsoAngles);
    pa_re->AddRefEntityToScene(&torso);

    head.reType = RT_MODEL;
    head.hModel = p->head;
    head.customSkin = p->skinHead;
    VectorCopy(origin, head.lightingOrigin);
    head.frame = 0;
    head.oldframe = 0;
    head.backlerp = 0.0f;
    head.shaderRGBA[0] = head.shaderRGBA[1] =
    head.shaderRGBA[2] = head.shaderRGBA[3] = 255;
    PA_OnTag(&head, &torso, p->torso, "tag_head");
    PA_RotateRelative(&head, headAngles);
    pa_re->AddRefEntityToScene(&head);

    /* The weapon hangs off the torso at tag_weapon, exactly as cgame hangs
     * it. Which weapon is RECORDED state; what it looks like is asset
     * knowledge resolved upstream. A zero handle means the demo did not tell
     * us, and nothing is drawn rather than a default gun appearing in his
     * hands. */
    if (weaponModel) {
        memset(&weapon, 0, sizeof(weapon));
        weapon.reType = RT_MODEL;
        weapon.hModel = weaponModel;
        VectorCopy(origin, weapon.lightingOrigin);
        weapon.shaderRGBA[0] = weapon.shaderRGBA[1] =
        weapon.shaderRGBA[2] = weapon.shaderRGBA[3] = 255;
        PA_OnTag(&weapon, &torso, p->torso, "tag_weapon");
        pa_re->AddRefEntityToScene(&weapon);
    }
}

/*
 * A missile is one model pointed along its own velocity, plus the dynamic
 * light cgame gives it. The light values are the rocket's own (200, 1 0.75 0
 * in cg_weapons.c); they are not a look chosen here.
 */
void PANTHEON_MissileAdd(qhandle_t model, const vec3_t origin,
                         const vec3_t angles)
{
    refEntity_t ent;

    if (!model) return;

    memset(&ent, 0, sizeof(ent));
    ent.reType = RT_MODEL;
    ent.hModel = model;
    ent.renderfx = RF_NOSHADOW;
    VectorCopy(origin, ent.origin);
    VectorCopy(origin, ent.oldorigin);
    VectorCopy(origin, ent.lightingOrigin);
    AnglesToAxis(angles, ent.axis);
    ent.shaderRGBA[0] = ent.shaderRGBA[1] =
    ent.shaderRGBA[2] = ent.shaderRGBA[3] = 255;
    pa_re->AddRefEntityToScene(&ent);

    pa_re->AddLightToScene(origin, 200, 1.0f, 0.75f, 0.0f);
}
