# Diff: `code/ui/ui_shared.h`
**Canonical:** `wolfcamql-src` (sha256 `f3a51b257210...`, 20339 bytes)

## Variants

### `quake3-source`  — sha256 `12ed36d1f53b...`, 17891 bytes

_Diff stat: +57 / -105 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_shared.h	2026-04-16 20:02:25.820962400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\ui\ui_shared.h	2026-04-16 20:02:19.988148000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -23,27 +23,21 @@
 #define __UI_SHARED_H
 
 
-#include "../qcommon/q_shared.h"
-#include "../renderercommon/tr_types.h"
-#include "../client/keycodes.h"
+#include "../game/q_shared.h"
+#include "../cgame/tr_types.h"
+#include "keycodes.h"
 
 #include "../../ui/menudef.h"
-#include "ui_common.h"
-
-// never used
-//#define MAX_MENUNAME 32
-//#define MAX_ITEMTEXT 64
-//#define MAX_ITEMACTION 64
 
+#define MAX_MENUNAME 32
+#define MAX_ITEMTEXT 64
+#define MAX_ITEMACTION 64
 #define MAX_MENUDEFFILE 4096
 #define MAX_MENUFILE 32768
-#define MAX_MENUS 512  //128
-
+#define MAX_MENUS 64
+#define MAX_MENUITEMS 96
 #define MAX_COLOR_RANGES 10
-#define MAX_OPEN_MENUS 256  //16
-
-#define MAX_MENU_VARS 128
-#define MAX_MENU_VAR_NAME 64
+#define MAX_OPEN_MENUS 16
 
 #define WINDOW_MOUSEOVER			0x00000001	// mouse is over it, non exclusive
 #define WINDOW_HASFOCUS				0x00000002	// has cursor focus, exclusive
@@ -77,15 +71,13 @@
 #define CURSOR_SIZER				0x00000004
 
 #ifdef CGAME
-#define STRING_POOL_SIZE 2 * 1024 * 1024  //128*1024 //128*1024
+#define STRING_POOL_SIZE 128*1024
 #else
-#define STRING_POOL_SIZE 2 * 1024 * 1024  //384*1024
+#define STRING_POOL_SIZE 384*1024
 #endif
+#define MAX_STRING_HANDLES 4096
 
-// unused
-//#define MAX_STRING_HANDLES 4096
-//#define MAX_SCRIPT_ARGS 12
-
+#define MAX_SCRIPT_ARGS 12
 #define MAX_EDITFIELD 256
 
 #define ART_FX_BASE			"menu/art/fx_base"
@@ -111,21 +103,12 @@
 #define SLIDER_HEIGHT 16.0
 #define SLIDER_THUMB_WIDTH 12.0
 #define SLIDER_THUMB_HEIGHT 20.0
+#define	NUM_CROSSHAIRS			10
 
-#define WIDESCREEN_STRETCH 0
-#define WIDESCREEN_LEFT 1
-#define WIDESCREEN_CENTER 2
-#define WIDESCREEN_RIGHT 3
-
-extern int DefaultWideScreenValue;
-
-// unused
-/*
 typedef struct {
   const char *command;
   const char *args[MAX_SCRIPT_ARGS];
 } scriptDef_t;
-*/
 
 
 typedef struct {
@@ -149,7 +132,6 @@
   int border;                     //
   int ownerDraw;									// ownerDraw style
 	int ownerDrawFlags;							// show flags for ownerdraw items
-	int ownerDrawFlags2;
   float borderSize;               // 
   int flags;                      // visible, focus, mouseover, cursor
   Rectangle rectEffects;          // for various effects
@@ -160,8 +142,7 @@
   vec4_t backColor;               // border color
   vec4_t borderColor;             // border color
   vec4_t outlineColor;            // border color
-  qhandle_t background;           // background asset
-  const char *backgroundName;
+  qhandle_t background;           // background asset  
 } windowDef_t;
 
 typedef windowDef_t Window;
@@ -182,7 +163,7 @@
 // the benefits of c++ in DOOM will greatly help crap like this
 // FIXME: need to put a type ptr that points to specific type info per type
 // 
