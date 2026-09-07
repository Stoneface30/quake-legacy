/*
 * Smallest honest reproduction of the PANTHEON first-frame blocker.
 *
 * No Quake, no renderer, no PANTHEON: a hidden window, a plain WGL context,
 * and five GL 1.1 calls. If this dies, the fault is the driver plus this kind
 * of context, and no amount of porting work moves it.
 */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>

static LRESULT CALLBACK WP(HWND h, UINT m, WPARAM w, LPARAM l)
{
    return DefWindowProcA(h, m, w, l);
}

#define STEP(label, call) \
    do { printf("  %-28s ", label); fflush(stdout); \
         call; \
         printf("returned (err=0x%x)\n", (unsigned)glGetError()); fflush(stdout); \
    } while (0)

int main(void)
{
    WNDCLASSA wc;
    PIXELFORMATDESCRIPTOR pfd;
    HWND hwnd; HDC hdc; HGLRC rc;
    int fmt; GLuint t = 0;

    printf("build: %d-bit\n", (int)(sizeof(void *) * 8));

    memset(&wc, 0, sizeof(wc));
    wc.lpfnWndProc = WP;
    wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "glmin";
    RegisterClassA(&wc);
    hwnd = CreateWindowExA(0, "glmin", "glmin", WS_OVERLAPPEDWINDOW,
                           0, 0, 640, 480, NULL, NULL, wc.hInstance, NULL);
    hdc = GetDC(hwnd);

    memset(&pfd, 0, sizeof(pfd));
    pfd.nSize = sizeof(pfd); pfd.nVersion = 1;
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
    pfd.iPixelType = PFD_TYPE_RGBA;
    pfd.cColorBits = 24; pfd.cDepthBits = 24; pfd.cStencilBits = 8;
    fmt = ChoosePixelFormat(hdc, &pfd);
    if (!fmt || !SetPixelFormat(hdc, fmt, &pfd)) { printf("no pixel format\n"); return 2; }
    rc = wglCreateContext(hdc);
    if (!rc || !wglMakeCurrent(hdc, rc)) { printf("no context\n"); return 2; }

    printf("GL_VENDOR   : %s\n", (const char *)glGetString(GL_VENDOR));
    printf("GL_RENDERER : %s\n", (const char *)glGetString(GL_RENDERER));
    printf("GL_VERSION  : %s\n", (const char *)glGetString(GL_VERSION));

    STEP("glGenTextures (before)", glGenTextures(1, &t));
    STEP("glClearDepth",           glClearDepth(1.0));
    STEP("glCullFace",             glCullFace(GL_FRONT));
    STEP("glColor4f",              glColor4f(1, 1, 1, 1));
    STEP("glGenTextures (after)",  glGenTextures(1, &t));

    printf("SURVIVED\n");
    wglMakeCurrent(NULL, NULL);
    wglDeleteContext(rc);
    return 0;
}
