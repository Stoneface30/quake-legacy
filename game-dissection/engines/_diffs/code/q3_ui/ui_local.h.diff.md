# Diff: `code/q3_ui/ui_local.h`
**Canonical:** `wolfcamql-src` (sha256 `7cb5303ed1e8...`, 23621 bytes)

## Variants

### `quake3-source`  — sha256 `5d6c521189c6...`, 22539 bytes

_Diff stat: +41 / -60 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_local.h	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_local.h	2026-04-16 20:02:19.946829300 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -23,15 +23,14 @@
 #ifndef __UI_LOCAL_H__
 #define __UI_LOCAL_H__
 
-#include "../qcommon/q_shared.h"
-#include "../renderercommon/tr_types.h"
-#include "../ui/ui_common.h"
+#include "../game/q_shared.h"
+#include "../cgame/tr_types.h"
 //NOTE: include the ui_public.h from the new UI
-#include "../ui/ui_public.h"
+#include "../ui/ui_public.h" // bk001205 - yes, do have to use this
 //redefine to old API version
 #undef UI_API_VERSION
 #define UI_API_VERSION	4
-#include "../client/keycodes.h"
+#include "keycodes.h"
 #include "../game/bg_public.h"
 
 typedef void (*voidfunc_f)(void);
@@ -93,12 +92,7 @@
 
 extern vmCvar_t	ui_cdkey;
 extern vmCvar_t	ui_cdkeychecked;
-extern vmCvar_t	ui_ioq3;
 
-extern vmCvar_t ui_doubleClickTime;
-
-extern vmCvar_t ui_demoSortDirFirst;
-extern vmCvar_t ui_demoStayInFolder;
 
 //
 // ui_qmenu.c
@@ -111,46 +105,46 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#define MAX_MENUITEMS			64
 
 #define MTYPE_NULL				0
-#define MTYPE_SLIDER			1
+#define MTYPE_SLIDER			1	
 #define MTYPE_ACTION			2
 #define MTYPE_SPINCONTROL		3
 #define MTYPE_FIELD				4
 #define MTYPE_RADIOBUTTON		5
-#define MTYPE_BITMAP			6
+#define MTYPE_BITMAP			6	
 #define MTYPE_TEXT				7
 #define MTYPE_SCROLLLIST		8
 #define MTYPE_PTEXT				9
 #define MTYPE_BTEXT				10
 
-#define QMF_BLINK				((unsigned int) 0x00000001)
-#define QMF_SMALLFONT			((unsigned int) 0x00000002)
-#define QMF_LEFT_JUSTIFY		((unsigned int) 0x00000004)
-#define QMF_CENTER_JUSTIFY		((unsigned int) 0x00000008)
-#define QMF_RIGHT_JUSTIFY		((unsigned int) 0x00000010)
-#define QMF_NUMBERSONLY			((unsigned int) 0x00000020)	// edit field is only numbers
-#define QMF_HIGHLIGHT			((unsigned int) 0x00000040)
-#define QMF_HIGHLIGHT_IF_FOCUS	((unsigned int) 0x00000080)	// steady focus
-#define QMF_PULSEIFFOCUS		((unsigned int) 0x00000100)	// pulse if focus
-#define QMF_HASMOUSEFOCUS		((unsigned int) 0x00000200)
-#define QMF_NOONOFFTEXT			((unsigned int) 0x00000400)
-#define QMF_MOUSEONLY			((unsigned int) 0x00000800)	// only mouse input allowed
-#define QMF_HIDDEN				((unsigned int) 0x00001000)	// skips drawing
-#define QMF_GRAYED				((unsigned int) 0x00002000)	// grays and disables
-#define QMF_INACTIVE			((unsigned int) 0x00004000)	// disables any input
-#define QMF_NODEFAULTINIT		((unsigned int) 0x00008000)	// skip default initialization
-#define QMF_OWNERDRAW			((unsigned int) 0x00010000)
-#define QMF_PULSE				((unsigned int) 0x00020000)
-#define QMF_LOWERCASE			((unsigned int) 0x00040000)	// edit field is all lower case
-#define QMF_UPPERCASE			((unsigned int) 0x00080000)	// edit field is all upper case
-#define QMF_SILENT				((unsigned int) 0x00100000)
+#define QMF_BLINK				0x00000001
+#define QMF_SMALLFONT			0x00000002
+#define QMF_LEFT_JUSTIFY		0x00000004
+#define QMF_CENTER_JUSTIFY		0x00000008
+#define QMF_RIGHT_JUSTIFY		0x00000010
+#define QMF_NUMBERSONLY			0x00000020	// edit field is only numbers
+#define QMF_HIGHLIGHT			0x00000040
+#define QMF_HIGHLIGHT_IF_FOCUS	0x00000080	// steady focus
+#define QMF_PULSEIFFOCUS		0x00000100	// pulse if focus
+#define QMF_HASMOUSEFOCUS		0x00000200
+#define QMF_NOONOFFTEXT			0x00000400
+#define QMF_MOUSEONLY			0x00000800	// only mouse input allowed
+#define QMF_HIDDEN				0x00001000	// skips drawing
+#define QMF_GRAYED				0x00002000	// grays and disables
+#define QMF_INACTIVE			0x00004000	// disables any input
+#define QMF_NODEFAULTINIT		0x00008000	// skip default initialization
+#define QMF_OWNERDRAW			0x00010000
+#define QMF_PULSE				0x00020000
+#define QMF_LOWERCASE			0x00040000	// edit field is all lower case
+#define QMF_UPPERCASE			0x00080000	// edit field is all upper case
+#define QMF_SILENT				0x00100000
 
 // callback notifications
 #define QM_GOTFOCUS				1
 #define QM_LOSTFOCUS			2
 #define QM_ACTIVATED			3