-#define MAX_LB_COLUMNS 32
+#define MAX_LB_COLUMNS 16
 
 typedef struct columnInfo_s {
 	int pos;
@@ -195,13 +176,9 @@
 	int endPos;
 	int drawPadding;
 	int cursorPos;
-	int selectedCursorPos;
 	float elementWidth;
 	float elementHeight;
 	int elementStyle;
-	vec4_t elementColor;
-	vec4_t selectedColor;
-	vec4_t altRowColor;
 	int numColumns;
 	columnInfo_t columnInfo[MAX_LB_COLUMNS];
 	const char *doubleClick;
@@ -226,7 +203,6 @@
 	float cvarValue[MAX_MULTI_CVARS];
 	int count;
 	qboolean strDef;
-	qboolean videoMode;
 } multiDef_t;
 
 typedef struct modelDef_s {
@@ -246,18 +222,15 @@
   Window window;                 // common positional, border, style, layout info
   Rectangle textRect;            // rectangle the text ( if any ) consumes     
   int type;                      // text, button, radiobutton, checkbox, textfield, listbox, combo
-  int alignment;                 // left center right, this is passed to ownerdraw items
-  int textalignment;             // ( optional ) alignment for text within rect based on text width, this is only for the value specified by 'text' and is not passed to ownerdraw items
+  int alignment;                 // left center right
+  int textalignment;             // ( optional ) alignment for text within rect based on text width
   float textalignx;              // ( optional ) text alignment x coord
   float textaligny;              // ( optional ) text alignment x coord
   float textscale;               // scale percentage from 72pts
   int textStyle;                 // ( optional ) style, normal and shadowed are it for now
-	int fontIndex;
   const char *text;              // display text
   void *parent;                  // menu owner
   qhandle_t asset;               // handle to asset
-	const char *assetName;
-  const char *run;  // run this script every frame
   const char *mouseEnterText;    // mouse enter script
   const char *mouseExitText;     // mouse exit script
   const char *mouseEnter;        // mouse enter script
@@ -265,23 +238,16 @@
   const char *action;            // select script
   const char *onFocus;           // select script
   const char *leaveFocus;        // select script
-  const char *cvar;              // associated cvar
+  const char *cvar;              // associated cvar 
   const char *cvarTest;          // associated cvar for enable actions
-  const char *enableCvar;		 // enable, disable, show, or hide based on value, this can contain a list
+	const char *enableCvar;			   // enable, disable, show, or hide based on value, this can contain a list
 	int cvarFlags;								 //	what type of action to take on cvarenables
   sfxHandle_t focusSound;
-	const char *focusSoundName;
-
-	sfxHandle_t playSound;
-	const char *playSoundName;
-
 	int numColors;								 // number of color ranges
 	colorRangeDef_t colorRanges[MAX_COLOR_RANGES];
 	float special;								 // used for feeder id's etc.. diff per type
   int cursorPos;                 // cursor position in characters
-	int precision;
-	void *typeData;								 // type specific data ptr's
-	int widescreen;
+	void *typeData;								 // type specific data ptr's	
 } itemDef_t;
 
 typedef struct {
@@ -302,7 +268,6 @@
   vec4_t focusColor;								// focus color for items
   vec4_t disableColor;							// focus color for items
   itemDef_t *items[MAX_MENUITEMS];	// items this menu contains   
-	int widescreen;
 } menuDef_t;
 
 typedef struct {
@@ -312,8 +277,6 @@
   fontInfo_t textFont;
   fontInfo_t smallFont;
   fontInfo_t bigFont;
-	fontInfo_t extraFonts[MAX_FONTS + 1];  //FIXME hack so that 0 is default
-  int numFonts;
   qhandle_t cursor;
   qhandle_t gradientBar;
   qhandle_t scrollBarArrowUp;
@@ -355,36 +318,34 @@
 typedef struct {
   qhandle_t (*registerShaderNoMip) (const char *p);
   void (*setColor) (const vec4_t v);
-	void (*drawHandlePic) (float x, float y, float w, float h, qhandle_t asset, int widescreen, rectDef_t menuRect);
-	void (*drawStretchPic) (float x, float y, float w, float h, float s1, float t1, float s2, float t2, qhandle_t hShader, int widescreen, rectDef_t menuRect);
-	void (*drawText) (float x, float y, float scale, const vec4_t color, const char *text, float adjust, int limit, int style, int fontIndex, int widescreen, rectDef_t menuRect);
-	float (*textWidth) (const char *text, float scale, int limit, int fontIndex, int widescreen, rectDef_t menuRect);
-	float (*textHeight) (const char *text, float scale, int limit, int fontIndex, int widescreen, rectDef_t menuRect);
+  void (*drawHandlePic) (float x, float y, float w, float h, qhandle_t asset);
+  void (*drawStretchPic) (float x, float y, float w, float h, float s1, float t1, float s2, float t2, qhandle_t hShader );
+  void (*drawText) (float x, float y, float scale, vec4_t color, const char *text, float adjust, int limit, int style );
+  int (*textWidth) (const char *text, float scale, int limit);
+  int (*textHeight) (const char *text, float scale, int limit);
   qhandle_t (*registerModel) (const char *p);
   void (*modelBounds) (qhandle_t model, vec3_t min, vec3_t max);
-	void (*fillRect) (float x, float y, float w, float h, const vec4_t color, int widescreen, rectDef_t menuRect);
-	void (*drawRect) (float x, float y, float w, float h, float size, const vec4_t color, int widescreen, rectDef_t menuRect);
-	void (*drawSides) (float x, float y, float w, float h, float size, int widescreen, rectDef_t menuRect);
-	void (*drawTopBottom) (float x, float y, float w, float h, float size, int widescreen, rectDef_t menuRect);
-  void (*clearScene) ( void );
+  void (*fillRect) ( float x, float y, float w, float h, const vec4_t color);
+  void (*drawRect) ( float x, float y, float w, float h, float size, const vec4_t color);
+  void (*drawSides) (float x, float y, float w, float h, float size);
+  void (*drawTopBottom) (float x, float y, float w, float h, float size);
+  void (*clearScene) ();
   void (*addRefEntityToScene) (const refEntity_t *re );
   void (*renderScene) ( const refdef_t *fd );
   void (*registerFont) (const char *pFontname, int pointSize, fontInfo_t *font);
-	void (*ownerDrawItem) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int ownerDrawFlags2, int align, float special, float scale, const vec4_t color, qhandle_t shader, int textStyle, int fontIndex, int menuWidescreen, int itemWidescreen, rectDef_t menuRect);
-	//void (*ownerDrawItem2) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int align, float special, float scale, vec4_t color, qhandle_t shader, int textStyle, int fontIndex, int menuWidescreen, int itemWidescreen, rectDef_t menuRect);
+  void (*ownerDrawItem) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int align, float special, float scale, vec4_t color, qhandle_t shader, int textStyle);
 	float (*getValue) (int ownerDraw);
-	qboolean (*ownerDrawVisible) (int flags, int flags2);
+	qboolean (*ownerDrawVisible) (int flags);
   void (*runScript)(char **p);
   void (*getTeamColor)(vec4_t *color);
   void (*getCVarString)(const char *cvar, char *buffer, int bufsize);
   float (*getCVarValue)(const char *cvar);
   void (*setCVar)(const char *cvar, const char *value);
-	qboolean (*cvarExists)(const char *var_name);
-	void (*drawTextWithCursor)(float x, float y, float scale, const vec4_t color, const char *text, int cursorPos, char cursor, int limit, int style, int fontIndex, int widescreen, rectDef_t menuRect);
+  void (*drawTextWithCursor)(float x, float y, float scale, vec4_t color, const char *text, int cursorPos, char cursor, int limit, int style);
   void (*setOverstrikeMode)(qboolean b);
-  qboolean (*getOverstrikeMode)( void );
+  qboolean (*getOverstrikeMode)();
   void (*startLocalSound)( sfxHandle_t sfx, int channelNum );
