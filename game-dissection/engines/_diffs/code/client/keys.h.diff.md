# Diff: `code/client/keys.h`
**Canonical:** `wolfcamql-src` (sha256 `c10125f87e7e...`, 2699 bytes)

## Variants

### `quake3-source`  — sha256 `7f5f8d75158a...`, 2130 bytes

_Diff stat: +8 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\keys.h	2026-04-16 20:02:25.174724100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\keys.h	2026-04-16 20:02:19.894095900 +0100
@@ -1,6 +1,3 @@
-#ifndef keys_h_included
-#define keys_h_included
-
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -18,11 +15,13 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
-#include "keycodes.h"
+#include "../ui/keycodes.h"
+
+#define	MAX_KEYS		256
 
 typedef struct {
 	qboolean	down;
@@ -30,39 +29,29 @@
 	char		*binding;
 } qkey_t;
 
-//extern	qboolean	key_overstrikeMode;
+extern	qboolean	key_overstrikeMode;
 extern	qkey_t		keys[MAX_KEYS];
 
 // NOTE TTimo the declaration of field_t and Field_Clear is now in qcommon/qcommon.h
 void Field_KeyDownEvent( field_t *edit, int key );
 void Field_CharEvent( field_t *edit, int ch );
-void Field_Draw( field_t *edit, int x, int y, int width, qboolean showCursor, qboolean noColorEscape );
-void Field_BigDraw( field_t *edit, int x, int y, int width, qboolean showCursor, qboolean noColorEscape );
-void Field_VariableSizeDraw (field_t *edit, float x, float y, int width, int size, qboolean drawSmall, float cwidth, float cheight, qboolean showCursor, qboolean noColorEscape);
+void Field_Draw( field_t *edit, int x, int y, int width, qboolean showCursor );
+void Field_BigDraw( field_t *edit, int x, int y, int width, qboolean showCursor );
 
 #define		COMMAND_HISTORY		32
 extern	field_t	historyEditLines[COMMAND_HISTORY];
 
 extern	field_t	g_consoleField;
 extern	field_t	chatField;
-extern	int				anykeydown;
+extern	qboolean	anykeydown;
 extern	qboolean	chat_team;
 extern	int			chat_playerNum;
 
 void Key_WriteBindings( fileHandle_t f );
 void Key_SetBinding( int keynum, const char *binding );
 char *Key_GetBinding( int keynum );
-void Key_KeynumToStringBuf( int keynum, char *buf, int buflen );
-void Key_GetBindingBuf( int keynum, char *buf, int buflen );
-
-void Cgame_Key_GetBinding(int keynum, char *buffer);
 qboolean Key_IsDown( int keynum );
 qboolean Key_GetOverstrikeMode( void );
 void Key_SetOverstrikeMode( qboolean state );
 void Key_ClearStates( void );
 int Key_GetKey(const char *binding);
-
-int Key_StringToKeynum( const char *str );
-char *Key_KeynumToString (int keynum);
-
-#endif  // keys_h_included

```

### `openarena-engine`  — sha256 `eba914efba10...`, 2166 bytes
Also identical in: ioquake3

_Diff stat: +1 / -14 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\keys.h	2026-04-16 20:02:25.174724100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\keys.h	2026-04-16 22:48:25.733378900 +0100
@@ -1,6 +1,3 @@
-#ifndef keys_h_included
-#define keys_h_included
-
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -30,7 +27,7 @@
 	char		*binding;
 } qkey_t;
 
-//extern	qboolean	key_overstrikeMode;
+extern	qboolean	key_overstrikeMode;
 extern	qkey_t		keys[MAX_KEYS];
 
 // NOTE TTimo the declaration of field_t and Field_Clear is now in qcommon/qcommon.h
@@ -38,7 +35,6 @@
 void Field_CharEvent( field_t *edit, int ch );
 void Field_Draw( field_t *edit, int x, int y, int width, qboolean showCursor, qboolean noColorEscape );
 void Field_BigDraw( field_t *edit, int x, int y, int width, qboolean showCursor, qboolean noColorEscape );
-void Field_VariableSizeDraw (field_t *edit, float x, float y, int width, int size, qboolean drawSmall, float cwidth, float cheight, qboolean showCursor, qboolean noColorEscape);
 
 #define		COMMAND_HISTORY		32
 extern	field_t	historyEditLines[COMMAND_HISTORY];
@@ -52,17 +48,8 @@
 void Key_WriteBindings( fileHandle_t f );
 void Key_SetBinding( int keynum, const char *binding );
 char *Key_GetBinding( int keynum );
-void Key_KeynumToStringBuf( int keynum, char *buf, int buflen );
-void Key_GetBindingBuf( int keynum, char *buf, int buflen );
-
-void Cgame_Key_GetBinding(int keynum, char *buffer);
 qboolean Key_IsDown( int keynum );
 qboolean Key_GetOverstrikeMode( void );
 void Key_SetOverstrikeMode( qboolean state );
 void Key_ClearStates( void );
 int Key_GetKey(const char *binding);
-
-int Key_StringToKeynum( const char *str );
-char *Key_KeynumToString (int keynum);
-
-#endif  // keys_h_included

```