-#define QM_DOUBLECLICKED 4
 
 typedef struct _tag_menuframework
 {
@@ -180,7 +174,7 @@
 	int	bottom;
 	menuframework_s *parent;
 	int menuPosition;
-	unsigned int flags;
+	unsigned flags;
 
 	void (*callback)( void *self, int event );
 	void (*statusbar)( void *self );
@@ -201,7 +195,7 @@
 	mfield_t		field;
 } menufield_s;
 
-typedef struct
+typedef struct 
 {
 	menucommon_s generic;
 
@@ -220,13 +214,13 @@
 	int curvalue;
 	int	numitems;
 	int	top;
-
+		
 	const char **itemnames;
 
 	int width;
 	int height;
 	int	columns;
-	int	separation;
+	int	seperation;
 } menulist_s;
 
 typedef struct
@@ -243,7 +237,7 @@
 typedef struct
 {
 	menucommon_s	generic;
-	char*			focuspic;
+	char*			focuspic;	
 	char*			errorpic;
 	qhandle_t		shader;
 	qhandle_t		focusshader;
@@ -297,7 +291,7 @@
 extern vec4_t		name_color;
 extern vec4_t		list_color;
 extern vec4_t		listbar_color;
-extern vec4_t		text_color_disabled;
+extern vec4_t		text_color_disabled; 
 extern vec4_t		text_color_normal;
 extern vec4_t		text_color_highlight;
 
@@ -323,7 +317,6 @@
 extern void UI_MainMenu(void);
 extern void UI_RegisterCvars( void );
 extern void UI_UpdateCvars( void );
-extern void ScrollList_Init( menulist_s *l );
 
 //
 // ui_credits.c
@@ -370,7 +363,7 @@
 //
 // ui_demo2.c
 //
-extern void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir);
+extern void UI_DemosMenu( void );
 extern void Demos_Cache( void );
 
 //
@@ -492,18 +485,12 @@
 
 	animation_t		animations[MAX_ANIMATIONS];
 
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
-
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
 	qhandle_t		flashModel;
 	vec3_t			flashDlightColor;
 	int				muzzleFlashTime;
 
-	vec3_t color1;
-	byte c1RGBA[4];
-
 	// currently in use drawing parms
 	vec3_t			viewAngles;
 	vec3_t			moveAngles;
@@ -560,23 +547,21 @@
 	qhandle_t			cursor;
 	qhandle_t			rb_on;
 	qhandle_t			rb_off;
-	float				xscale;
-	float				yscale;
+	float				scale;
 	float				bias;
 	qboolean			demoversion;
 	qboolean			firstdraw;
-	qboolean showErrorMenu;
 } uiStatic_t;
 
 extern void			UI_Init( void );
 extern void			UI_Shutdown( void );
 extern void			UI_KeyEvent( int key, int down );
-extern void			UI_MouseEvent( int dx, int dy, qboolean active );
+extern void			UI_MouseEvent( int dx, int dy );
 extern void			UI_Refresh( int realtime );
 extern qboolean		UI_ConsoleCommand( int realTime );
 extern float		UI_ClampCvar( float min, float max, float value );
 extern void			UI_DrawNamedPic( float x, float y, float width, float height, const char *picname );
-extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader );
+extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader ); 
 extern void			UI_FillRect( float x, float y, float width, float height, const float *color );
 extern void			UI_DrawRect( float x, float y, float width, float height, const float *color );
 extern void			UI_UpdateScreen( void );
@@ -633,7 +618,7 @@
 // ui_syscalls.c
 //
 void			trap_Print( const char *string );
-void			trap_Error( const char *string ) Q_NO_RETURN;
+void			trap_Error( const char *string );
 int				trap_Milliseconds( void );
 void			trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags );
 void			trap_Cvar_Update( vmCvar_t *vmCvar );
@@ -692,13 +677,9 @@
 void			trap_GetCDKey( char *buf, int buflen );
 void			trap_SetCDKey( char *buf );
 
-qboolean               trap_VerifyCDKey( const char *key, const char *chksum);
+qboolean               trap_VerifyCDKey( const char *key, const char *chksum); // bk001208 - RC4
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
-void trap_R_BeginHud (void);
 
 //
 // ui_addbots.c