-	qboolean (*ownerDrawHandleKey)(int ownerDraw, int flags, int flags2, float *special, int key);
+  qboolean (*ownerDrawHandleKey)(int ownerDraw, int flags, float *special, int key);
   int (*feederCount)(float feederID);
   const char *(*feederItemText)(float feederID, int index, int column, qhandle_t *handle);
   qhandle_t (*feederItemImage)(float feederID, int index);
@@ -392,24 +353,23 @@
 	void (*keynumToStringBuf)( int keynum, char *buf, int buflen );
 	void (*getBindingBuf)( int keynum, char *buf, int buflen );
 	void (*setBinding)( int keynum, const char *binding );
-	void (*executeText)(int exec_when, const char *text );
-	void (*Error)(int level, const char *error, ...) Q_NO_RETURN Q_PRINTF_FUNC(2, 3);
-	void (*Print)(const char *msg, ...) Q_PRINTF_FUNC(1, 2);
+	void (*executeText)(int exec_when, const char *text );	
+	void (*Error)(int level, const char *error, ...);
+	void (*Print)(const char *msg, ...);
 	void (*Pause)(qboolean b);
-	float (*ownerDrawWidth)(int ownerDraw, float scale, int fontIndex, int widescreen, rectDef_t menuRect);
+	int (*ownerDrawWidth)(int ownerDraw, float scale);
 	sfxHandle_t (*registerSound)(const char *name, qboolean compressed);
 	void (*startBackgroundTrack)( const char *intro, const char *loop);
-	void (*stopBackgroundTrack)( void );
-	int (*playCinematic)(const char *name, float x, float y, float w, float h, int widescreen, rectDef_t menuRect);
+	void (*stopBackgroundTrack)();
+	int (*playCinematic)(const char *name, float x, float y, float w, float h);
 	void (*stopCinematic)(int handle);
-	void (*drawCinematic)(int handle, float x, float y, float w, float h, int widescreen, rectDef_t menuRect);
+	void (*drawCinematic)(int handle, float x, float y, float w, float h);
 	void (*runCinematicFrame)(int handle);
 
   float			yscale;
   float			xscale;
   float			bias;
   int				realTime;
-	float cgTime;
   int				frameTime;
 	int				cursorx;
 	int				cursory;
@@ -422,19 +382,18 @@
   qhandle_t gradientImage;
   qhandle_t cursor;
 	float FPS;
-	int widescreen;
 
 } displayContextDef_t;
 
 const char *String_Alloc(const char *p);
-void String_Init( void );
-void String_Report( void );
+void String_Init();
+void String_Report();
 void Init_Display(displayContextDef_t *dc);
 void Display_ExpandMacros(char * buff);
 void Menu_Init(menuDef_t *menu);
 void Item_Init(itemDef_t *item);
-//void Menu_PostParse(menuDef_t *menu);
-menuDef_t *Menu_GetFocused( void );
+void Menu_PostParse(menuDef_t *menu);
+menuDef_t *Menu_GetFocused();
 void Menu_HandleKey(menuDef_t *menu, int key, qboolean down);
 void Menu_HandleMouseMove(menuDef_t *menu, float x, float y);
 void Menu_ScrollFeeder(menuDef_t *menu, int feeder, qboolean down);
@@ -450,40 +409,33 @@
 qboolean PC_Rect_Parse(int handle, rectDef_t *r);
 qboolean PC_String_Parse(int handle, const char **out);
 qboolean PC_Script_Parse(int handle, const char **out);
-qboolean PC_Parenthesis_Parse(int handle, const char **out);
-qboolean MenuVar_Set (const char *varName, float f);
-float MenuVar_Get (const char *varName);
-char *Q_MathScript (char *script, float *val, int *error);  //FIXME not here
-
-int Menu_Count( void );
+int Menu_Count();
 void Menu_New(int handle);
-void Menu_HandleCapture (void);
-void Menu_PaintAll( void );
+void Menu_PaintAll();
 menuDef_t *Menus_ActivateByName(const char *p);
-void Menu_Reset( void );
-qboolean Menus_AnyFullScreenVisible( void );
+void Menu_Reset();
+qboolean Menus_AnyFullScreenVisible();
 void  Menus_Activate(menuDef_t *menu);
 
-int UI_SelectForKey(int key);
-displayContextDef_t *Display_GetContext( void );
+displayContextDef_t *Display_GetContext();
 void *Display_CaptureItem(int x, int y);
 qboolean Display_MouseMove(void *p, int x, int y);
 int Display_CursorType(int x, int y);
-qboolean Display_KeyBindPending( void );
+qboolean Display_KeyBindPending();
 void Menus_OpenByName(const char *p);
 menuDef_t *Menus_FindByName(const char *p);
 void Menus_ShowByName(const char *p);
 void Menus_CloseByName(const char *p);
 void Display_HandleKey(int key, qboolean down, int x, int y);
 void LerpColor(vec4_t a, vec4_t b, vec4_t c, float t);
-void Menus_CloseAll( void );
+void Menus_CloseAll();
 void Menu_Paint(menuDef_t *menu, qboolean forcePaint);
 void Menu_SetFeederSelection(menuDef_t *menu, int feeder, int index, const char *name);
-void Display_CacheAll( void );
+void Display_CacheAll();
 
 void *UI_Alloc( int size );
 void UI_InitMemory( void );
-qboolean UI_OutOfMemory( void );
+qboolean UI_OutOfMemory();
 
 void Controls_GetConfig( void );
 void Controls_SetConfig(qboolean restart);

