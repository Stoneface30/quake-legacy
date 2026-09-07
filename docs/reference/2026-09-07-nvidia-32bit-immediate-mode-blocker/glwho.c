/*
 * Which OpenGL is actually answering, and does it survive the failing calls?
 *
 * The trap this exists to avoid: an application-local Mesa that fails to load,
 * Windows silently resolving opengl32.dll from System32 instead, and the run
 * being reported as "Mesa works". So this prints the FULL PATH of the loaded
 * opengl32 and libgallium_wgl modules before it prints anything else.
 *
 * It also reports the capabilities the Q3/QL renderer actually needs, because
 * "software GL survives glColor4f" and "software GL can run this renderer" are
 * different claims -- Microsoft's generic 1.1 rasteriser satisfies the first
 * and not the second.
 */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <string.h>

static LRESULT CALLBACK WP(HWND h, UINT m, WPARAM w, LPARAM l)
{
    return DefWindowProcA(h, m, w, l);
}

static void show_module(const char *name)
{
    char path[MAX_PATH];
    HMODULE m = GetModuleHandleA(name);
    if (!m) { printf("  %-22s NOT LOADED\n", name); return; }
    if (GetModuleFileNameA(m, path, sizeof(path)))
        printf("  %-22s %s\n", name, path);
    else
        printf("  %-22s (path unavailable)\n", name);
}

static void has_ext(const char *exts, const char *e)
{
    printf("  %-34s %s\n", e, (exts && strstr(exts, e)) ? "yes" : "NO");
}

int main(void)
{
    WNDCLASSA wc; PIXELFORMATDESCRIPTOR pfd;
    HWND hwnd; HDC hdc; HGLRC rc; int fmt;
    const char *exts;
    GLuint t = 0;
    GLint units = 0, texsize = 0;

    memset(&wc, 0, sizeof(wc));
    wc.lpfnWndProc = WP; wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "glwho"; RegisterClassA(&wc);
    hwnd = CreateWindowExA(0, "glwho", "glwho", WS_OVERLAPPEDWINDOW,
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

    printf("LOADED MODULES\n");
    show_module("opengl32.dll");
    show_module("libgallium_wgl.dll");
    show_module("nvoglv32.dll");
    show_module("nvoglv64.dll");

    printf("\nIMPLEMENTATION (%d-bit process)\n", (int)(sizeof(void *) * 8));
    printf("  GL_VENDOR              %s\n", (const char *)glGetString(GL_VENDOR));
    printf("  GL_RENDERER            %s\n", (const char *)glGetString(GL_RENDERER));
    printf("  GL_VERSION             %s\n", (const char *)glGetString(GL_VERSION));

    exts = (const char *)glGetString(GL_EXTENSIONS);
    glGetIntegerv(GL_MAX_TEXTURE_SIZE, &texsize);
    printf("  GL_MAX_TEXTURE_SIZE    %d\n", (int)texsize);

    printf("\nCAPABILITIES THE Q3/QL RENDERER USES\n");
    has_ext(exts, "GL_ARB_multitexture");
    has_ext(exts, "GL_EXT_texture_env_add");
    has_ext(exts, "GL_ARB_texture_compression");
    has_ext(exts, "GL_EXT_texture_filter_anisotropic");
    has_ext(exts, "GL_EXT_compiled_vertex_array");
    has_ext(exts, "GL_EXT_framebuffer_object");
    has_ext(exts, "GL_ARB_shader_objects");
    has_ext(exts, "GL_ARB_texture_rectangle");
    if (exts && strstr(exts, "GL_ARB_multitexture")) {
        glGetIntegerv(0x84E2 /* GL_MAX_TEXTURE_UNITS_ARB */, &units);
        printf("  %-34s %d\n", "GL_MAX_TEXTURE_UNITS_ARB", (int)units);
    }

    printf("\nTHE FAILING CALLS\n");
    printf("  glColor4f ... "); fflush(stdout);
    glColor4f(1, 1, 1, 1);
    glGenTextures(1, &t); glFinish();
    printf("survived\n"); fflush(stdout);

    printf("  glNormal3f ... "); fflush(stdout);
    glNormal3f(0, 0, 1);
    glGenTextures(1, &t); glFinish();
    printf("survived (err=0x%x)\n", (unsigned)glGetError()); fflush(stdout);

    printf("\nRESULT: this implementation runs the calls that block PANTHEON.\n");
    return 0;
}