```

### `ioquake3`  — sha256 `3d0c91ac8664...`, 23123 bytes

_Diff stat: +14 / -25 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_local.h	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_local.h	2026-04-16 20:02:21.554426200 +0100
@@ -25,7 +25,6 @@
 
 #include "../qcommon/q_shared.h"
 #include "../renderercommon/tr_types.h"
-#include "../ui/ui_common.h"
 //NOTE: include the ui_public.h from the new UI
 #include "../ui/ui_public.h"
 //redefine to old API version
@@ -95,10 +94,6 @@
 extern vmCvar_t	ui_cdkeychecked;
 extern vmCvar_t	ui_ioq3;
 
-extern vmCvar_t ui_doubleClickTime;
-
-extern vmCvar_t ui_demoSortDirFirst;
-extern vmCvar_t ui_demoStayInFolder;
 
 //
 // ui_qmenu.c
@@ -111,14 +106,15 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#define MAX_MENUITEMS			64
 
 #define MTYPE_NULL				0
-#define MTYPE_SLIDER			1
+#define MTYPE_SLIDER			1	
 #define MTYPE_ACTION			2
 #define MTYPE_SPINCONTROL		3
 #define MTYPE_FIELD				4
 #define MTYPE_RADIOBUTTON		5
-#define MTYPE_BITMAP			6
+#define MTYPE_BITMAP			6	
 #define MTYPE_TEXT				7
 #define MTYPE_SCROLLLIST		8
 #define MTYPE_PTEXT				9
@@ -150,7 +146,6 @@
 #define QM_GOTFOCUS				1
 #define QM_LOSTFOCUS			2
 #define QM_ACTIVATED			3
-#define QM_DOUBLECLICKED 4
 
 typedef struct _tag_menuframework
 {
@@ -201,7 +196,7 @@
 	mfield_t		field;
 } menufield_s;
 
-typedef struct
+typedef struct 
 {
 	menucommon_s generic;
 
@@ -220,7 +215,7 @@
 	int curvalue;
 	int	numitems;
 	int	top;
-
+		
 	const char **itemnames;
 
 	int width;
@@ -243,7 +238,7 @@
 typedef struct
 {
 	menucommon_s	generic;
-	char*			focuspic;
+	char*			focuspic;	
 	char*			errorpic;
 	qhandle_t		shader;
 	qhandle_t		focusshader;
@@ -297,7 +292,7 @@
 extern vec4_t		name_color;
 extern vec4_t		list_color;
 extern vec4_t		listbar_color;
-extern vec4_t		text_color_disabled;
+extern vec4_t		text_color_disabled; 
 extern vec4_t		text_color_normal;
 extern vec4_t		text_color_highlight;
 
@@ -323,7 +318,6 @@
 extern void UI_MainMenu(void);
 extern void UI_RegisterCvars( void );
 extern void UI_UpdateCvars( void );
-extern void ScrollList_Init( menulist_s *l );
 
 //
 // ui_credits.c
@@ -370,7 +364,7 @@
 //
 // ui_demo2.c
 //
-extern void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir);
+extern void UI_DemosMenu( void );
 extern void Demos_Cache( void );
 
 //
@@ -492,8 +486,8 @@
 
 	animation_t		animations[MAX_ANIMATIONS];
 
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
+	qboolean		fixedlegs;		// true if legs yaw is always the same as torso yaw
+	qboolean		fixedtorso;		// true if torso never changes yaw
 
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
@@ -501,8 +495,8 @@
 	vec3_t			flashDlightColor;
 	int				muzzleFlashTime;
 
-	vec3_t color1;
-	byte c1RGBA[4];
+	vec3_t			color1;
+	byte			c1RGBA[4];
 
 	// currently in use drawing parms
 	vec3_t			viewAngles;
@@ -565,18 +559,17 @@
 	float				bias;
 	qboolean			demoversion;
 	qboolean			firstdraw;
-	qboolean showErrorMenu;
 } uiStatic_t;
 
 extern void			UI_Init( void );
 extern void			UI_Shutdown( void );
 extern void			UI_KeyEvent( int key, int down );
-extern void			UI_MouseEvent( int dx, int dy, qboolean active );
+extern void			UI_MouseEvent( int dx, int dy );
 extern void			UI_Refresh( int realtime );
 extern qboolean		UI_ConsoleCommand( int realTime );
 extern float		UI_ClampCvar( float min, float max, float value );
 extern void			UI_DrawNamedPic( float x, float y, float width, float height, const char *picname );
-extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader );
+extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader ); 
 extern void			UI_FillRect( float x, float y, float width, float height, const float *color );
 extern void			UI_DrawRect( float x, float y, float width, float height, const float *color );
 extern void			UI_UpdateScreen( void );
@@ -695,10 +688,6 @@
 qboolean               trap_VerifyCDKey( const char *key, const char *chksum);
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
-void trap_R_BeginHud (void);
 
 //
 // ui_addbots.c

```

### `openarena-engine`  — sha256 `41745a17398b...`, 22999 bytes