```

### `ioquake3`  — sha256 `ab7416ab7686...`, 18129 bytes

_Diff stat: +36 / -82 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_shared.h	2026-04-16 20:02:25.820962400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\ui\ui_shared.h	2026-04-16 20:02:21.815055200 +0100
@@ -28,22 +28,16 @@
 #include "../client/keycodes.h"
 
 #include "../../ui/menudef.h"
-#include "ui_common.h"
-
-// never used
-//#define MAX_MENUNAME 32
-//#define MAX_ITEMTEXT 64
-//#define MAX_ITEMACTION 64
 
+#define MAX_MENUNAME 32
+#define MAX_ITEMTEXT 64
+#define MAX_ITEMACTION 64
 #define MAX_MENUDEFFILE 4096
 #define MAX_MENUFILE 32768
-#define MAX_MENUS 512  //128
-
+#define MAX_MENUS 64
+#define MAX_MENUITEMS 96
 #define MAX_COLOR_RANGES 10
-#define MAX_OPEN_MENUS 256  //16
-
-#define MAX_MENU_VARS 128
-#define MAX_MENU_VAR_NAME 64
+#define MAX_OPEN_MENUS 16
 
 #define WINDOW_MOUSEOVER			0x00000001	// mouse is over it, non exclusive
 #define WINDOW_HASFOCUS				0x00000002	// has cursor focus, exclusive
@@ -77,15 +71,13 @@
 #define CURSOR_SIZER				0x00000004
 
 #ifdef CGAME
-#define STRING_POOL_SIZE 2 * 1024 * 1024  //128*1024 //128*1024
+#define STRING_POOL_SIZE 128*1024
 #else
-#define STRING_POOL_SIZE 2 * 1024 * 1024  //384*1024
+#define STRING_POOL_SIZE 384*1024
 #endif
+#define MAX_STRING_HANDLES 4096
 
-// unused
-//#define MAX_STRING_HANDLES 4096
-//#define MAX_SCRIPT_ARGS 12
-
+#define MAX_SCRIPT_ARGS 12
 #define MAX_EDITFIELD 256
 
 #define ART_FX_BASE			"menu/art/fx_base"
@@ -111,21 +103,12 @@
 #define SLIDER_HEIGHT 16.0
 #define SLIDER_THUMB_WIDTH 12.0
 #define SLIDER_THUMB_HEIGHT 20.0
+#define	NUM_CROSSHAIRS			10
 
-#define WIDESCREEN_STRETCH 0
-#define WIDESCREEN_LEFT 1
-#define WIDESCREEN_CENTER 2
-#define WIDESCREEN_RIGHT 3
-
-extern int DefaultWideScreenValue;
-
-// unused
-/*
 typedef struct {
   const char *command;
   const char *args[MAX_SCRIPT_ARGS];
 } scriptDef_t;
-*/
 
 
 typedef struct {
@@ -149,7 +132,6 @@
   int border;                     //
   int ownerDraw;									// ownerDraw style
 	int ownerDrawFlags;							// show flags for ownerdraw items
-	int ownerDrawFlags2;
   float borderSize;               // 
   int flags;                      // visible, focus, mouseover, cursor
   Rectangle rectEffects;          // for various effects
@@ -160,8 +142,7 @@
   vec4_t backColor;               // border color
   vec4_t borderColor;             // border color
   vec4_t outlineColor;            // border color
-  qhandle_t background;           // background asset
-  const char *backgroundName;
+  qhandle_t background;           // background asset  
 } windowDef_t;
 
 typedef windowDef_t Window;
@@ -182,7 +163,7 @@
 // the benefits of c++ in DOOM will greatly help crap like this
 // FIXME: need to put a type ptr that points to specific type info per type
 // 
-#define MAX_LB_COLUMNS 32
+#define MAX_LB_COLUMNS 16
 
 typedef struct columnInfo_s {
 	int pos;
@@ -195,13 +176,9 @@
 	int endPos;
 	int drawPadding;
 	int cursorPos;
-	int selectedCursorPos;
 	float elementWidth;
 	float elementHeight;
 	int elementStyle;
-	vec4_t elementColor;
-	vec4_t selectedColor;
-	vec4_t altRowColor;
 	int numColumns;
 	columnInfo_t columnInfo[MAX_LB_COLUMNS];
 	const char *doubleClick;
@@ -246,18 +223,15 @@
   Window window;                 // common positional, border, style, layout info
   Rectangle textRect;            // rectangle the text ( if any ) consumes     
   int type;                      // text, button, radiobutton, checkbox, textfield, listbox, combo
-  int alignment;                 // left center right, this is passed to ownerdraw items
-  int textalignment;             // ( optional ) alignment for text within rect based on text width, this is only for the value specified by 'text' and is not passed to ownerdraw items
+  int alignment;                 // left center right
+  int textalignment;             // ( optional ) alignment for text within rect based on text width
   float textalignx;              // ( optional ) text alignment x coord
   float textaligny;              // ( optional ) text alignment x coord
   float textscale;               // scale percentage from 72pts
   int textStyle;                 // ( optional ) style, normal and shadowed are it for now
-	int fontIndex;
   const char *text;              // display text
   void *parent;                  // menu owner
   qhandle_t asset;               // handle to asset
-	const char *assetName;
-  const char *run;  // run this script every frame
   const char *mouseEnterText;    // mouse enter script
   const char *mouseExitText;     // mouse exit script
   const char *mouseEnter;        // mouse enter script
@@ -265,23 +239,16 @@
   const char *action;            // select script
   const char *onFocus;           // select script
   const char *leaveFocus;        // select script
-  const char *cvar;              // associated cvar
+  const char *cvar;              // associated cvar 
   const char *cvarTest;          // associated cvar for enable actions
-  const char *enableCvar;		 // enable, disable, show, or hide based on value, this can contain a list
+	const char *enableCvar;			   // enable, disable, show, or hide based on value, this can contain a list
 	int cvarFlags;								 //	what type of action to take on cvarenables
   sfxHandle_t focusSound;
-	const char *focusSoundName;
-
-	sfxHandle_t playSound;
-	const char *playSoundName;
-
 	int numColors;								 // number of color ranges
 	colorRangeDef_t colorRanges[MAX_COLOR_RANGES];
 	float special;								 // used for feeder id's etc.. diff per type
   int cursorPos;                 // cursor position in characters
-	int precision;
-	void *typeData;								 // type specific data ptr's
-	int widescreen;
+	void *typeData;								 // type specific data ptr's	
 } itemDef_t;
 
 typedef struct {
@@ -302,7 +269,6 @@
   vec4_t focusColor;								// focus color for items
   vec4_t disableColor;							// focus color for items
   itemDef_t *items[MAX_MENUITEMS];	// items this menu contains   
-	int widescreen;
 } menuDef_t;
 
 typedef struct {
@@ -312,8 +278,6 @@
   fontInfo_t textFont;
   fontInfo_t smallFont;
   fontInfo_t bigFont;
-	fontInfo_t extraFonts[MAX_FONTS + 1];  //FIXME hack so that 0 is default
-  int numFonts;
   qhandle_t cursor;
   qhandle_t gradientBar;
   qhandle_t scrollBarArrowUp;
@@ -355,36 +319,34 @@
 typedef struct {
   qhandle_t (*registerShaderNoMip) (const char *p);
   void (*setColor) (const vec4_t v);
-	void (*drawHandlePic) (float x, float y, float w, float h, qhandle_t asset, int widescreen, rectDef_t menuRect);
-	void (*drawStretchPic) (float x, float y, float w, float h, float s1, float t1, float s2, float t2, qhandle_t hShader, int widescreen, rectDef_t menuRect);
-	void (*drawText) (float x, float y, float scale, const vec4_t color, const char *text, float adjust, int limit, int style, int fontIndex, int widescreen, rectDef_t menuRect);
-	float (*textWidth) (const char *text, float scale, int limit, int fontIndex, int widescreen, rectDef_t menuRect);
-	float (*textHeight) (const char *text, float scale, int limit, int fontIndex, int widescreen, rectDef_t menuRect);
+  void (*drawHandlePic) (float x, float y, float w, float h, qhandle_t asset);
+  void (*drawStretchPic) (float x, float y, float w, float h, float s1, float t1, float s2, float t2, qhandle_t hShader );
+  void (*drawText) (float x, float y, float scale, vec4_t color, const char *text, float adjust, int limit, int style );
+  int (*textWidth) (const char *text, float scale, int limit);
+  int (*textHeight) (const char *text, float scale, int limit);
   qhandle_t (*registerModel) (const char *p);
   void (*modelBounds) (qhandle_t model, vec3_t min, vec3_t max);
-	void (*fillRect) (float x, float y, float w, float h, const vec4_t color, int widescreen, rectDef_t menuRect);
-	void (*drawRect) (float x, float y, float w, float h, float size, const vec4_t color, int widescreen, rectDef_t menuRect);
-	void (*drawSides) (float x, float y, float w, float h, float size, int widescreen, rectDef_t menuRect);
-	void (*drawTopBottom) (float x, float y, float w, float h, float size, int widescreen, rectDef_t menuRect);
+  void (*fillRect) ( float x, float y, float w, float h, const vec4_t color);
+  void (*drawRect) ( float x, float y, float w, float h, float size, const vec4_t color);
+  void (*drawSides) (float x, float y, float w, float h, float size);
+  void (*drawTopBottom) (float x, float y, float w, float h, float size);
   void (*clearScene) ( void );
   void (*addRefEntityToScene) (const refEntity_t *re );
   void (*renderScene) ( const refdef_t *fd );
   void (*registerFont) (const char *pFontname, int pointSize, fontInfo_t *font);
-	void (*ownerDrawItem) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int ownerDrawFlags2, int align, float special, float scale, const vec4_t color, qhandle_t shader, int textStyle, int fontIndex, int menuWidescreen, int itemWidescreen, rectDef_t menuRect);
-	//void (*ownerDrawItem2) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int align, float special, float scale, vec4_t color, qhandle_t shader, int textStyle, int fontIndex, int menuWidescreen, int itemWidescreen, rectDef_t menuRect);
+  void (*ownerDrawItem) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int align, float special, float scale, vec4_t color, qhandle_t shader, int textStyle);
 	float (*getValue) (int ownerDraw);
-	qboolean (*ownerDrawVisible) (int flags, int flags2);
+	qboolean (*ownerDrawVisible) (int flags);
   void (*runScript)(char **p);
   void (*getTeamColor)(vec4_t *color);
   void (*getCVarString)(const char *cvar, char *buffer, int bufsize);
   float (*getCVarValue)(const char *cvar);
   void (*setCVar)(const char *cvar, const char *value);
-	qboolean (*cvarExists)(const char *var_name);
-	void (*drawTextWithCursor)(float x, float y, float scale, const vec4_t color, const char *text, int cursorPos, char cursor, int limit, int style, int fontIndex, int widescreen, rectDef_t menuRect);
+  void (*drawTextWithCursor)(float x, float y, float scale, vec4_t color, const char *text, int cursorPos, char cursor, int limit, int style);
   void (*setOverstrikeMode)(qboolean b);
   qboolean (*getOverstrikeMode)( void );
   void (*startLocalSound)( sfxHandle_t sfx, int channelNum );
-	qboolean (*ownerDrawHandleKey)(int ownerDraw, int flags, int flags2, float *special, int key);
+  qboolean (*ownerDrawHandleKey)(int ownerDraw, int flags, float *special, int key);
   int (*feederCount)(float feederID);
   const char *(*feederItemText)(float feederID, int index, int column, qhandle_t *handle);
   qhandle_t (*feederItemImage)(float feederID, int index);
@@ -392,24 +354,23 @@
 	void (*keynumToStringBuf)( int keynum, char *buf, int buflen );
 	void (*getBindingBuf)( int keynum, char *buf, int buflen );
 	void (*setBinding)( int keynum, const char *binding );
-	void (*executeText)(int exec_when, const char *text );
+	void (*executeText)(int exec_when, const char *text );	
 	void (*Error)(int level, const char *error, ...) Q_NO_RETURN Q_PRINTF_FUNC(2, 3);
 	void (*Print)(const char *msg, ...) Q_PRINTF_FUNC(1, 2);
 	void (*Pause)(qboolean b);
-	float (*ownerDrawWidth)(int ownerDraw, float scale, int fontIndex, int widescreen, rectDef_t menuRect);
+	int (*ownerDrawWidth)(int ownerDraw, float scale);
 	sfxHandle_t (*registerSound)(const char *name, qboolean compressed);
 	void (*startBackgroundTrack)( const char *intro, const char *loop);
 	void (*stopBackgroundTrack)( void );
-	int (*playCinematic)(const char *name, float x, float y, float w, float h, int widescreen, rectDef_t menuRect);
+	int (*playCinematic)(const char *name, float x, float y, float w, float h);
 	void (*stopCinematic)(int handle);
-	void (*drawCinematic)(int handle, float x, float y, float w, float h, int widescreen, rectDef_t menuRect);
+	void (*drawCinematic)(int handle, float x, float y, float w, float h);
 	void (*runCinematicFrame)(int handle);
 
   float			yscale;
   float			xscale;
   float			bias;
   int				realTime;
-	float cgTime;
   int				frameTime;
 	int				cursorx;
 	int				cursory;
@@ -422,7 +383,6 @@
   qhandle_t gradientImage;
   qhandle_t cursor;
 	float FPS;
-	int widescreen;
 
 } displayContextDef_t;
 
@@ -433,7 +393,7 @@
 void Display_ExpandMacros(char * buff);
 void Menu_Init(menuDef_t *menu);
 void Item_Init(itemDef_t *item);
-//void Menu_PostParse(menuDef_t *menu);
+void Menu_PostParse(menuDef_t *menu);
 menuDef_t *Menu_GetFocused( void );
 void Menu_HandleKey(menuDef_t *menu, int key, qboolean down);
 void Menu_HandleMouseMove(menuDef_t *menu, float x, float y);
@@ -450,14 +410,8 @@
 qboolean PC_Rect_Parse(int handle, rectDef_t *r);
 qboolean PC_String_Parse(int handle, const char **out);
 qboolean PC_Script_Parse(int handle, const char **out);
-qboolean PC_Parenthesis_Parse(int handle, const char **out);
-qboolean MenuVar_Set (const char *varName, float f);
-float MenuVar_Get (const char *varName);
-char *Q_MathScript (char *script, float *val, int *error);  //FIXME not here
-
 int Menu_Count( void );
 void Menu_New(int handle);
-void Menu_HandleCapture (void);
 void Menu_PaintAll( void );
 menuDef_t *Menus_ActivateByName(const char *p);
 void Menu_Reset( void );

```

