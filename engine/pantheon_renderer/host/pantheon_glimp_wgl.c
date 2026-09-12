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

/* GL enums used below, by their spec values. */
#ifndef GL_MAX_RENDERBUFFER_SIZE_EXT
#define GL_MAX_RENDERBUFFER_SIZE_EXT 0x84E8
#endif

/*
 * THE WINDOW IS A DEVICE CONTEXT, NOT A PICTURE.
 *
 * WGL cannot create a context without a window, so one is created -- tiny,
 * undecorated, never shown. It is NOT where frames are drawn.
 *
 * Until 2026-09-12 it was. The window was created at the render size, and
 * the renderer drew into its default framebuffer. The GL rule that decides
 * what such a framebuffer holds is pixel ownership: pixels the window does
 * not own on the desktop -- behind its title bar, off the edge of the
 * screen, past the monitor -- are UNDEFINED. That one rule produced both
 * the long-standing "corner artefact" (an undrawn margin reading back as
 * texture memory) and the supersampling failure (a 5120x2880 request clipped
 * to the 3004x1421 the desktop could hold). A headless engine whose output
 * size is capped by the monitor was never headless.
 *
 * Frames now go to a framebuffer object sized from glConfig. An FBO has no
 * owner on any desktop, so every pixel in it is defined, at any size the GPU
 * accepts. The window stays PANTHEON_DC_WINDOW square forever.
 */
#define PANTHEON_DC_WINDOW 64

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
                             WS_POPUP,              /* never shown */
                             0, 0, PANTHEON_DC_WINDOW, PANTHEON_DC_WINDOW,
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

    /* THE SIZE COMES FROM r_mode, AS IT DOES IN EVERY OTHER PLATFORM LAYER.
     *
     * sdl_glimp.c:323 fills glConfig.vidWidth/vidHeight from R_GetModeInfo,
     * which for r_mode -1 reads r_customwidth/r_customheight. This file never
     * made that call, so glConfig stayed zero and the fallback below made
     * EVERY PANTHEON render 1280x720, whatever the shot asked for -- measured:
     * a 5120x2880 shot wrote 1280x720 files, and the host downgraded it with
     * one warning line. The fallback now only fires if the mode itself is
     * invalid, and says so. */
    if (!R_GetModeInfo(&glConfig.vidWidth, &glConfig.vidHeight,
                       &glConfig.windowAspect, r_mode->integer) ||
        glConfig.vidWidth <= 0 || glConfig.vidHeight <= 0)
        ri.Error(ERR_FATAL, "PANTHEON: r_mode %d gives no usable size "
                 "(r_customwidth/r_customheight unset?)", r_mode->integer);
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

    /* The swap-time blit draws the scene into the DC window at this size.
     * It is a 64x64 picture nobody reads; the frame is read from the FBO. */
    glConfig.visibleWindowWidth = PANTHEON_DC_WINDOW;
    glConfig.visibleWindowHeight = PANTHEON_DC_WINDOW;

    /* SAY WE HAVE A FRAMEBUFFER OBJECT, BECAUSE WE DO.
     *
     * InitFrameBufferAndRenderBuffer returns on its first line unless
     * glConfig.fbo is set, and in the shipped client only sdl_glimp.c ever
     * sets it. This file never did -- so the FBO code in tr_init.c had never
     * once run inside PANTHEON, whatever r_useFbo said. Detected the same way
     * sdl_glimp.c does it: the extension is advertised AND every entry point
     * PANTHEON_BindGL was asked for came back. */
    glConfig.fbo = strstr(glConfig.extensions_string,
                          "GL_EXT_framebuffer_object") &&
                   qglGenFramebuffersEXT && qglBindFramebufferEXT &&
                   qglFramebufferTexture2DEXT && qglCheckFramebufferStatusEXT &&
                   qglGenRenderbuffersEXT && qglBindRenderbufferEXT &&
                   qglFramebufferRenderbufferEXT && qglRenderbufferStorageEXT;
    glConfig.fboStencil = glConfig.fbo &&
        strstr(glConfig.extensions_string, "GL_EXT_packed_depth_stencil") != NULL;
    glConfig.fboMultiSample = qfalse;   /* r_fboAntiAlias is 0; sampling is ours */

    if (!glConfig.fbo)
        ri.Error(ERR_FATAL, "PANTHEON: the GL driver offers no usable "
                 "GL_EXT_framebuffer_object; refusing to fall back to drawing "
                 "into a window, whose pixels the desktop can take away");
    {
        GLint maxRb = 0, maxTex = 0;
        glGetIntegerv(GL_MAX_RENDERBUFFER_SIZE_EXT, &maxRb);
        glGetIntegerv(GL_MAX_TEXTURE_SIZE, &maxTex);
        if ((maxRb && (glConfig.vidWidth > maxRb || glConfig.vidHeight > maxRb)) ||
            (maxTex && (glConfig.vidWidth > maxTex || glConfig.vidHeight > maxTex)))
            ri.Error(ERR_FATAL, "PANTHEON: %dx%d exceeds this GPU's framebuffer "
                     "limit (renderbuffer %d, texture %d)", glConfig.vidWidth,
                     glConfig.vidHeight, maxRb, maxTex);
        ri.Printf(PRINT_ALL, "PANTHEON: offscreen target %dx%d "
                  "(GPU limit renderbuffer %d, texture %d)%s\n",
                  glConfig.vidWidth, glConfig.vidHeight, maxRb, maxTex,
                  glConfig.fboStencil ? ", packed depth-stencil" : "");
    }
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
