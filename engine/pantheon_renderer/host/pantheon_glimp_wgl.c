/*
 * PANTHEON native renderer host -- the GL platform layer.
 *
 * WGL RATHER THAN SDL, on purpose. The renderer needs a GL context and a
 * handful of GLimp_* entry points; SDL supplies those in the shipped client,
 * but the shipped client is also where today's failure lives -- on the hidden
 * desktop SDL comes up on "windib" and the multisample framebuffer is refused
 * outright (0x8cdd, GL_FRAMEBUFFER_UNSUPPORTED). Owning the context is the
 * point of owning the renderer, so the first frame takes the shortest honest
 * path to one: a Win32 window that is never shown, and a plain WGL context.
 *
 * This file provides ONLY what the renderer imports. It does not create a
 * client, read input, play a demo or decide anything about game truth.
 */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>

#include "../wolfcamql-11.3-src/wolfcamql-src/code/renderer/tr_local.h"

/* glConfig, textureFilterAnisotropic, maxAnisotropy and displayAspect are
 * OWNED BY tr_init.c. The platform layer fills them in; it does not define
 * them, or the renderer ends up with two. */

static HWND s_hwnd;
static HDC s_hdc;
static HGLRC s_hglrc;

/* The renderer asks for extensions through qgl* pointers. wglGetProcAddress
 * returns them once a context is current; anything absent stays NULL and the
 * renderer's own capability checks decide what to do. */
void PANTHEON_BindGL(void);

void *PANTHEON_GetProcAddress(const char *name)
{
    void *p = (void *)wglGetProcAddress(name);
    if (p == NULL || p == (void *)0x1 || p == (void *)0x2 ||
        p == (void *)0x3 || p == (void *)-1) {
        HMODULE m = GetModuleHandleA("opengl32.dll");
        p = m ? (void *)GetProcAddress(m, name) : NULL;
    }
    return p;
}

static LRESULT CALLBACK PantheonWndProc(HWND h, UINT m, WPARAM w, LPARAM l)
{
    return DefWindowProcA(h, m, w, l);
}

/*
 * A window is created because WGL needs a device context, and it is never
 * shown. This is not the hidden-desktop trick: there is no second desktop and
 * no foreground change, because the window never becomes visible at all.
 */
void GLimp_Init(void)
{
    WNDCLASSA wc;
    PIXELFORMATDESCRIPTOR pfd;
    int fmt;
    const char *s;

    memset(&wc, 0, sizeof(wc));
    wc.lpfnWndProc = PantheonWndProc;
    wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "PantheonRenderHost";
    RegisterClassA(&wc);

    s_hwnd = CreateWindowExA(0, "PantheonRenderHost", "pantheon",
                             WS_OVERLAPPEDWINDOW,   /* never shown */
                             0, 0, glConfig.vidWidth ? glConfig.vidWidth : 1280,
                             glConfig.vidHeight ? glConfig.vidHeight : 720,
                             NULL, NULL, wc.hInstance, NULL);
    if (!s_hwnd)
        ri.Error(ERR_FATAL, "PANTHEON: CreateWindow failed (%lu)",
                 (unsigned long)GetLastError());

    s_hdc = GetDC(s_hwnd);
    memset(&pfd, 0, sizeof(pfd));
    pfd.nSize = sizeof(pfd);
    pfd.nVersion = 1;
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
    pfd.iPixelType = PFD_TYPE_RGBA;
    pfd.cColorBits = 24;
    pfd.cDepthBits = 24;
    pfd.cStencilBits = 8;

    fmt = ChoosePixelFormat(s_hdc, &pfd);
    if (!fmt || !SetPixelFormat(s_hdc, fmt, &pfd))
        ri.Error(ERR_FATAL, "PANTHEON: no usable pixel format");

    s_hglrc = wglCreateContext(s_hdc);
    if (!s_hglrc || !wglMakeCurrent(s_hdc, s_hglrc))
        ri.Error(ERR_FATAL, "PANTHEON: wglCreateContext/MakeCurrent failed");

    /* BIND THE EXTENSION POINTERS HERE, NOT LATER. The renderer starts using
     * them inside the very call that brought us here -- R_Init goes straight
     * on to InitFrameBufferAndRenderBuffer, which calls qglGenFramebuffersEXT.
     * Binding after BeginRegistration returns is binding after first use. */
    PANTHEON_BindGL();

    glConfig.vidWidth = glConfig.vidWidth ? glConfig.vidWidth : 1280;
    glConfig.vidHeight = glConfig.vidHeight ? glConfig.vidHeight : 720;
    glConfig.windowAspect = (float)glConfig.vidWidth / glConfig.vidHeight;
    glConfig.colorBits = 24;
    glConfig.depthBits = 24;
    glConfig.stencilBits = 8;
    glConfig.deviceSupportsGamma = qfalse;
    glConfig.isFullscreen = qfalse;
    glConfig.driverType = GLDRV_ICD;
    glConfig.hardwareType = GLHW_GENERIC;
    glConfig.textureCompression = TC_NONE;
    glConfig.textureEnvAddAvailable = qfalse;

    s = (const char *)glGetString(GL_RENDERER);
    Q_strncpyz(glConfig.renderer_string, s ? s : "unknown",
               sizeof(glConfig.renderer_string));
    s = (const char *)glGetString(GL_VENDOR);
    Q_strncpyz(glConfig.vendor_string, s ? s : "unknown",
               sizeof(glConfig.vendor_string));
    s = (const char *)glGetString(GL_VERSION);
    Q_strncpyz(glConfig.version_string, s ? s : "unknown",
               sizeof(glConfig.version_string));
    s = (const char *)glGetString(GL_EXTENSIONS);
    Q_strncpyz(glConfig.extensions_string, s ? s : "",
               sizeof(glConfig.extensions_string));

    ri.Printf(PRINT_ALL, "PANTHEON GL: %s | %s | %s\n",
              glConfig.vendor_string, glConfig.renderer_string,
              glConfig.version_string);
}

void GLimp_Shutdown(void)
{
    if (s_hglrc) { wglMakeCurrent(NULL, NULL); wglDeleteContext(s_hglrc); }
    if (s_hdc && s_hwnd) ReleaseDC(s_hwnd, s_hdc);
    if (s_hwnd) DestroyWindow(s_hwnd);
    s_hglrc = NULL; s_hdc = NULL; s_hwnd = NULL;
}

void GLimp_EndFrame(void)
{
    /* Nothing is presented: frames are read back, not shown. */
    glFinish();
}

void GLimp_SetGamma(unsigned char r[256], unsigned char g[256],
                    unsigned char b[256]) { (void)r; (void)g; (void)b; }
void GLimp_LogComment(char *c) { (void)c; }

/* Single threaded on purpose: a frame is rendered on demand, not pumped.
 * Refusing to spawn a render thread is a supported answer -- the renderer
 * falls back to running the backend on the calling thread. */
qboolean GLimp_SpawnRenderThread(void (*f)(void)) { (void)f; return qfalse; }
void GLimp_FrontEndSleep(void) {}
void GLimp_WakeRenderer(void *d) { (void)d; }
void *GLimp_RendererSleep(void) { return NULL; }