### `openarena-engine`  — sha256 `de09d7b6a429...`, 18114 bytes

_Diff stat: +38 / -86 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_shared.h	2026-04-16 20:02:25.820962400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\ui\ui_shared.h	2026-04-16 22:48:25.961607400 +0100
@@ -28,22 +28,16 @@
 #include "../client/keycodes.h"
 
 #include "../../ui/menudef.h"
-#include "ui_common.h"
-
-// never used
-//#define MAX_MENUNAME 32
-//#define MAX_ITEMTEXT 64
-//#define MAX_ITEMACTION 64
 
+#define MAX_MENUNAME 32
+#define MAX_ITEMTEXT 64
+#define MAX_ITEMACTION 64
 #define MAX_MENUDEFFILE 4096
 #define MAX_MENUFILE 32768
-#define MAX_MENUS 512  //128
-
+#define MAX_MENUS 64
+#define MAX_MENUITEMS 96
 #define MAX_COLOR_RANGES 10
-#define MAX_OPEN_MENUS 256  //16
-
-#define MAX_MENU_VARS 128
-#define MAX_MENU_VAR_NAME 64
+#define MAX_OPEN_MENUS 16
 
 #define WINDOW_MOUSEOVER			0x00000001	// mouse is over it, non exclusive
 #define WINDOW_HASFOCUS				0x00000002	// has cursor focus, exclusive
