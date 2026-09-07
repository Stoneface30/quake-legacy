/*
 * Application-side ABI audit for the glColor4f blocker.
 *
 * The point of this program is to try to blame OURSELVES. Before a driver is
 * accused, the caller has to be cleared:
 *
 *   - is the stack balanced across the call (stdcall cleanup correct)?
 *   - does the call even return, or does it fault inside?
 *   - is a guarded buffer around our locals intact afterwards?
 *   - does the paired control (glClearColor, same 4 floats, same @16
 *     decoration) behave differently through the identical code path?
 *
 * argv[1] = color4f | clearcolor | normal3f | none
 */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>

static LRESULT CALLBACK WP(HWND h, UINT m, WPARAM w, LPARAM l)
{
    return DefWindowProcA(h, m, w, l);
}

/* The stack-pointer read is a GCC/x86 check. MSVC has no inline asm on x64,
 * and the stdcall cleanup question it answers does not exist there anyway:
 * x64 Windows has one calling convention and the caller always cleans up. */
#if defined(__GNUC__) && defined(__i386__)
static unsigned read_esp(void)
{
    unsigned esp;
    __asm__ __volatile__("movl %%esp, %0" : "=r"(esp));
    return esp;
}
#else
static unsigned read_esp(void) { return 0; }
#endif

int main(int argc, char **argv)
{
    const char *which = (argc > 1) ? argv[1] : "color4f";
    WNDCLASSA wc; PIXELFORMATDESCRIPTOR pfd;
    HWND hwnd; HDC hdc; HGLRC rc; int fmt;
    unsigned before, after;
    volatile unsigned char guard_lo[32], guard_hi[32];
    int i, corrupt = 0;

    memset((void *)guard_lo, 0xAB, sizeof(guard_lo));
    memset((void *)guard_hi, 0xCD, sizeof(guard_hi));

    memset(&wc, 0, sizeof(wc));
    wc.lpfnWndProc = WP; wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "glabi"; RegisterClassA(&wc);
    hwnd = CreateWindowExA(0, "glabi", "glabi", WS_OVERLAPPEDWINDOW,
                           0, 0, 320, 240, NULL, NULL, wc.hInstance, NULL);
    hdc = GetDC(hwnd);
    memset(&pfd, 0, sizeof(pfd));
    pfd.nSize = sizeof(pfd); pfd.nVersion = 1;
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
    pfd.iPixelType = PFD_TYPE_RGBA; pfd.cColorBits = 24;
    pfd.cDepthBits = 24; pfd.cStencilBits = 8;
    fmt = ChoosePixelFormat(hdc, &pfd);
    if (!fmt || !SetPixelFormat(hdc, fmt, &pfd)) { printf("no pixel format\n"); return 2; }
    rc = wglCreateContext(hdc);
    if (!rc || !wglMakeCurrent(hdc, rc)) { printf("no context\n"); return 2; }

    printf("%-11s pointer width %d, GL %s\n", which,
           (int)(sizeof(void *) * 8), (const char *)glGetString(GL_VERSION));
    fflush(stdout);

    before = read_esp();
    printf("%-11s esp before 0x%08x -> calling\n", which, before);
    fflush(stdout);

    if      (!strcmp(which, "color4f"))    glColor4f(1.0f, 1.0f, 1.0f, 1.0f);
    else if (!strcmp(which, "clearcolor")) glClearColor(1.0f, 1.0f, 1.0f, 1.0f);
    else if (!strcmp(which, "normal3f"))   glNormal3f(0.0f, 0.0f, 1.0f);
    else if (!strcmp(which, "none"))       { }
    else { printf("unknown\n"); return 3; }

    after = read_esp();
    printf("%-11s RETURNED, esp after 0x%08x (delta %d)\n",
           which, after, (int)(after - before));
    fflush(stdout);

    for (i = 0; i < (int)sizeof(guard_lo); i++) if (guard_lo[i] != 0xAB) corrupt++;
    for (i = 0; i < (int)sizeof(guard_hi); i++) if (guard_hi[i] != 0xCD) corrupt++;
    printf("%-11s guard bytes corrupt: %d\n", which, corrupt);
    fflush(stdout);

    glFinish();
    printf("%-11s SURVIVED sync (err=0x%x)\n", which, (unsigned)glGetError());
    fflush(stdout);
    return 0;
}