_Diff stat: +14 / -28 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_local.h	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_local.h	2026-04-16 22:48:25.895195900 +0100
@@ -25,7 +25,6 @@
 
 #include "../qcommon/q_shared.h"
 #include "../renderercommon/tr_types.h"
-#include "../ui/ui_common.h"
 //NOTE: include the ui_public.h from the new UI
 #include "../ui/ui_public.h"
 //redefine to old API version
@@ -95,10 +94,6 @@
 extern vmCvar_t	ui_cdkeychecked;
 extern vmCvar_t	ui_ioq3;
 
-extern vmCvar_t ui_doubleClickTime;
-
-extern vmCvar_t ui_demoSortDirFirst;
-extern vmCvar_t ui_demoStayInFolder;
 
 //
 // ui_qmenu.c
@@ -111,14 +106,15 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#define MAX_MENUITEMS			64
 
 #define MTYPE_NULL				0
-#define MTYPE_SLIDER			1
+#define MTYPE_SLIDER			1	
 #define MTYPE_ACTION			2
 #define MTYPE_SPINCONTROL		3
 #define MTYPE_FIELD				4
 #define MTYPE_RADIOBUTTON		5
-#define MTYPE_BITMAP			6
+#define MTYPE_BITMAP			6	
 #define MTYPE_TEXT				7
 #define MTYPE_SCROLLLIST		8
 #define MTYPE_PTEXT				9
@@ -150,7 +146,6 @@
 #define QM_GOTFOCUS				1
 #define QM_LOSTFOCUS			2
 #define QM_ACTIVATED			3
-#define QM_DOUBLECLICKED 4
 
 typedef struct _tag_menuframework
 {
@@ -201,7 +196,7 @@
 	mfield_t		field;
 } menufield_s;
 
-typedef struct
+typedef struct 
 {
 	menucommon_s generic;
 
@@ -220,13 +215,13 @@
 	int curvalue;
 	int	numitems;
 	int	top;
-
+		
 	const char **itemnames;
 
 	int width;
 	int height;
 	int	columns;
-	int	separation;
+	int	seperation;
 } menulist_s;
 
 typedef struct
@@ -243,7 +238,7 @@
 typedef struct
 {
 	menucommon_s	generic;
-	char*			focuspic;
+	char*			focuspic;	
 	char*			errorpic;
 	qhandle_t		shader;
 	qhandle_t		focusshader;
@@ -297,7 +292,7 @@
 extern vec4_t		name_color;
 extern vec4_t		list_color;
 extern vec4_t		listbar_color;
-extern vec4_t		text_color_disabled;
+extern vec4_t		text_color_disabled; 
 extern vec4_t		text_color_normal;
 extern vec4_t		text_color_highlight;
 
@@ -323,7 +318,6 @@
 extern void UI_MainMenu(void);
 extern void UI_RegisterCvars( void );
 extern void UI_UpdateCvars( void );
-extern void ScrollList_Init( menulist_s *l );
 
 //
 // ui_credits.c
@@ -370,7 +364,7 @@
 //
 // ui_demo2.c
 //
-extern void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir);
+extern void UI_DemosMenu( void );
 extern void Demos_Cache( void );
 
 //
@@ -492,17 +486,14 @@
 
 	animation_t		animations[MAX_ANIMATIONS];
 
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
-
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
 	qhandle_t		flashModel;
 	vec3_t			flashDlightColor;
 	int				muzzleFlashTime;
 
-	vec3_t color1;
-	byte c1RGBA[4];
+	vec3_t			color1;
+	byte			c1RGBA[4];
 
 	// currently in use drawing parms
 	vec3_t			viewAngles;
@@ -565,18 +556,17 @@
 	float				bias;
 	qboolean			demoversion;
 	qboolean			firstdraw;
-	qboolean showErrorMenu;
 } uiStatic_t;
 
 extern void			UI_Init( void );
 extern void			UI_Shutdown( void );
 extern void			UI_KeyEvent( int key, int down );
-extern void			UI_MouseEvent( int dx, int dy, qboolean active );
+extern void			UI_MouseEvent( int dx, int dy );
 extern void			UI_Refresh( int realtime );
 extern qboolean		UI_ConsoleCommand( int realTime );
 extern float		UI_ClampCvar( float min, float max, float value );
 extern void			UI_DrawNamedPic( float x, float y, float width, float height, const char *picname );
-extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader );
+extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader ); 
 extern void			UI_FillRect( float x, float y, float width, float height, const float *color );
 extern void			UI_DrawRect( float x, float y, float width, float height, const float *color );
 extern void			UI_UpdateScreen( void );
@@ -633,7 +623,7 @@
 // ui_syscalls.c
 //
 void			trap_Print( const char *string );
-void			trap_Error( const char *string ) Q_NO_RETURN;
+void			trap_Error( const char *string ) __attribute__((noreturn));
 int				trap_Milliseconds( void );
 void			trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags );
 void			trap_Cvar_Update( vmCvar_t *vmCvar );
@@ -695,10 +685,6 @@
 qboolean               trap_VerifyCDKey( const char *key, const char *chksum);
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
-void trap_R_BeginHud (void);
 
 //
 // ui_addbots.c

