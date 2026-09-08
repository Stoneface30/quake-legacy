/*
 * Which GL calls does this driver actually refuse?
 *
 * One call per process, so a crash names exactly one culprit and cannot be
 * blamed on something queued earlier. Each run does: create context, make the
 * one call under test, then a synchronising call to force the driver's worker
 * thread to catch up. Survive = that call is safe.
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
    const char *c = (argc > 1) ? argv[1] : "none";
    WNDCLASSA wc; PIXELFORMATDESCRIPTOR pfd;
    HWND hwnd; HDC hdc; HGLRC rc; int fmt; GLuint t = 0;

    memset(&wc, 0, sizeof(wc));
    wc.lpfnWndProc = WP; wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "glchar"; RegisterClassA(&wc);
    hwnd = CreateWindowExA(0, "glchar", "glchar", WS_OVERLAPPEDWINDOW,
                           0, 0, 320, 240, NULL, NULL, wc.hInstance, NULL);
    hdc = GetDC(hwnd);
    memset(&pfd, 0, sizeof(pfd));
    pfd.nSize = sizeof(pfd); pfd.nVersion = 1;
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
    pfd.iPixelType = PFD_TYPE_RGBA; pfd.cColorBits = 24;
    pfd.cDepthBits = 24; pfd.cStencilBits = 8;
    fmt = ChoosePixelFormat(hdc, &pfd);
    if (!fmt || !SetPixelFormat(hdc, fmt, &pfd)) return 2;
    rc = wglCreateContext(hdc);
    if (!rc || !wglMakeCurrent(hdc, rc)) return 2;

    if      (!strcmp(c, "none"))        { }
    else if (!strcmp(c, "color4f"))     glColor4f(1, 1, 1, 1);
    else if (!strcmp(c, "color3f"))     glColor3f(1, 1, 1);
    else if (!strcmp(c, "color4ub"))    glColor4ub(255, 255, 255, 255);
    else if (!strcmp(c, "color4fv"))    { GLfloat v[4] = {1,1,1,1}; glColor4fv(v); }
    else if (!strcmp(c, "shademodel"))  glShadeModel(GL_SMOOTH);
    else if (!strcmp(c, "depthfunc"))   glDepthFunc(GL_LEQUAL);
    else if (!strcmp(c, "enabletex"))   glEnable(GL_TEXTURE_2D);
    else if (!strcmp(c, "matrixmode"))  { glMatrixMode(GL_MODELVIEW); glLoadIdentity(); }
    else if (!strcmp(c, "clientstate")) glEnableClientState(GL_VERTEX_ARRAY);
    else if (!strcmp(c, "texenv"))      glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    else if (!strcmp(c, "clearcolor"))  glClearColor(0, 0, 0, 1);
    else if (!strcmp(c, "normal3f"))    glNormal3f(0, 0, 1);
    else { printf("%-12s UNKNOWN\n", c); return 3; }

    glGenTextures(1, &t);
    glFinish();
    printf("%-12s SURVIVED (err=0x%x)\n", c, (unsigned)glGetError());
    fflush(stdout);
    return 0;
}