### `quake3e`  — sha256 `5e72b9b78827...`, 1884 bytes

_Diff stat: +13 / -28 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\keys.h	2026-04-16 20:02:25.174724100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\keys.h	2026-04-16 20:02:26.914504200 +0100
@@ -1,6 +1,3 @@
-#ifndef keys_h_included
-#define keys_h_included
-
 /*
 ===========================================================================
 Copyright (C) 1999-2005 Id Software, Inc.
@@ -26,43 +23,31 @@
 
 typedef struct {
 	qboolean	down;
+	qboolean	bound;
 	int			repeats;		// if > 1, it is autorepeating
 	char		*binding;
 } qkey_t;
 
-//extern	qboolean	key_overstrikeMode;
+extern	qboolean	key_overstrikeMode;
 extern	qkey_t		keys[MAX_KEYS];
 
+extern  int         anykeydown;
+
 // NOTE TTimo the declaration of field_t and Field_Clear is now in qcommon/qcommon.h
-void Field_KeyDownEvent( field_t *edit, int key );
-void Field_CharEvent( field_t *edit, int ch );
-void Field_Draw( field_t *edit, int x, int y, int width, qboolean showCursor, qboolean noColorEscape );
-void Field_BigDraw( field_t *edit, int x, int y, int width, qboolean showCursor, qboolean noColorEscape );
-void Field_VariableSizeDraw (field_t *edit, float x, float y, int width, int size, qboolean drawSmall, float cwidth, float cheight, qboolean showCursor, qboolean noColorEscape);
-
-#define		COMMAND_HISTORY		32
-extern	field_t	historyEditLines[COMMAND_HISTORY];
-
-extern	field_t	g_consoleField;
-extern	field_t	chatField;
-extern	int				anykeydown;
-extern	qboolean	chat_team;
-extern	int			chat_playerNum;
 
 void Key_WriteBindings( fileHandle_t f );
 void Key_SetBinding( int keynum, const char *binding );
-char *Key_GetBinding( int keynum );
-void Key_KeynumToStringBuf( int keynum, char *buf, int buflen );
-void Key_GetBindingBuf( int keynum, char *buf, int buflen );
+const char *Key_GetBinding( int keynum );
+void Key_ParseBinding( int key, qboolean down, unsigned time );
+
+int Key_GetKey( const char *binding );
+const char *Key_KeynumToString( int keynum );
+int Key_StringToKeynum( const char *str );
 
-void Cgame_Key_GetBinding(int keynum, char *buffer);
 qboolean Key_IsDown( int keynum );
-qboolean Key_GetOverstrikeMode( void );
-void Key_SetOverstrikeMode( qboolean state );
 void Key_ClearStates( void );
-int Key_GetKey(const char *binding);
 
-int Key_StringToKeynum( const char *str );
-char *Key_KeynumToString (int keynum);
+qboolean Key_GetOverstrikeMode( void );
+void Key_SetOverstrikeMode( qboolean state );
 
-#endif  // keys_h_included
+void Com_InitKeyCommands( void );

```
