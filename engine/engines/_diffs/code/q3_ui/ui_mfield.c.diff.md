# Diff: `code/q3_ui/ui_mfield.c`
**Canonical:** `wolfcamql-src` (sha256 `53c2309410de...`, 9300 bytes)

## Variants

### `quake3-source`  — sha256 `9cf3e650e1ee...`, 9340 bytes

_Diff stat: +7 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_mfield.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_mfield.c	2026-04-16 20:02:19.948586100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -253,7 +253,7 @@
 		return;
 	}
 
-	if ( trap_Key_GetOverstrikeMode() ) {	
+	if ( !trap_Key_GetOverstrikeMode() ) {	
 		if ((edit->cursor == MAX_EDIT_LINE - 1) || (edit->maxchars && edit->cursor >= edit->maxchars))
 			return;
 	} else {
@@ -334,6 +334,7 @@
 	int		x;
 	int		y;
 	int		w;
+	int		h;
 	int		style;
 	qboolean focus;
 	float	*color;
@@ -344,13 +345,15 @@
 	if (f->generic.flags & QMF_SMALLFONT)
 	{
 		w = SMALLCHAR_WIDTH;
+		h = SMALLCHAR_HEIGHT;
 		style = UI_SMALLFONT;
 	}
 	else
 	{
 		w = BIGCHAR_WIDTH;
+		h = BIGCHAR_HEIGHT;
 		style = UI_BIGFONT;
-	}
+	}	
 
 	if (Menu_ItemAtCursor( f->generic.parent ) == f) {
 		focus = qtrue;
@@ -370,7 +373,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color );
+		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|style, color);
 	}
 

```

### `ioquake3`  — sha256 `ad68b14ce3eb...`, 9301 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_mfield.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_mfield.c	2026-04-16 20:02:21.555592800 +0100
@@ -253,7 +253,7 @@
 		return;
 	}
 
-	if ( trap_Key_GetOverstrikeMode() ) {	
+	if ( trap_Key_GetOverstrikeMode() ) {
 		if ((edit->cursor == MAX_EDIT_LINE - 1) || (edit->maxchars && edit->cursor >= edit->maxchars))
 			return;
 	} else {
@@ -350,7 +350,7 @@
 	{
 		w = BIGCHAR_WIDTH;
 		style = UI_BIGFONT;
-	}
+	}	
 
 	if (Menu_ItemAtCursor( f->generic.parent ) == f) {
 		focus = qtrue;
@@ -370,7 +370,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color );
+		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|style, color);
 	}
 

```

### `openarena-engine`  — sha256 `14231cb2c0d0...`, 9303 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_mfield.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_mfield.c	2026-04-16 22:48:25.896194800 +0100
@@ -253,7 +253,7 @@
 		return;
 	}
 
-	if ( trap_Key_GetOverstrikeMode() ) {	
+	if ( !trap_Key_GetOverstrikeMode() ) {	
 		if ((edit->cursor == MAX_EDIT_LINE - 1) || (edit->maxchars && edit->cursor >= edit->maxchars))
 			return;
 	} else {
@@ -350,7 +350,7 @@
 	{
 		w = BIGCHAR_WIDTH;
 		style = UI_BIGFONT;
-	}
+	}	
 
 	if (Menu_ItemAtCursor( f->generic.parent ) == f) {
 		focus = qtrue;
@@ -370,7 +370,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color );
+		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|style, color);
 	}
 

```

### `openarena-gamecode`  — sha256 `a9fcbfdfcdfa...`, 9091 bytes

_Diff stat: +11 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_mfield.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_mfield.c	2026-04-16 22:48:24.183498100 +0100
@@ -140,14 +140,14 @@
 	int		len;
 
 	// shift-insert is paste
-	if ( ( ( key == K_INS ) || ( key == K_KP_INS ) ) && trap_Key_IsDown( K_SHIFT ) ) {
+	if ( ( key == K_INS ) && trap_Key_IsDown( K_SHIFT ) ) {
 		MField_Paste( edit );
 		return;
 	}
 
 	len = strlen( edit->buffer );
 
-	if ( key == K_DEL || key == K_KP_DEL ) {
+	if ( key == K_DEL ) {
 		if ( edit->cursor < len ) {
 			memmove( edit->buffer + edit->cursor, 
 				edit->buffer + edit->cursor + 1, len - edit->cursor );
@@ -155,7 +155,7 @@
 		return;
 	}
 
-	if ( key == K_RIGHTARROW || key == K_KP_RIGHTARROW ) 
+	if ( key == K_RIGHTARROW ) 
 	{
 		if ( edit->cursor < len ) {
 			edit->cursor++;
@@ -167,7 +167,7 @@
 		return;
 	}
 
-	if ( key == K_LEFTARROW || key == K_KP_LEFTARROW ) 
+	if ( key == K_LEFTARROW ) 
 	{
 		if ( edit->cursor > 0 ) {
 			edit->cursor--;
@@ -179,13 +179,13 @@
 		return;
 	}
 
-	if ( key == K_HOME || key == K_KP_HOME || ( tolower(key) == 'a' && trap_Key_IsDown( K_CTRL ) ) ) {
+	if ( key == K_HOME || ( tolower(key) == 'a' && trap_Key_IsDown( K_CTRL ) ) ) {
 		edit->cursor = 0;
 		edit->scroll = 0;
 		return;
 	}
 
-	if ( key == K_END || key == K_KP_END || ( tolower(key) == 'e' && trap_Key_IsDown( K_CTRL ) ) ) {
+	if ( key == K_END || ( tolower(key) == 'e' && trap_Key_IsDown( K_CTRL ) ) ) {
 		edit->cursor = len;
 		edit->scroll = len - edit->widthInChars + 1;
 		if (edit->scroll < 0)
@@ -193,7 +193,7 @@
 		return;
 	}
 
-	if ( key == K_INS || key == K_KP_INS ) {
+	if ( key == K_INS  ) {
 		trap_Key_SetOverstrikeMode( !trap_Key_GetOverstrikeMode() );
 		return;
 	}
@@ -232,7 +232,7 @@
 		return;
 	}
 
-	if ( ch == 'a' - 'a' + 1 ) {	// ctrl-a is home
+	if ( ch == 1 ) {	// ctrl-a is home
 		edit->cursor = 0;
 		edit->scroll = 0;
 		return;
@@ -253,7 +253,7 @@
 		return;
 	}
 
-	if ( trap_Key_GetOverstrikeMode() ) {	
+	if ( !trap_Key_GetOverstrikeMode() ) {	
 		if ((edit->cursor == MAX_EDIT_LINE - 1) || (edit->maxchars && edit->cursor >= edit->maxchars))
 			return;
 	} else {
@@ -350,7 +350,7 @@
 	{
 		w = BIGCHAR_WIDTH;
 		style = UI_BIGFONT;
-	}
+	}	
 
 	if (Menu_ItemAtCursor( f->generic.parent ) == f) {
 		focus = qtrue;
@@ -370,7 +370,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color );
+		UI_FillRect( f->generic.left, f->generic.top, f->generic.right-f->generic.left+1, f->generic.bottom-f->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|style, color);
 	}
 
@@ -405,9 +405,7 @@
 			break;
 
 		case K_TAB:
-		case K_KP_DOWNARROW:
 		case K_DOWNARROW:
-		case K_KP_UPARROW:
 		case K_UPARROW:
 			break;
 

```
