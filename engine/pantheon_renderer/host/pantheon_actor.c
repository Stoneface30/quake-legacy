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
#define PA_TORSO_NEGATIVE 30
#define PA_LEGS_WALK     14
#define PA_LEGS_BACKCR   32
#define PA_LEGS_BACKWALK 33
#define PA_FLAG_RUN      34
#define PA_FLAG_STAND    35
#define PA_FLAG_STAND2RUN 36

static refexport_t *pa_re;

void PANTHEON_ActorInit(refexport_t *re) { pa_re = re; }

/*
 * animation.cfg, parsed the way cg_players.c::CG_ParseAnimationFile parses it.
 *
 * This is a transcription of that function, not a paraphrase of it. Three
 * things the earlier hand-rolled version dropped, each of which changes what
 * is drawn:
 *
 *   * the OPTIONAL PARAMETERS. fixedlegs and fixedtorso live here, in the
 *     model's own cfg -- they are not configstring fields -- and
 *     CG_PlayerAngles poses the body differently for a model that declares
 *     them.
 *   * initialLerp. CG_SetLerpFrameAnimation offsets animationTime by it, so
 *     where an animation starts depends on it.
 *   * the DERIVED entries. Backward crouch, backward walk and the three flag
 *     animations are not in the file; the engine builds them afterwards, and
 *     a table that stops at the file's 31 entries has them all zero.
 *
 * fps is parsed with atof, not atoi: a cfg declaring 22.5 fps rounds to a
 * different frameLerp under integer parsing.
 */