@@ -77,15 +71,13 @@
 #define CURSOR_SIZER				0x00000004
 
 #ifdef CGAME
-#define STRING_POOL_SIZE 2 * 1024 * 1024  //128*1024 //128*1024
+#define STRING_POOL_SIZE 128*1024
 #else
-#define STRING_POOL_SIZE 2 * 1024 * 1024  //384*1024
+#define STRING_POOL_SIZE 384*1024
 #endif
+#define MAX_STRING_HANDLES 4096
 
-// unused
-//#define MAX_STRING_HANDLES 4096
-//#define MAX_SCRIPT_ARGS 12
-
+#define MAX_SCRIPT_ARGS 12
 #define MAX_EDITFIELD 256
 
 #define ART_FX_BASE			"menu/art/fx_base"
@@ -111,21 +103,12 @@
 #define SLIDER_HEIGHT 16.0
 #define SLIDER_THUMB_WIDTH 12.0
 #define SLIDER_THUMB_HEIGHT 20.0
+#define	NUM_CROSSHAIRS			10
 
-#define WIDESCREEN_STRETCH 0
-#define WIDESCREEN_LEFT 1
-#define WIDESCREEN_CENTER 2
-#define WIDESCREEN_RIGHT 3
-
-extern int DefaultWideScreenValue;
-
-// unused
-/*
 typedef struct {
   const char *command;
   const char *args[MAX_SCRIPT_ARGS];
 } scriptDef_t;
-*/
 
 
 typedef struct {
@@ -149,7 +132,6 @@
   int border;                     //
   int ownerDraw;									// ownerDraw style
 	int ownerDrawFlags;							// show flags for ownerdraw items
-	int ownerDrawFlags2;
   float borderSize;               // 
   int flags;                      // visible, focus, mouseover, cursor
   Rectangle rectEffects;          // for various effects
@@ -160,8 +142,7 @@
   vec4_t backColor;               // border color
   vec4_t borderColor;             // border color
   vec4_t outlineColor;            // border color
-  qhandle_t background;           // background asset
-  const char *backgroundName;
+  qhandle_t background;           // background asset  
 } windowDef_t;
 
 typedef windowDef_t Window;
@@ -182,7 +163,7 @@
 // the benefits of c++ in DOOM will greatly help crap like this
 // FIXME: need to put a type ptr that points to specific type info per type
 // 
