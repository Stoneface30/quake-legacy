# Diff: `code/q3_ui/ui_credits.c`
**Canonical:** `wolfcamql-src` (sha256 `bbdb204bd3e0...`, 6267 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `4dcb30b6ab52...`, 4893 bytes

_Diff stat: +2 / -52 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_credits.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_credits.c	2026-04-16 20:02:19.945826100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -34,57 +34,12 @@
 
 typedef struct {
 	menuframework_s	menu;
-	int frame;
 } creditsmenu_t;
 
 static creditsmenu_t	s_credits;
 
 
 /*
-===============
-UI_CreditMenu_Draw_ioq3
-===============
-*/
-static void UI_CreditMenu_Draw_ioq3( void ) {
-	int		y;
-	int		i;
-
-	// These are all people that have made commits to Subversion, and thus
-	//  probably incomplete.
-	// (These are in alphabetical order, for the defense of everyone's egos.)
-	static const char *names[] = {
-		"Tim Angus",
-		"James Canete",
-		"Vincent Cojot",
-		"Ryan C. Gordon",
-		"Aaron Gyes",
-		"Zack Middleton",
-		"Ludwig Nussel",
-		"Julian Priestley",
-		"Scirocco Six",
-		"Thilo Schulz",
-		"Zachary J. Slater",
-		"Tony J. White",
-		"...and many, many others!",  // keep this one last.
-		NULL
-	};
-
-	// Center text vertically on the screen
-	y = (SCREEN_HEIGHT - ARRAY_LEN(names) * (1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE)) / 2;
-
-	UI_DrawProportionalString( 320, y, "ioquake3 contributors:", UI_CENTER|UI_SMALLFONT, color_white );
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-
-	for (i = 0; names[i]; i++) {
-		UI_DrawProportionalString( 320, y, names[i], UI_CENTER|UI_SMALLFONT, color_white );
-		y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	}
-
-	UI_DrawString( 320, 459, "https://www.ioquake3.org/", UI_CENTER|UI_SMALLFONT, color_red );
-}
-
-
-/*
 =================
 UI_CreditMenu_Key
 =================
@@ -94,12 +49,7 @@
 		return 0;
 	}
 
-	s_credits.frame++;
-	if (s_credits.frame == 1) {
-		s_credits.menu.draw = UI_CreditMenu_Draw_ioq3;
-	} else {
-		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
-	}
+	trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
 	return 0;
 }
 

```

### `openarena-engine`  — sha256 `6ffe9f4664a7...`, 6266 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_credits.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_credits.c	2026-04-16 22:48:25.894194800 +0100
@@ -80,7 +80,7 @@
 		y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
 	}
 
-	UI_DrawString( 320, 459, "https://www.ioquake3.org/", UI_CENTER|UI_SMALLFONT, color_red );
+	UI_DrawString( 320, 459, "http://www.ioquake3.org/", UI_CENTER|UI_SMALLFONT, color_red );
 }
 
 

```

### `openarena-gamecode`  — sha256 `6104be102685...`, 2729 bytes

_Diff stat: +15 / -98 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_credits.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_credits.c	2026-04-16 22:48:24.181495000 +0100
@@ -28,63 +28,22 @@
 =======================================================================
 */
 
+/*
+ *Sago 2008-06-29: This is kinda annoying and does not really give usefull information anyway
+ */
+
 
 #include "ui_local.h"
 
 
 typedef struct {
 	menuframework_s	menu;
-	int frame;
 } creditsmenu_t;
 
 static creditsmenu_t	s_credits;
 
 
 /*
-===============
-UI_CreditMenu_Draw_ioq3
-===============
-*/
-static void UI_CreditMenu_Draw_ioq3( void ) {
-	int		y;
-	int		i;
-
-	// These are all people that have made commits to Subversion, and thus
-	//  probably incomplete.
-	// (These are in alphabetical order, for the defense of everyone's egos.)
-	static const char *names[] = {
-		"Tim Angus",
-		"James Canete",
-		"Vincent Cojot",
-		"Ryan C. Gordon",
-		"Aaron Gyes",
-		"Zack Middleton",
-		"Ludwig Nussel",
-		"Julian Priestley",
-		"Scirocco Six",
-		"Thilo Schulz",
-		"Zachary J. Slater",
-		"Tony J. White",
-		"...and many, many others!",  // keep this one last.
-		NULL
-	};
-
-	// Center text vertically on the screen
-	y = (SCREEN_HEIGHT - ARRAY_LEN(names) * (1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE)) / 2;
-
-	UI_DrawProportionalString( 320, y, "ioquake3 contributors:", UI_CENTER|UI_SMALLFONT, color_white );
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-
-	for (i = 0; names[i]; i++) {
-		UI_DrawProportionalString( 320, y, names[i], UI_CENTER|UI_SMALLFONT, color_white );
-		y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	}
-
-	UI_DrawString( 320, 459, "https://www.ioquake3.org/", UI_CENTER|UI_SMALLFONT, color_red );
-}
-
-
-/*
 =================
 UI_CreditMenu_Key
 =================
@@ -94,12 +53,8 @@
 		return 0;
 	}
 
-	s_credits.frame++;
-	if (s_credits.frame == 1) {
-		s_credits.menu.draw = UI_CreditMenu_Draw_ioq3;
-	} else {
-		trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
-	}
+        //Sago: I no longer show credits on close. Consider something else if ingame credits are to be made
+	//trap_Cmd_ExecuteText( EXEC_APPEND, "quit\n" );
 	return 0;
 }
 
@@ -113,54 +68,15 @@
 	int		y;
 
 	y = 12;
-	UI_DrawProportionalString( 320, y, "id Software is:", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Programming", UI_CENTER|UI_SMALLFONT, color_white );
+	UI_DrawProportionalString( 320, y, "Thank you for playing", UI_CENTER|UI_SMALLFONT, color_white );
 	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "John Carmack, Robert A. Duffy, Jim Dose'", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Art", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Adrian Carmack, Kevin Cloud,", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Kenneth Scott, Seneca Menard, Fred Nilsson", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Game Designer", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Graeme Devine", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Level Design", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Tim Willits, Christian Antkow, Paul Jaquays", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "CEO", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Todd Hollenshead", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Director of Business Development", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Marty Stratton", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Biz Assist and id Mom", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Donna Jackson", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.42 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Development Assistance", UI_CENTER|UI_SMALLFONT, color_white );
-	y += PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawProportionalString( 320, y, "Eric Webb", UI_CENTER|UI_SMALLFONT, color_white );
-
-	y += 1.35 * PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
-	UI_DrawString( 320, y, "To order: 1-800-idgames     www.quake3arena.com     www.idsoftware.com", UI_CENTER|UI_SMALLFONT, color_red );
-	y += SMALLCHAR_HEIGHT;
-	UI_DrawString( 320, y, "Quake III Arena(c) 1999-2000, Id Software, Inc.  All Rights Reserved", UI_CENTER|UI_SMALLFONT, color_red );
+	UI_DrawProportionalString( 320, y, "Open Arena", UI_CENTER|UI_SMALLFONT, color_white );
+	
+	y += 228;
+	UI_DrawString( 320, y, "Terminating...", UI_CENTER|UI_SMALLFONT, color_red );
+        
+        y = 480 - PROP_HEIGHT * PROP_SMALL_SIZE_SCALE;
+	UI_DrawProportionalString( 320, y, "www.openarena.ws", UI_CENTER|UI_SMALLFONT, color_white );
 }
 
 
@@ -176,4 +92,5 @@
 	s_credits.menu.key = UI_CreditMenu_Key;
 	s_credits.menu.fullscreen = qtrue;
 	UI_PushMenu ( &s_credits.menu );
+        trap_Cmd_ExecuteText( EXEC_APPEND, "wait 2; quit\n" );
 }

```