static qboolean PA_ParseAnimations(paPlayer_t *p)
{
    char path[MAX_QPATH];
    char *buf = NULL;
    char *text_p, *prev;
    const char *token;
    paAnim_t *animations = p->anims;
    float fps;
    int len, i, skip = 0;

    Com_sprintf(path, sizeof(path), "models/players/%s/animation.cfg", p->model);
    len = FS_ReadFile(path, (void **)&buf);
    if (len <= 0 || !buf) {
        Com_Printf("PANTHEON: no %s\n", path);
        return qfalse;
    }

    text_p = buf;

    p->footsteps = 0;                  /* FOOTSTEP_NORMAL */
    VectorClear(p->headOffset);
    p->gender = 0;                     /* GENDER_MALE */
    p->fixedlegs = qfalse;
    p->fixedtorso = qfalse;

    /* optional parameters */
    for (;;) {
        prev = text_p;                 /* so we can unget */
        token = COM_Parse(&text_p);
        if (!token || !token[0]) break;

        if (!Q_stricmp(token, "footsteps")) {
            token = COM_Parse(&text_p);
            if (!token || !token[0]) break;
            if (!Q_stricmp(token, "boot"))        p->footsteps = 1;
            else if (!Q_stricmp(token, "flesh"))  p->footsteps = 2;
            else if (!Q_stricmp(token, "mech"))   p->footsteps = 3;
            else if (!Q_stricmp(token, "energy")) p->footsteps = 4;
            else                                  p->footsteps = 0;
            continue;
        } else if (!Q_stricmp(token, "headoffset")) {
            for (i = 0; i < 3; i++) {
                token = COM_Parse(&text_p);
                if (!token || !token[0]) break;
                p->headOffset[i] = atof(token);
            }
            continue;
        } else if (!Q_stricmp(token, "sex")) {
            token = COM_Parse(&text_p);
            if (!token || !token[0]) break;
            if (token[0] == 'f' || token[0] == 'F')      p->gender = 1;
            else if (token[0] == 'n' || token[0] == 'N') p->gender = 2;
            else                                         p->gender = 0;
            continue;
        } else if (!Q_stricmp(token, "fixedlegs")) {
            p->fixedlegs = qtrue;
            continue;
        } else if (!Q_stricmp(token, "fixedtorso")) {
            p->fixedtorso = qtrue;
            continue;
        }

        if (token[0] >= '0' && token[0] <= '9') {
            text_p = prev;             /* unget: the animations start here */
            break;
        }
        Com_Printf("PANTHEON: unknown token '%s' in %s\n", token, path);
    }

    for (i = 0; i < PA_FILE_ANIMATIONS; i++) {
        token = COM_Parse(&text_p);
        if (!token || !token[0]) {
            /* A file that stops early still declares the gesture animations,
             * by copying the first one. */
            if (i >= PA_TORSO_GETFLAG && i <= PA_TORSO_NEGATIVE) {
                animations[i] = animations[PA_TORSO_GESTURE];
                animations[i].reversed = qfalse;
                animations[i].flipflop = qfalse;
                continue;
            }
            break;
        }
        animations[i].firstFrame = atoi(token);

        /* leg-only frames do not count the upper-body-only frames */
        if (i == PA_LEGS_WALKCR)
            skip = animations[PA_LEGS_WALKCR].firstFrame
                 - animations[PA_TORSO_GESTURE].firstFrame;
        if (i >= PA_LEGS_WALKCR && i < PA_TORSO_GETFLAG)
            animations[i].firstFrame -= skip;

        token = COM_Parse(&text_p);
        if (!token || !token[0]) break;
        animations[i].numFrames = atoi(token);
        animations[i].reversed = qfalse;
        animations[i].flipflop = qfalse;
        if (animations[i].numFrames < 0) {
            animations[i].numFrames = -animations[i].numFrames;
            animations[i].reversed = qtrue;
        }

        token = COM_Parse(&text_p);
        if (!token || !token[0]) break;
        animations[i].loopFrames = atoi(token);

        token = COM_Parse(&text_p);
        if (!token || !token[0]) break;
        fps = atof(token);
        if (fps == 0) fps = 1;
        animations[i].frameLerp   = 1000 / fps;
        animations[i].initialLerp = 1000 / fps;
    }

    FS_FreeFile(buf);

    if (i != PA_FILE_ANIMATIONS) {
        /* The shipped client refuses the whole file here rather than drawing
         * a half-parsed body. So does this. */
        Com_Printf("PANTHEON: error parsing %s (got %d of %d animations)\n",
                   path, i, PA_FILE_ANIMATIONS);
        p->haveAnims = qfalse;
        return qfalse;
    }

    /* the animations the file does not contain */
    animations[PA_LEGS_BACKCR] = animations[PA_LEGS_WALKCR];
    animations[PA_LEGS_BACKCR].reversed = qtrue;
    animations[PA_LEGS_BACKWALK] = animations[PA_LEGS_WALK];
    animations[PA_LEGS_BACKWALK].reversed = qtrue;

    animations[PA_FLAG_RUN].firstFrame  = 0;
    animations[PA_FLAG_RUN].numFrames   = 16;
    animations[PA_FLAG_RUN].loopFrames  = 16;
    animations[PA_FLAG_RUN].frameLerp   = 1000 / 15;
    animations[PA_FLAG_RUN].initialLerp = 1000 / 15;
    animations[PA_FLAG_RUN].reversed    = qfalse;

    animations[PA_FLAG_STAND].firstFrame  = 16;
    animations[PA_FLAG_STAND].numFrames   = 5;
    animations[PA_FLAG_STAND].loopFrames  = 0;
    animations[PA_FLAG_STAND].frameLerp   = 1000 / 20;
    animations[PA_FLAG_STAND].initialLerp = 1000 / 20;
    animations[PA_FLAG_STAND].reversed    = qfalse;

    animations[PA_FLAG_STAND2RUN].firstFrame  = 16;
    animations[PA_FLAG_STAND2RUN].numFrames   = 5;
    animations[PA_FLAG_STAND2RUN].loopFrames  = 1;
    animations[PA_FLAG_STAND2RUN].frameLerp   = 1000 / 15;
    animations[PA_FLAG_STAND2RUN].initialLerp = 1000 / 15;
    animations[PA_FLAG_STAND2RUN].reversed    = qtrue;

    p->haveAnims = qtrue;
    return qtrue;
}