```

### `openarena-gamecode`  — sha256 `2116a34eec16...`, 25512 bytes

_Diff stat: +194 / -113 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_local.h	2026-04-16 20:02:25.207499600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_local.h	2026-04-16 22:48:24.182499300 +0100
@@ -23,82 +23,96 @@
 #ifndef __UI_LOCAL_H__
 #define __UI_LOCAL_H__
 
+#define BASEOA
+
 #include "../qcommon/q_shared.h"
-#include "../renderercommon/tr_types.h"
-#include "../ui/ui_common.h"
+#include "../renderer/tr_types.h"
 //NOTE: include the ui_public.h from the new UI
-#include "../ui/ui_public.h"
+#include "../ui/ui_public.h" // bk001205 - yes, do have to use this
 //redefine to old API version
 #undef UI_API_VERSION
 #define UI_API_VERSION	4
 #include "../client/keycodes.h"
 #include "../game/bg_public.h"
+#include "../ui/ui_shared.h"
 
 typedef void (*voidfunc_f)(void);
 
-extern vmCvar_t	ui_ffa_fraglimit;
-extern vmCvar_t	ui_ffa_timelimit;
-
-extern vmCvar_t	ui_tourney_fraglimit;
-extern vmCvar_t	ui_tourney_timelimit;
-
-extern vmCvar_t	ui_team_fraglimit;
-extern vmCvar_t	ui_team_timelimit;
-extern vmCvar_t	ui_team_friendly;
-
-extern vmCvar_t	ui_ctf_capturelimit;
-extern vmCvar_t	ui_ctf_timelimit;
-extern vmCvar_t	ui_ctf_friendly;
-
-extern vmCvar_t	ui_arenasFile;
-extern vmCvar_t	ui_botsFile;
-extern vmCvar_t	ui_spScores1;
-extern vmCvar_t	ui_spScores2;
-extern vmCvar_t	ui_spScores3;
-extern vmCvar_t	ui_spScores4;
-extern vmCvar_t	ui_spScores5;
-extern vmCvar_t	ui_spAwards;
-extern vmCvar_t	ui_spVideos;
-extern vmCvar_t	ui_spSkill;
-
-extern vmCvar_t	ui_spSelection;
-
-extern vmCvar_t	ui_browserMaster;
-extern vmCvar_t	ui_browserGameType;
-extern vmCvar_t	ui_browserSortKey;
-extern vmCvar_t	ui_browserShowFull;
-extern vmCvar_t	ui_browserShowEmpty;
-
-extern vmCvar_t	ui_brassTime;
-extern vmCvar_t	ui_drawCrosshair;
-extern vmCvar_t	ui_drawCrosshairNames;
-extern vmCvar_t	ui_marks;
-
-extern vmCvar_t	ui_server1;
-extern vmCvar_t	ui_server2;
-extern vmCvar_t	ui_server3;
-extern vmCvar_t	ui_server4;
-extern vmCvar_t	ui_server5;
-extern vmCvar_t	ui_server6;
-extern vmCvar_t	ui_server7;
-extern vmCvar_t	ui_server8;
-extern vmCvar_t	ui_server9;
-extern vmCvar_t	ui_server10;
-extern vmCvar_t	ui_server11;
-extern vmCvar_t	ui_server12;
-extern vmCvar_t	ui_server13;
-extern vmCvar_t	ui_server14;
-extern vmCvar_t	ui_server15;
-extern vmCvar_t	ui_server16;
-
-extern vmCvar_t	ui_cdkey;
-extern vmCvar_t	ui_cdkeychecked;
-extern vmCvar_t	ui_ioq3;
-
-extern vmCvar_t ui_doubleClickTime;
-
-extern vmCvar_t ui_demoSortDirFirst;
-extern vmCvar_t ui_demoStayInFolder;
+extern vmCvar_t ui_ffa_fraglimit;
+extern vmCvar_t ui_ffa_timelimit;
+extern vmCvar_t ui_tourney_fraglimit;
+extern vmCvar_t ui_tourney_timelimit;
+extern vmCvar_t ui_team_fraglimit;
+extern vmCvar_t ui_team_timelimit;
+extern vmCvar_t ui_team_friendly;
+extern vmCvar_t ui_ctf_capturelimit;
+extern vmCvar_t ui_ctf_timelimit;
+extern vmCvar_t ui_ctf_friendly;
+extern vmCvar_t ui_1fctf_capturelimit;
+extern vmCvar_t ui_1fctf_timelimit;
+extern vmCvar_t ui_1fctf_friendly;
+extern vmCvar_t ui_overload_capturelimit;
+extern vmCvar_t ui_overload_timelimit;
+extern vmCvar_t ui_overload_friendly;
+extern vmCvar_t ui_harvester_capturelimit;
+extern vmCvar_t ui_harvester_timelimit;
+extern vmCvar_t ui_harvester_friendly;
+extern vmCvar_t ui_elimination_capturelimit;
+extern vmCvar_t ui_elimination_timelimit;
+extern vmCvar_t ui_ctf_elimination_capturelimit;
+extern vmCvar_t ui_ctf_elimination_timelimit;
+extern vmCvar_t ui_lms_fraglimit;
+extern vmCvar_t ui_lms_timelimit;
+extern vmCvar_t ui_dd_capturelimit;
+extern vmCvar_t ui_dd_timelimit;
+extern vmCvar_t ui_dd_friendly;
+extern vmCvar_t ui_dom_capturelimit;
+extern vmCvar_t ui_dom_timelimit;
+extern vmCvar_t ui_dom_friendly;
+extern vmCvar_t ui_pos_scorelimit;
+extern vmCvar_t ui_pos_timelimit;
+extern vmCvar_t ui_arenasFile;
+extern vmCvar_t ui_botsFile;
+extern vmCvar_t ui_spScores1;
+extern vmCvar_t ui_spScores2;
+extern vmCvar_t ui_spScores3;
+extern vmCvar_t ui_spScores4;
+extern vmCvar_t ui_spScores5;
+extern vmCvar_t ui_spAwards;
+extern vmCvar_t ui_spVideos;
+extern vmCvar_t ui_spSkill;
+extern vmCvar_t ui_spSelection;
+extern vmCvar_t ui_browserMaster;
+extern vmCvar_t ui_browserGameType;
+extern vmCvar_t ui_browserSortKey;
+extern vmCvar_t ui_browserShowFull;
+extern vmCvar_t ui_browserShowEmpty;
+extern vmCvar_t ui_brassTime;
+extern vmCvar_t ui_drawCrosshair;
+extern vmCvar_t ui_drawCrosshairNames;
+extern vmCvar_t ui_marks;
+extern vmCvar_t ui_server1;
+extern vmCvar_t ui_server2;
+extern vmCvar_t ui_server3;
+extern vmCvar_t ui_server4;
+extern vmCvar_t ui_server5;
+extern vmCvar_t ui_server6;
+extern vmCvar_t ui_server7;
+extern vmCvar_t ui_server8;
+extern vmCvar_t ui_server9;
+extern vmCvar_t ui_server10;
+extern vmCvar_t ui_server11;
+extern vmCvar_t ui_server12;
+extern vmCvar_t ui_server13;
+extern vmCvar_t ui_server14;
+extern vmCvar_t ui_server15;
+extern vmCvar_t ui_server16;
+//extern vmCvar_t ui_cdkey;
+//extern vmCvar_t ui_cdkeychecked;
+extern vmCvar_t ui_setupchecked;
+//new in beta 23:
+extern vmCvar_t ui_browserOnlyHumans;
+extern vmCvar_t ui_browserHidePrivate;
 
 //
 // ui_qmenu.c
@@ -111,46 +125,50 @@
 #define	MAX_EDIT_LINE			256
 
 #define MAX_MENUDEPTH			8
+#ifndef MAX_MENUITEMS
+#define MAX_MENUITEMS			64
+#endif
 
 #define MTYPE_NULL				0
-#define MTYPE_SLIDER			1
+#define MTYPE_SLIDER			1	
 #define MTYPE_ACTION			2
 #define MTYPE_SPINCONTROL		3
 #define MTYPE_FIELD				4
 #define MTYPE_RADIOBUTTON		5
-#define MTYPE_BITMAP			6
+#define MTYPE_BITMAP			6	
 #define MTYPE_TEXT				7
 #define MTYPE_SCROLLLIST		8
 #define MTYPE_PTEXT				9
 #define MTYPE_BTEXT				10
 
-#define QMF_BLINK				((unsigned int) 0x00000001)
-#define QMF_SMALLFONT			((unsigned int) 0x00000002)
-#define QMF_LEFT_JUSTIFY		((unsigned int) 0x00000004)
-#define QMF_CENTER_JUSTIFY		((unsigned int) 0x00000008)
-#define QMF_RIGHT_JUSTIFY		((unsigned int) 0x00000010)
-#define QMF_NUMBERSONLY			((unsigned int) 0x00000020)	// edit field is only numbers
-#define QMF_HIGHLIGHT			((unsigned int) 0x00000040)
-#define QMF_HIGHLIGHT_IF_FOCUS	((unsigned int) 0x00000080)	// steady focus
-#define QMF_PULSEIFFOCUS		((unsigned int) 0x00000100)	// pulse if focus
-#define QMF_HASMOUSEFOCUS		((unsigned int) 0x00000200)
-#define QMF_NOONOFFTEXT			((unsigned int) 0x00000400)
-#define QMF_MOUSEONLY			((unsigned int) 0x00000800)	// only mouse input allowed
-#define QMF_HIDDEN				((unsigned int) 0x00001000)	// skips drawing
-#define QMF_GRAYED				((unsigned int) 0x00002000)	// grays and disables
-#define QMF_INACTIVE			((unsigned int) 0x00004000)	// disables any input
-#define QMF_NODEFAULTINIT		((unsigned int) 0x00008000)	// skip default initialization
-#define QMF_OWNERDRAW			((unsigned int) 0x00010000)
-#define QMF_PULSE				((unsigned int) 0x00020000)
-#define QMF_LOWERCASE			((unsigned int) 0x00040000)	// edit field is all lower case
-#define QMF_UPPERCASE			((unsigned int) 0x00080000)	// edit field is all upper case
-#define QMF_SILENT				((unsigned int) 0x00100000)
+#define QMF_BLINK				(unsigned int)0x00000001
+#define QMF_SMALLFONT			(unsigned int)0x00000002
+#define QMF_LEFT_JUSTIFY		(unsigned int)0x00000004
+#define QMF_CENTER_JUSTIFY		(unsigned int)0x00000008
+#define QMF_RIGHT_JUSTIFY		(unsigned int)0x00000010
+#define QMF_NUMBERSONLY			(unsigned int)0x00000020	// edit field is only numbers
+#define QMF_HIGHLIGHT			(unsigned int)0x00000040
+#define QMF_HIGHLIGHT_IF_FOCUS	(unsigned int)0x00000080	// steady focus
+#define QMF_PULSEIFFOCUS		(unsigned int)0x00000100	// pulse if focus
+#define QMF_HASMOUSEFOCUS		(unsigned int)0x00000200
+#define QMF_NOONOFFTEXT			(unsigned int)0x00000400
+#define QMF_MOUSEONLY			(unsigned int)0x00000800	// only mouse input allowed
+#define QMF_HIDDEN				(unsigned int)0x00001000	// skips drawing
+#define QMF_GRAYED				(unsigned int)0x00002000	// grays and disables
+#define QMF_INACTIVE			(unsigned int)0x00004000	// disables any input
+#define QMF_NODEFAULTINIT		(unsigned int)0x00008000	// skip default initialization
+#define QMF_OWNERDRAW			(unsigned int)0x00010000
+#define QMF_PULSE				(unsigned int)0x00020000
+#define QMF_LOWERCASE			(unsigned int)0x00040000	// edit field is all lower case
+#define QMF_UPPERCASE			(unsigned int)0x00080000	// edit field is all upper case
+#define QMF_SILENT				(unsigned int)0x00100000
 
 // callback notifications
 #define QM_GOTFOCUS				1
 #define QM_LOSTFOCUS			2
 #define QM_ACTIVATED			3
-#define QM_DOUBLECLICKED 4
+
+#define MENU_ART_DIR "art_blueish"
 
 typedef struct _tag_menuframework
 {
@@ -180,7 +198,7 @@
 	int	bottom;
 	menuframework_s *parent;
 	int menuPosition;
-	unsigned int flags;
+	unsigned flags;
 
 	void (*callback)( void *self, int event );
 	void (*statusbar)( void *self );
@@ -201,7 +219,7 @@
 	mfield_t		field;
 } menufield_s;
 
-typedef struct
+typedef struct 
 {
 	menucommon_s generic;
 
@@ -220,13 +238,13 @@
 	int curvalue;
 	int	numitems;
 	int	top;
-
+		
 	const char **itemnames;
 
 	int width;
 	int height;
 	int	columns;
-	int	separation;
+	int	seperation;
 } menulist_s;
 
 typedef struct
@@ -243,7 +261,7 @@
 typedef struct
 {
 	menucommon_s	generic;
-	char*			focuspic;
+	char*			focuspic;	
 	char*			errorpic;
 	qhandle_t		shader;
 	qhandle_t		focusshader;
@@ -260,6 +278,22 @@
 	float*			color;
 } menutext_s;
 
+#define MAX_MAPNAME_LENGTH 32
+
+typedef struct {
+	int pagenumber;
+	char mapname[10][MAX_MAPNAME_LENGTH];
+} t_mappage;
+
+#define MAX_NAMELENGTH_INFO 20
+
+typedef struct {
+	char mapname[MAX_NAMELENGTH_INFO];
+	mapinfo_result_t mapinfo;
+} t_mapinfo;
+
+extern t_mappage mappage;
+
 extern void			Menu_Cache( void );
 extern void			Menu_Focus( menucommon_s *m );
 extern void			Menu_AddItem( menuframework_s *menu, void *item );
@@ -297,7 +331,7 @@
 extern vec4_t		name_color;
 extern vec4_t		list_color;
 extern vec4_t		listbar_color;
-extern vec4_t		text_color_disabled;
+extern vec4_t		text_color_disabled; 
 extern vec4_t		text_color_normal;
 extern vec4_t		text_color_highlight;
 
@@ -305,6 +339,8 @@
 extern char	*ui_medalPicNames[];
 extern char	*ui_medalSounds[];
 
+extern t_mapinfo*	GetMapInfoUI( void );
+
 //
 // ui_mfield.c
 //
@@ -323,7 +359,7 @@
 extern void UI_MainMenu(void);
 extern void UI_RegisterCvars( void );
 extern void UI_UpdateCvars( void );
-extern void ScrollList_Init( menulist_s *l );
+extern void UI_SetDefaultCvar(const char* cvar, const char* value);
 
 //
 // ui_credits.c
@@ -370,10 +406,15 @@
 //
 // ui_demo2.c
 //
-extern void UI_DemosMenu (qboolean useQuakeLiveDir, const char *lastdemodir);
+extern void UI_DemosMenu( void );
 extern void Demos_Cache( void );
 
 //
+// ui_challenges.c
+//
+extern void UI_Challenges( void );
+
+//
 // ui_cinematics.c
 //
 extern void UI_CinematicsMenu( void );
@@ -439,6 +480,7 @@
 extern void ServerOptions_Cache( void );
 extern void UI_BotSelectMenu( char *bot );
 extern void UI_BotSelectMenu_Cache( void );
+extern void WriteMapList(void) ;
 
 //
 // ui_serverinfo.c
@@ -454,6 +496,54 @@
 extern void DriverInfo_Cache( void );
 
 //
+// ui_votemenu.c
+//
+extern void UI_VoteMenuMenu( void );
+
+//
+// ui_votemenu_fraglimit.c
+//
+extern void UI_VoteFraglimitMenu( void );
+
+//
+// ui_votemenu_timelimit.c
+//
+extern void UI_VoteTimelimitMenu( void );
+
+//
+// ui_votemenu_gametype.c
+//
+extern void UI_VoteGametypeMenu( void );
+
+//
+// ui_votemenu_kick.c
+//
+extern void UI_VoteKickMenu( void );
+
+//
+// ui_votemenu_map.c
+//
+extern void UI_VoteMapMenu( void );
+extern void UI_VoteMapMenuInternal( void );
+
+//
+// ui_password.c
+//
+extern void SpecifyPassword_Cache( void );
+extern void UI_SpecifyPasswordMenu( const char* string, const char *name );
+
+//
+// ui_firstconnect.c
+//
+extern void FirstConnect_Cache( void );
+extern void UI_FirstConnectMenu( void );
+
+//
+// ui_votemenu_custom.c
+
+extern void UI_VoteCustomMenu( void );
+
+//
 // ui_players.c
 //
 
@@ -491,9 +581,8 @@
 	qhandle_t		headSkin;
 
 	animation_t		animations[MAX_ANIMATIONS];
-
-	qboolean                fixedlegs;              // true if legs yaw is always the same as torso yaw
-	qboolean                fixedtorso;             // true if torso never changes yaw
+	qboolean		fixedlegs;		// true if legs yaw is always the same as torso yaw
+	qboolean		fixedtorso;		// true if torso never changes yaw
 
 	qhandle_t		weaponModel;
 	qhandle_t		barrelModel;
@@ -501,9 +590,6 @@
 	vec3_t			flashDlightColor;
 	int				muzzleFlashTime;
 
-	vec3_t color1;
-	byte c1RGBA[4];
-
 	// currently in use drawing parms
 	vec3_t			viewAngles;
 	vec3_t			moveAngles;
@@ -565,18 +651,17 @@
 	float				bias;
 	qboolean			demoversion;
 	qboolean			firstdraw;
-	qboolean showErrorMenu;
 } uiStatic_t;
 
 extern void			UI_Init( void );
 extern void			UI_Shutdown( void );
 extern void			UI_KeyEvent( int key, int down );
-extern void			UI_MouseEvent( int dx, int dy, qboolean active );
+extern void			UI_MouseEvent( int dx, int dy );
 extern void			UI_Refresh( int realtime );
 extern qboolean		UI_ConsoleCommand( int realTime );
 extern float		UI_ClampCvar( float min, float max, float value );
 extern void			UI_DrawNamedPic( float x, float y, float width, float height, const char *picname );
-extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader );
+extern void			UI_DrawHandlePic( float x, float y, float w, float h, qhandle_t hShader ); 
 extern void			UI_FillRect( float x, float y, float width, float height, const float *color );
 extern void			UI_DrawRect( float x, float y, float width, float height, const float *color );
 extern void			UI_UpdateScreen( void );
@@ -633,7 +718,7 @@
 // ui_syscalls.c
 //
 void			trap_Print( const char *string );
-void			trap_Error( const char *string ) Q_NO_RETURN;
+void			trap_Error( const char *string )  __attribute__((noreturn));
 int				trap_Milliseconds( void );
 void			trap_Cvar_Register( vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags );
 void			trap_Cvar_Update( vmCvar_t *vmCvar );
@@ -692,13 +777,9 @@
 void			trap_GetCDKey( char *buf, int buflen );
 void			trap_SetCDKey( char *buf );
 
-qboolean               trap_VerifyCDKey( const char *key, const char *chksum);
+qboolean               trap_VerifyCDKey( const char *key, const char *chksum); // bk001208 - RC4
 
 void			trap_SetPbClStatus( int status );
-void trap_OpenQuakeLiveDirectory (void);
-void trap_OpenWolfcamDirectory (void);
-void trap_DrawConsoleLinesOver (int xpos, int ypos, int numLines);
-void trap_R_BeginHud (void);
 
 //
 // ui_addbots.c

```