-#define MAX_LB_COLUMNS 32
+#define MAX_LB_COLUMNS 16
 
 typedef struct columnInfo_s {
 	int pos;
@@ -195,13 +176,9 @@
 	int endPos;
 	int drawPadding;
 	int cursorPos;
-	int selectedCursorPos;
 	float elementWidth;
 	float elementHeight;
 	int elementStyle;
-	vec4_t elementColor;
-	vec4_t selectedColor;
-	vec4_t altRowColor;
 	int numColumns;
 	columnInfo_t columnInfo[MAX_LB_COLUMNS];
 	const char *doubleClick;
@@ -226,7 +203,6 @@
 	float cvarValue[MAX_MULTI_CVARS];
 	int count;
 	qboolean strDef;
-	qboolean videoMode;
 } multiDef_t;
 
 typedef struct modelDef_s {
@@ -246,18 +222,15 @@
   Window window;                 // common positional, border, style, layout info
   Rectangle textRect;            // rectangle the text ( if any ) consumes     
   int type;                      // text, button, radiobutton, checkbox, textfield, listbox, combo
-  int alignment;                 // left center right, this is passed to ownerdraw items
-  int textalignment;             // ( optional ) alignment for text within rect based on text width, this is only for the value specified by 'text' and is not passed to ownerdraw items
+  int alignment;                 // left center right
+  int textalignment;             // ( optional ) alignment for text within rect based on text width
   float textalignx;              // ( optional ) text alignment x coord
   float textaligny;              // ( optional ) text alignment x coord
   float textscale;               // scale percentage from 72pts
   int textStyle;                 // ( optional ) style, normal and shadowed are it for now
-	int fontIndex;
   const char *text;              // display text
   void *parent;                  // menu owner
   qhandle_t asset;               // handle to asset
-	const char *assetName;
-  const char *run;  // run this script every frame
   const char *mouseEnterText;    // mouse enter script
   const char *mouseExitText;     // mouse exit script
   const char *mouseEnter;        // mouse enter script
@@ -265,23 +238,16 @@
   const char *action;            // select script
   const char *onFocus;           // select script
   const char *leaveFocus;        // select script
-  const char *cvar;              // associated cvar
+  const char *cvar;              // associated cvar 
   const char *cvarTest;          // associated cvar for enable actions
-  const char *enableCvar;		 // enable, disable, show, or hide based on value, this can contain a list
+	const char *enableCvar;			   // enable, disable, show, or hide based on value, this can contain a list
 	int cvarFlags;								 //	what type of action to take on cvarenables
   sfxHandle_t focusSound;
-	const char *focusSoundName;
-
-	sfxHandle_t playSound;
-	const char *playSoundName;
-
 	int numColors;								 // number of color ranges
 	colorRangeDef_t colorRanges[MAX_COLOR_RANGES];
 	float special;								 // used for feeder id's etc.. diff per type
   int cursorPos;                 // cursor position in characters
-	int precision;
-	void *typeData;								 // type specific data ptr's
-	int widescreen;
+	void *typeData;								 // type specific data ptr's	
 } itemDef_t;
 
 typedef struct {
@@ -302,7 +268,6 @@
   vec4_t focusColor;								// focus color for items
   vec4_t disableColor;							// focus color for items
   itemDef_t *items[MAX_MENUITEMS];	// items this menu contains   
-	int widescreen;
 } menuDef_t;
 
 typedef struct {
@@ -312,8 +277,6 @@
   fontInfo_t textFont;
   fontInfo_t smallFont;
   fontInfo_t bigFont;
-	fontInfo_t extraFonts[MAX_FONTS + 1];  //FIXME hack so that 0 is default
-  int numFonts;
   qhandle_t cursor;
   qhandle_t gradientBar;
   qhandle_t scrollBarArrowUp;
@@ -355,36 +318,34 @@
 typedef struct {
   qhandle_t (*registerShaderNoMip) (const char *p);
   void (*setColor) (const vec4_t v);
-	void (*drawHandlePic) (float x, float y, float w, float h, qhandle_t asset, int widescreen, rectDef_t menuRect);
-	void (*drawStretchPic) (float x, float y, float w, float h, float s1, float t1, float s2, float t2, qhandle_t hShader, int widescreen, rectDef_t menuRect);
-	void (*drawText) (float x, float y, float scale, const vec4_t color, const char *text, float adjust, int limit, int style, int fontIndex, int widescreen, rectDef_t menuRect);
-	float (*textWidth) (const char *text, float scale, int limit, int fontIndex, int widescreen, rectDef_t menuRect);
-	float (*textHeight) (const char *text, float scale, int limit, int fontIndex, int widescreen, rectDef_t menuRect);
+  void (*drawHandlePic) (float x, float y, float w, float h, qhandle_t asset);
+  void (*drawStretchPic) (float x, float y, float w, float h, float s1, float t1, float s2, float t2, qhandle_t hShader );
+  void (*drawText) (float x, float y, float scale, vec4_t color, const char *text, float adjust, int limit, int style );
+  int (*textWidth) (const char *text, float scale, int limit);
+  int (*textHeight) (const char *text, float scale, int limit);
   qhandle_t (*registerModel) (const char *p);
   void (*modelBounds) (qhandle_t model, vec3_t min, vec3_t max);
-	void (*fillRect) (float x, float y, float w, float h, const vec4_t color, int widescreen, rectDef_t menuRect);
-	void (*drawRect) (float x, float y, float w, float h, float size, const vec4_t color, int widescreen, rectDef_t menuRect);
-	void (*drawSides) (float x, float y, float w, float h, float size, int widescreen, rectDef_t menuRect);
-	void (*drawTopBottom) (float x, float y, float w, float h, float size, int widescreen, rectDef_t menuRect);
+  void (*fillRect) ( float x, float y, float w, float h, const vec4_t color);
+  void (*drawRect) ( float x, float y, float w, float h, float size, const vec4_t color);
+  void (*drawSides) (float x, float y, float w, float h, float size);
+  void (*drawTopBottom) (float x, float y, float w, float h, float size);
   void (*clearScene) ( void );
   void (*addRefEntityToScene) (const refEntity_t *re );
   void (*renderScene) ( const refdef_t *fd );
   void (*registerFont) (const char *pFontname, int pointSize, fontInfo_t *font);
-	void (*ownerDrawItem) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int ownerDrawFlags2, int align, float special, float scale, const vec4_t color, qhandle_t shader, int textStyle, int fontIndex, int menuWidescreen, int itemWidescreen, rectDef_t menuRect);
-	//void (*ownerDrawItem2) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int align, float special, float scale, vec4_t color, qhandle_t shader, int textStyle, int fontIndex, int menuWidescreen, int itemWidescreen, rectDef_t menuRect);
+  void (*ownerDrawItem) (float x, float y, float w, float h, float text_x, float text_y, int ownerDraw, int ownerDrawFlags, int align, float special, float scale, vec4_t color, qhandle_t shader, int textStyle);
 	float (*getValue) (int ownerDraw);
-	qboolean (*ownerDrawVisible) (int flags, int flags2);
+	qboolean (*ownerDrawVisible) (int flags);
   void (*runScript)(char **p);
   void (*getTeamColor)(vec4_t *color);
   void (*getCVarString)(const char *cvar, char *buffer, int bufsize);
   float (*getCVarValue)(const char *cvar);
   void (*setCVar)(const char *cvar, const char *value);
-	qboolean (*cvarExists)(const char *var_name);
-	void (*drawTextWithCursor)(float x, float y, float scale, const vec4_t color, const char *text, int cursorPos, char cursor, int limit, int style, int fontIndex, int widescreen, rectDef_t menuRect);
+  void (*drawTextWithCursor)(float x, float y, float scale, vec4_t color, const char *text, int cursorPos, char cursor, int limit, int style);
   void (*setOverstrikeMode)(qboolean b);
   qboolean (*getOverstrikeMode)( void );
   void (*startLocalSound)( sfxHandle_t sfx, int channelNum );
-	qboolean (*ownerDrawHandleKey)(int ownerDraw, int flags, int flags2, float *special, int key);
+  qboolean (*ownerDrawHandleKey)(int ownerDraw, int flags, float *special, int key);
   int (*feederCount)(float feederID);
   const char *(*feederItemText)(float feederID, int index, int column, qhandle_t *handle);
   qhandle_t (*feederItemImage)(float feederID, int index);
@@ -392,24 +353,23 @@
 	void (*keynumToStringBuf)( int keynum, char *buf, int buflen );
 	void (*getBindingBuf)( int keynum, char *buf, int buflen );
 	void (*setBinding)( int keynum, const char *binding );
-	void (*executeText)(int exec_when, const char *text );
-	void (*Error)(int level, const char *error, ...) Q_NO_RETURN Q_PRINTF_FUNC(2, 3);
-	void (*Print)(const char *msg, ...) Q_PRINTF_FUNC(1, 2);
+	void (*executeText)(int exec_when, const char *text );	
+	void (*Error)(int level, const char *error, ...) __attribute__ ((noreturn, format (printf, 2, 3)));
+	void (*Print)(const char *msg, ...) __attribute__ ((format (printf, 1, 2)));
 	void (*Pause)(qboolean b);
-	float (*ownerDrawWidth)(int ownerDraw, float scale, int fontIndex, int widescreen, rectDef_t menuRect);
+	int (*ownerDrawWidth)(int ownerDraw, float scale);
 	sfxHandle_t (*registerSound)(const char *name, qboolean compressed);
 	void (*startBackgroundTrack)( const char *intro, const char *loop);
 	void (*stopBackgroundTrack)( void );
-	int (*playCinematic)(const char *name, float x, float y, float w, float h, int widescreen, rectDef_t menuRect);
+	int (*playCinematic)(const char *name, float x, float y, float w, float h);
 	void (*stopCinematic)(int handle);
-	void (*drawCinematic)(int handle, float x, float y, float w, float h, int widescreen, rectDef_t menuRect);
+	void (*drawCinematic)(int handle, float x, float y, float w, float h);
 	void (*runCinematicFrame)(int handle);
 
   float			yscale;
   float			xscale;
   float			bias;
   int				realTime;
-	float cgTime;
   int				frameTime;
 	int				cursorx;
 	int				cursory;
@@ -422,7 +382,6 @@
   qhandle_t gradientImage;
   qhandle_t cursor;
 	float FPS;
-	int widescreen;
 
 } displayContextDef_t;
 
