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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_public.h"
#include "pantheon_actor.h"

void PANTHEON_SetInstallPath(const char *p);
refexport_t *GetRefAPI(int apiVersion, refimport_t *rimp);
void CON_Init(void);
extern CRITICAL_SECTION printCriticalSection;

#define PA_MAX_PLAYERS 8
#define PA_MAX_FRAMES  4096
#define PA_MAX_ACTORS  8

#define PA_MAX_MODELS  16
#define PA_MAX_MISSILES 8
/* Authored world geometry placed in the scene: a PANTHEON door leaf,
 * a plinth, a banner. Same transform as a missile and deliberately a
 * SEPARATE keyword -- a door is not a projectile, and a grammar that
 * blurs the two would put set dressing into the projectile track. */
#define PA_MAX_PROPS 32

typedef struct {
    int      player;                 /* index into the declared players */
    vec3_t   origin;
    vec3_t   angles;
    int      legs, torso;
    int      legs_ms, torso_ms;      /* independent per-part animation clocks */
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
    int           numProps;
    shotMissile_t props[PA_MAX_PROPS];
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

/* ── TGA out ────────────────────────────────────────────────────────────── */
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
static void ParseShot(const char *path)
{
    FILE *f = fopen(path, "r");
    char line[1024];
    shotFrame_t *cur = NULL;
    int lineno = 0;

    if (!f) Com_Error(ERR_FATAL, "PANTHEON: cannot open shot script %s", path);

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
                Com_Error(ERR_FATAL, "PANTHEON: too many players in shot");
            if (sscanf(line, "%*s %63s %63s",
                       s_shot.playerModel[i], s_shot.playerSkin[i]) != 2)
                Com_Error(ERR_FATAL, "PANTHEON: bad player line %d", lineno);
            s_shot.numPlayers++;
        } else if (!strcmp(kw, "model")) {
            int i = s_shot.numModels;
            if (i >= PA_MAX_MODELS)
                Com_Error(ERR_FATAL, "PANTHEON: too many models in shot");
            if (sscanf(line, "%*s %63s", s_shot.modelPath[i]) != 1)
                Com_Error(ERR_FATAL, "PANTHEON: bad model line %d", lineno);
            s_shot.numModels++;
        } else if (!strcmp(kw, "frame")) {
            if (s_shot.numFrames >= PA_MAX_FRAMES)
                Com_Error(ERR_FATAL, "PANTHEON: too many frames in shot");
            cur = &s_shot.frames[s_shot.numFrames++];
            memset(cur, 0, sizeof(*cur));
            if (sscanf(line, "%*s %d %d %f %f %f %f %f %f %f %255s",
                       &cur->index, &cur->server_time_ms,
                       &cur->cam_origin[0], &cur->cam_origin[1],
                       &cur->cam_origin[2],
                       &cur->cam_angles[0], &cur->cam_angles[1],
                       &cur->cam_angles[2], &cur->fov, cur->out) != 10)
                Com_Error(ERR_FATAL, "PANTHEON: bad frame line %d", lineno);
        } else if (!strcmp(kw, "actor")) {
            shotActor_t *a;
            if (!cur) Com_Error(ERR_FATAL,
                                "PANTHEON: actor before frame, line %d", lineno);
            if (cur->numActors >= PA_MAX_ACTORS)
                Com_Error(ERR_FATAL, "PANTHEON: too many actors, line %d", lineno);
            a = &cur->actors[cur->numActors];
            if (sscanf(line,
                       "%*s %d %f %f %f %d %d %d %d "
                       "%f %f %f %f %f %f %f %f %f %d",
                       &a->player, &a->origin[0], &a->origin[1], &a->origin[2],
                       &a->legs, &a->torso, &a->legs_ms, &a->torso_ms,
                       &a->legsAngles[0], &a->legsAngles[1], &a->legsAngles[2],
                       &a->torsoAngles[0], &a->torsoAngles[1], &a->torsoAngles[2],
                       &a->headAngles[0], &a->headAngles[1], &a->headAngles[2],
                       &a->weaponModel) != 18)
                Com_Error(ERR_FATAL, "PANTHEON: bad actor line %d", lineno);
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
                Com_Error(ERR_FATAL, "PANTHEON: too many missiles, line %d",
                          lineno);
            m = &cur->missiles[cur->numMissiles];
            if (sscanf(line, "%*s %d %f %f %f %f %f %f",
                       &m->model, &m->origin[0], &m->origin[1], &m->origin[2],
                       &m->angles[0], &m->angles[1], &m->angles[2]) != 7)
                Com_Error(ERR_FATAL, "PANTHEON: bad projectile line %d", lineno);
            if (m->model < 0 || m->model >= s_shot.numModels)
                Com_Error(ERR_FATAL,
                          "PANTHEON: projectile names undeclared model %d, "
                          "line %d", m->model, lineno);
            cur->numMissiles++;
        } else if (!strcmp(kw, "prop")) {
            shotMissile_t *m;
            if (!cur) Com_Error(ERR_FATAL,
                                "PANTHEON: prop before frame, line %d", lineno);
            if (cur->numProps >= PA_MAX_PROPS)
                Com_Error(ERR_FATAL, "PANTHEON: too many props, line %d", lineno);
            m = &cur->props[cur->numProps];
            if (sscanf(line, "%*s %d %f %f %f %f %f %f",
                       &m->model, &m->origin[0], &m->origin[1], &m->origin[2],
                       &m->angles[0], &m->angles[1], &m->angles[2]) != 7)
                Com_Error(ERR_FATAL, "PANTHEON: bad prop line %d", lineno);
            if (m->model < 0 || m->model >= s_shot.numModels)
                Com_Error(ERR_FATAL,
                          "PANTHEON: prop names undeclared model %d, line %d",
                          m->model, lineno);
            cur->numProps++;
        } else {
            Com_Error(ERR_FATAL, "PANTHEON: unknown shot keyword '%s' line %d",
                      kw, lineno);
        }
    }
    fclose(f);

    if (!s_shot.map[0])   Com_Error(ERR_FATAL, "PANTHEON: shot has no map");
    if (!s_shot.numFrames) Com_Error(ERR_FATAL, "PANTHEON: shot has no frames");
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