/*
 * Hand the parsed table to PANTHEON. One line per animation plus the model's
 * own flags; PANTHEON keeps the animation clocks, because CG_RunLerpFrame is
 * stateful and the differential proof of it lives on that side.
 */
void PANTHEON_ActorDumpModel(const paPlayer_t *p)
{
    int i;
    printf("model %s\n", p->model);
    printf("fixedlegs %d\n", p->fixedlegs ? 1 : 0);
    printf("fixedtorso %d\n", p->fixedtorso ? 1 : 0);
    printf("headoffset %f %f %f\n", p->headOffset[0], p->headOffset[1],
           p->headOffset[2]);
    printf("footsteps %d\n", p->footsteps);
    printf("gender %d\n", p->gender);
    printf("animations %d\n", PA_MAX_ANIMATIONS);
    for (i = 0; i < PA_MAX_ANIMATIONS; i++)
        printf("anim %d %d %d %d %d %d %d %d\n", i,
               p->anims[i].firstFrame, p->anims[i].numFrames,
               p->anims[i].loopFrames, p->anims[i].frameLerp,
               p->anims[i].initialLerp, p->anims[i].reversed ? 1 : 0,
               p->anims[i].flipflop ? 1 : 0);
    fflush(stdout);
}

/*
 * Parse a model's animation.cfg without registering anything. Used by
 * --dump-model, which needs the filesystem but no renderer.
 */
qboolean PANTHEON_ActorLoadAnimations(paPlayer_t *p, const char *model)
{
    memset(p, 0, sizeof(*p));
    Q_strncpyz(p->model, model, sizeof(p->model));
    return PA_ParseAnimations(p);
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

/*
 * There is no animation maths here any more.
 *
 * The host used to compute frame/oldFrame/backlerp in closed form, from
 * `time since the animation started`. The source oracle (oracle_anim.exe,
 * running the engine's own CG_RunLerpFrame) proved that wrong: the engine
 * advances frameTime by exactly ONE frameLerp per RENDER CALL, from the
 * previous frameTime, and only then clamps up to the current time. That is
 * history-dependent -- an animation plays SLOWER under a coarse render
 * schedule rather than skipping frames -- and no function of time alone can
 * reproduce it.
 *
 * So PANTHEON keeps the lerp frames (engine/pantheon/render_frame.py, proved
 * against the same oracle) and hands the host the three numbers the renderer
 * actually consumes.
 */

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
 * The frame pair and backlerp arrive already evaluated. PANTHEON observed
 * when each animation changed and ran the engine's own lerp-frame rule over
 * its declared render schedule; the host chooses nothing about the pose.
 */
void PANTHEON_ActorAdd(const paPlayer_t *p, const vec3_t origin,
                       const vec3_t legsAngles, const vec3_t torsoAngles,
                       const vec3_t headAngles,
                       int legsFrame, int legsOldFrame, float legsBacklerp,
                       int torsoFrame, int torsoOldFrame, float torsoBacklerp,
                       qhandle_t weaponModel)
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
    legs.frame    = legsFrame;
    legs.oldframe = legsOldFrame;
    legs.backlerp = legsBacklerp;
    legs.shaderRGBA[0] = legs.shaderRGBA[1] =
    legs.shaderRGBA[2] = legs.shaderRGBA[3] = 255;
    pa_re->AddRefEntityToScene(&legs);

    torso.reType = RT_MODEL;
    torso.hModel = p->torso;
    torso.customSkin = p->skinTorso;
    VectorCopy(origin, torso.lightingOrigin);
    torso.frame    = torsoFrame;
    torso.oldframe = torsoOldFrame;
    torso.backlerp = torsoBacklerp;
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
