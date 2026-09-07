/*
 * PANTHEON native renderer host -- the platform services qcommon expects.
 *
 * Wolfcam's own sys_main.c supplies these, but it also owns `main()` and
 * builds a client around it. PANTHEON owns its entry point, so the eleven
 * services qcommon actually calls are implemented here and nothing else is
 * inherited.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"

void Sys_Print(const char *msg)
{
    fputs(msg, stdout);
    fflush(stdout);
}

/*
 * ERR_FATAL from inside the renderer means the frame cannot be produced.
 * PANTHEON exits non-zero rather than limping on: a host that continues after
 * a renderer error goes on to write an image that is wrong in a way nobody
 * can see.
 */
void QDECL Sys_Error(const char *error, ...)
{
    va_list argptr;
    char text[4096];

    va_start(argptr, error);
    Q_vsnprintf(text, sizeof(text), error, argptr);
    va_end(argptr);

    fprintf(stderr, "PANTHEON FATAL: %s\n", text);
    fflush(stderr);
    exit(1);
}

void Sys_Quit(void)
{
    exit(0);
}

void Sys_Init(void)
{
    Cvar_Set("arch", "win_mingw i686");
    Cvar_Set("username", "pantheon");
}

char *Sys_ConsoleInput(void)
{
    return NULL;              /* headless: there is no console to read */
}

/*
 * The data root. PANTHEON passes it explicitly rather than guessing from the
 * executable's location, because the renderer host is built in one place and
 * the game assets live in another -- the same code/data split that produced
 * an empty review database earlier today.
 */
static char s_installPath[MAX_OSPATH];

void PANTHEON_SetInstallPath(const char *p)
{
    Q_strncpyz(s_installPath, p, sizeof(s_installPath));
}

char *Sys_DefaultInstallPath(void)
{
    if (s_installPath[0])
        return s_installPath;
    return Sys_Cwd();
}

qboolean Sys_FileIsDirectory(const char *path)
{
    struct stat st;
    if (stat(path, &st) != 0)
        return qfalse;
    return (st.st_mode & S_IFDIR) ? qtrue : qfalse;
}

/*
 * NO GAME MODULES. cgame/ui are the client's business and the renderer never
 * loads one; refusing here keeps a stray VM load from quietly succeeding.
 */
void *Sys_LoadDll(const char *name, char *fqpath,
                  intptr_t (QDECL **entryPoint)(int, ...),
                  intptr_t (QDECL *systemcalls)(intptr_t, ...))
{
    (void)fqpath; (void)entryPoint; (void)systemcalls;
    Com_Printf("PANTHEON: refusing to load game module '%s' "
               "(the renderer host has no VM)\n", name);
    return NULL;
}

void Sys_UnloadDll(void *dllHandle)
{
    (void)dllHandle;
}

void Sys_SigHandler(int signal)
{
    fprintf(stderr, "PANTHEON: signal %d\n", signal);
    exit(1);
}

/* SSE is assumed: the build already requires -msse2 for tr_mme. */
unsigned int Sys_GetProcessorFeatures(void)
{
    return 0;
}
