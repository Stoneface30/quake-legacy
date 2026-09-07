/*
 * Same probe, but on a NON-ACCELERATED pixel format.
 *
 * Windows ships its own software OpenGL 1.1 implementation inside
 * opengl32.dll. Selecting a generic (unaccelerated) pixel format takes the
 * NVIDIA ICD out of the picture entirely, with no download, no DLL beside the
 * executable and no change to any system setting.
 *
 * This is a diagnostic, not a renderer: GL 1.1 generic is not enough to draw a
 * Quake frame. What it answers is narrow and worth knowing -- whether
 * glColor4f is broken *in this driver*, or broken on this machine generally.
 *
 * argv[1] = the call to test, same names as glchar.c
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
    const char *c = (argc > 1) ? argv[1] : "color4f";
    WNDCLASSA wc; PIXELFORMATDESCRIPTOR pfd;
    HWND hwnd; HDC hdc; HGLRC rc;
    int i, n, chosen = 0; GLuint t = 0;

    memset(&wc, 0, sizeof(wc));
    wc.lpfnWndProc = WP; wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "glsw"; RegisterClassA(&wc);
    hwnd = CreateWindowExA(0, "glsw", "glsw", WS_OVERLAPPEDWINDOW,
                           0, 0, 320, 240, NULL, NULL, wc.hInstance, NULL);
    hdc = GetDC(hwnd);

    /* Walk every pixel format and take the first GENERIC (software) one:
     * PFD_GENERIC_FORMAT set and PFD_GENERIC_ACCELERATED clear means the
     * Microsoft rasteriser, not the vendor ICD. */
    n = DescribePixelFormat(hdc, 1, sizeof(pfd), NULL);
    for (i = 1; i <= n; i++) {
        memset(&pfd, 0, sizeof(pfd));
        if (!DescribePixelFormat(hdc, i, sizeof(pfd), &pfd)) continue;
        if (!(pfd.dwFlags & PFD_SUPPORT_OPENGL)) continue;
        if (!(pfd.dwFlags & PFD_DRAW_TO_WINDOW)) continue;
        if (!(pfd.dwFlags & PFD_GENERIC_FORMAT)) continue;
        if (pfd.dwFlags & PFD_GENERIC_ACCELERATED) continue;
        if (pfd.iPixelType != PFD_TYPE_RGBA) continue;
        chosen = i;
        break;
    }
    if (!chosen) { printf("%-12s NO GENERIC FORMAT AVAILABLE\n", c); return 2; }

    DescribePixelFormat(hdc, chosen, sizeof(pfd), &pfd);
    if (!SetPixelFormat(hdc, chosen, &pfd)) { printf("SetPixelFormat failed\n"); return 2; }
    rc = wglCreateContext(hdc);
    if (!rc || !wglMakeCurrent(hdc, rc)) { printf("no context\n"); return 2; }

    printf("  format #%d  %s | %s\n", chosen,
           (const char *)glGetString(GL_VENDOR),
           (const char *)glGetString(GL_VERSION));
    fflush(stdout);

    if      (!strcmp(c, "none"))       { }
    else if (!strcmp(c, "color4f"))    glColor4f(1, 1, 1, 1);
    else if (!strcmp(c, "color3f"))    glColor3f(1, 1, 1);
    else if (!strcmp(c, "normal3f"))   glNormal3f(0, 0, 1);
    else if (!strcmp(c, "clearcolor")) glClearColor(0, 0, 0, 1);
    else { printf("unknown\n"); return 3; }

    glGenTextures(1, &t);
    glFinish();
    printf("%-12s SURVIVED (err=0x%x)\n", c, (unsigned)glGetError());
    fflush(stdout);
    return 0;
}
