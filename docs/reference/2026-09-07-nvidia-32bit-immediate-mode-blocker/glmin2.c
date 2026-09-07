/*
 * Variant matrix for the 32-bit glColor4f blocker.
 *
 * argv[1] selects one variation of how the context is set up. The point is to
 * find a context this driver will accept fixed-function calls in, without
 * needing the user to change a driver-wide setting.
 *
 *   shown     - the window is visible (default is never shown)
 *   single    - no PFD_DOUBLEBUFFER
 *   nodepth   - no depth/stencil bits
 *   pump      - pump the message queue before the GL calls
 *   default   - same as the failing case, as a control
 */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>

static LRESULT CALLBACK WP(HWND h, UINT m, WPARAM w, LPARAM l)
{
    return DefWindowProcA(h, m, w, l);
}

int main(int argc, char **argv)
{
    const char *v = (argc > 1) ? argv[1] : "default";
    WNDCLASSA wc;
    PIXELFORMATDESCRIPTOR pfd;
    HWND hwnd; HDC hdc; HGLRC rc;
    int fmt; GLuint t = 0;
    MSG msg;

    printf("[%s] start\n", v); fflush(stdout);

    memset(&wc, 0, sizeof(wc));
    wc.lpfnWndProc = WP;
    wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "glmin2";
    RegisterClassA(&wc);
    hwnd = CreateWindowExA(0, "glmin2", "glmin2", WS_OVERLAPPEDWINDOW,
                           0, 0, 640, 480, NULL, NULL, wc.hInstance, NULL);
    if (!strcmp(v, "shown"))
        ShowWindow(hwnd, SW_SHOWNOACTIVATE);
    hdc = GetDC(hwnd);

    memset(&pfd, 0, sizeof(pfd));
    pfd.nSize = sizeof(pfd); pfd.nVersion = 1;
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL;
    if (strcmp(v, "single"))
        pfd.dwFlags |= PFD_DOUBLEBUFFER;
    pfd.iPixelType = PFD_TYPE_RGBA;
    pfd.cColorBits = 24;
    if (strcmp(v, "nodepth")) { pfd.cDepthBits = 24; pfd.cStencilBits = 8; }

    fmt = ChoosePixelFormat(hdc, &pfd);
    if (!fmt || !SetPixelFormat(hdc, fmt, &pfd)) { printf("[%s] no pixel format\n", v); return 2; }
    rc = wglCreateContext(hdc);
    if (!rc || !wglMakeCurrent(hdc, rc)) { printf("[%s] no context\n", v); return 2; }

    if (!strcmp(v, "pump"))
        while (PeekMessageA(&msg, NULL, 0, 0, PM_REMOVE)) { TranslateMessage(&msg); DispatchMessageA(&msg); }

    glGenTextures(1, &t);
    printf("[%s] pre-colour ok\n", v); fflush(stdout);
    glColor4f(1, 1, 1, 1);
    printf("[%s] glColor4f ok\n", v); fflush(stdout);
    glGenTextures(1, &t);
    glFinish();
    printf("[%s] SURVIVED (err=0x%x)\n", v, (unsigned)glGetError()); fflush(stdout);

    wglMakeCurrent(NULL, NULL);
    wglDeleteContext(rc);
    return 0;
}