@@ -433,7 +392,7 @@
 void Display_ExpandMacros(char * buff);
 void Menu_Init(menuDef_t *menu);
 void Item_Init(itemDef_t *item);
-//void Menu_PostParse(menuDef_t *menu);
+void Menu_PostParse(menuDef_t *menu);
 menuDef_t *Menu_GetFocused( void );
 void Menu_HandleKey(menuDef_t *menu, int key, qboolean down);
 void Menu_HandleMouseMove(menuDef_t *menu, float x, float y);
@@ -450,21 +409,14 @@
 qboolean PC_Rect_Parse(int handle, rectDef_t *r);
 qboolean PC_String_Parse(int handle, const char **out);
 qboolean PC_Script_Parse(int handle, const char **out);
-qboolean PC_Parenthesis_Parse(int handle, const char **out);
-qboolean MenuVar_Set (const char *varName, float f);
-float MenuVar_Get (const char *varName);
-char *Q_MathScript (char *script, float *val, int *error);  //FIXME not here
-
 int Menu_Count( void );
 void Menu_New(int handle);
-void Menu_HandleCapture (void);
 void Menu_PaintAll( void );
 menuDef_t *Menus_ActivateByName(const char *p);
 void Menu_Reset( void );
 qboolean Menus_AnyFullScreenVisible( void );
 void  Menus_Activate(menuDef_t *menu);
 
-int UI_SelectForKey(int key);
 displayContextDef_t *Display_GetContext( void );
 void *Display_CaptureItem(int x, int y);
 qboolean Display_MouseMove(void *p, int x, int y);

```

### `openarena-gamecode`  — sha256 `e6219abe7cb7...`, 20628 bytes

_Diff stat: +386 / -302 lines_

_(full diff is 33383 bytes — see files directly)_