int main(int argc, char **argv)
{
    refimport_t ri;
    refexport_t *re;
    refdef_t rd;
    byte *pixels;
    int i, fi;
    char cmdline[1024];
    const char *shotPath = NULL;

    /* single-frame mode inputs */
    char  cliMap[MAX_QPATH] = {0};
    char  cliOut[MAX_OSPATH] = "pantheon_frame.tga";
    char  cliModel[MAX_QPATH] = {0}, cliSkin[MAX_QPATH] = "default";
    vec3_t cliOrigin = {0, 0, 0}, cliAngles = {0, 0, 0};
    vec3_t cliActorOrigin = {0, 0, 0}, cliActorAngles = {0, 0, 0};
    int   cliLegs = 0, cliTorso = 0, cliW = 1280, cliH = 720;
    float cliFov = 90.0f;
    qboolean cliActor = qfalse;

    cmdline[0] = '\0';
    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--shot") && i + 1 < argc)
            shotPath = argv[++i];
        else if (!strcmp(argv[i], "--map") && i + 1 < argc)
            Q_strncpyz(cliMap, argv[++i], sizeof(cliMap));
        else if (!strcmp(argv[i], "--origin") && i + 3 < argc) {
            cliOrigin[0] = (float)atof(argv[++i]);
            cliOrigin[1] = (float)atof(argv[++i]);
            cliOrigin[2] = (float)atof(argv[++i]);
        } else if (!strcmp(argv[i], "--angles") && i + 3 < argc) {
            cliAngles[0] = (float)atof(argv[++i]);
            cliAngles[1] = (float)atof(argv[++i]);
            cliAngles[2] = (float)atof(argv[++i]);
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
        } else if (!strcmp(argv[i], "--fov") && i + 1 < argc)
            cliFov = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--width") && i + 1 < argc)
            cliW = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--height") && i + 1 < argc)
            cliH = atoi(argv[++i]);
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
        if (!cliMap[0]) {
            fprintf(stderr, "PANTHEON: --map or --shot is required; the "
                            "renderer does not choose a world\n");
            return 2;
        }
        Q_strcat(cmdline, sizeof(cmdline),
                 va("+set r_customwidth %d +set r_customheight %d ", cliW, cliH));
    }
    Q_strcat(cmdline, sizeof(cmdline),
             "+set r_mode -1 +set r_fullscreen 0 +set r_fboAntiAlias 0 ");

    Com_Init(cmdline);

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
        glconfig_t cfg;
        memset(&cfg, 0, sizeof(cfg));
        re->BeginRegistration(&cfg);
    }

    /* Models and skins must register BEFORE EndRegistration closes the pass,
     * or a handle comes back 0 and the actor silently is not drawn. */
    re->LoadWorld(va("maps/%s.bsp",
                     shotPath ? s_shot.map : cliMap));

    if (shotPath) {
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
    re->EndRegistration();

    pixels = malloc((size_t)(shotPath ? s_shot.width : cliW) *
                    (size_t)(shotPath ? s_shot.height : cliH) * 3);

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

        re->BeginFrame(STEREO_CENTER, qfalse);
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
                                  sf->actors[a].legs, sf->actors[a].torso,
                                  sf->actors[a].legs_ms, sf->actors[a].torso_ms,
                                  wm >= 0 ? s_shot.modelHandle[wm] : 0);
            }
            for (a = 0; a < sf->numMissiles; a++)
                PANTHEON_MissileAdd(s_shot.modelHandle[sf->missiles[a].model],
                                    sf->missiles[a].origin,
                                    sf->missiles[a].angles);
            for (a = 0; a < sf->numProps; a++)
                PANTHEON_MissileAdd(s_shot.modelHandle[sf->props[a].model],
                                    sf->props[a].origin,
                                    sf->props[a].angles);
        } else if (cliActor) {
            {
                vec3_t zero = {0, 0, 0};
                PANTHEON_ActorAdd(&s_players[0], cliActorOrigin,
                                  cliActorAngles, zero, zero,
                                  cliLegs, cliTorso, 0, 0, 0);
            }
        }

        re->RenderScene(&rd);
        re->EndFrame(NULL, NULL);

        glReadBuffer(GL_BACK);
        glPixelStorei(GL_PACK_ALIGNMENT, 1);
        glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, pixels);
        WriteTGA(out, pixels, w, h);

        if (shotPath && (fi % 10 == 0 || fi == s_shot.numFrames - 1))
            Com_Printf("PANTHEON: frame %d/%d t=%d -> %s\n",
                       fi + 1, s_shot.numFrames, time_ms, out);
    }

    free(pixels);
    if (shotPath)
        Com_Printf("PANTHEON: wrote %d frames (%dx%d) map=%s provenance=%s\n",
                   s_shot.numFrames, s_shot.width, s_shot.height,
                   s_shot.map, s_shot.provenance);
    else
        Com_Printf("PANTHEON: wrote %s (%dx%d) map=%s\n",
                   cliOut, cliW, cliH, cliMap);

    re->Shutdown(qtrue);
    return 0;
}
