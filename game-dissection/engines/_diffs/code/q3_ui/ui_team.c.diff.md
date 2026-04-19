# Diff: `code/q3_ui/ui_team.c`
**Canonical:** `wolfcamql-src` (sha256 `dacf9eb9adba...`, 5813 bytes)

## Variants

### `quake3-source`  — sha256 `43b09a858275...`, 6181 bytes

_Diff stat: +22 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_team.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_team.c	2026-04-16 20:02:19.955611800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -47,6 +47,16 @@
 
 static teammain_t	s_teammain;
 
+// bk001204 - unused
+//static menuframework_s	s_teammain_menu;
+//static menuaction_s		s_teammain_orders;
+//static menuaction_s		s_teammain_voice;
+//static menuaction_s		s_teammain_joinred;
+//static menuaction_s		s_teammain_joinblue;
+//static menuaction_s		s_teammain_joingame;
+//static menuaction_s		s_teammain_spectate;
+
+
 /*
 ===============
 TeamMain_MenuEvent
@@ -150,16 +160,25 @@
 	s_teammain.spectate.string           = "SPECTATE";
 	s_teammain.spectate.style            = UI_CENTER|UI_SMALLFONT;
 	s_teammain.spectate.color            = colorRed;
+	y += 20;
 
 	trap_GetConfigString(CS_SERVERINFO, info, MAX_INFO_STRING);   
 	gametype = atoi( Info_ValueForKey( info,"g_gametype" ) );
 			      
 	// set initial states
-	if (gametype == GT_SINGLE_PLAYER  ||  gametype == GT_FFA  ||  gametype == GT_TOURNAMENT) {
+	switch( gametype ) {
+	case GT_SINGLE_PLAYER:
+	case GT_FFA:
+	case GT_TOURNAMENT:
 		s_teammain.joinred.generic.flags  |= QMF_GRAYED;
 		s_teammain.joinblue.generic.flags |= QMF_GRAYED;
-	} else {
+		break;
+
+	default:
+	case GT_TEAM:
+	case GT_CTF:
 		s_teammain.joingame.generic.flags |= QMF_GRAYED;
+		break;
 	}
 
 	Menu_AddItem( &s_teammain.menu, (void*) &s_teammain.frame );

```

### `ioquake3`  — sha256 `077c54b26073...`, 5858 bytes

_Diff stat: +10 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_team.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_team.c	2026-04-16 20:02:21.562593700 +0100
@@ -155,11 +155,19 @@
 	gametype = atoi( Info_ValueForKey( info,"g_gametype" ) );
 			      
 	// set initial states
-	if (gametype == GT_SINGLE_PLAYER  ||  gametype == GT_FFA  ||  gametype == GT_TOURNAMENT) {
+	switch( gametype ) {
+	case GT_SINGLE_PLAYER:
+	case GT_FFA:
+	case GT_TOURNAMENT:
 		s_teammain.joinred.generic.flags  |= QMF_GRAYED;
 		s_teammain.joinblue.generic.flags |= QMF_GRAYED;
-	} else {
+		break;
+
+	default:
+	case GT_TEAM:
+	case GT_CTF:
 		s_teammain.joingame.generic.flags |= QMF_GRAYED;
+		break;
 	}
 
 	Menu_AddItem( &s_teammain.menu, (void*) &s_teammain.frame );

```

### `openarena-engine`  — sha256 `537870091537...`, 5869 bytes

_Diff stat: +11 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_team.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_team.c	2026-04-16 22:48:25.903298800 +0100
@@ -150,16 +150,25 @@
 	s_teammain.spectate.string           = "SPECTATE";
 	s_teammain.spectate.style            = UI_CENTER|UI_SMALLFONT;
 	s_teammain.spectate.color            = colorRed;
+	y += 20;
 
 	trap_GetConfigString(CS_SERVERINFO, info, MAX_INFO_STRING);   
 	gametype = atoi( Info_ValueForKey( info,"g_gametype" ) );
 			      
 	// set initial states
-	if (gametype == GT_SINGLE_PLAYER  ||  gametype == GT_FFA  ||  gametype == GT_TOURNAMENT) {
+	switch( gametype ) {
+	case GT_SINGLE_PLAYER:
+	case GT_FFA:
+	case GT_TOURNAMENT:
 		s_teammain.joinred.generic.flags  |= QMF_GRAYED;
 		s_teammain.joinblue.generic.flags |= QMF_GRAYED;
-	} else {
+		break;
+
+	default:
+	case GT_TEAM:
+	case GT_CTF:
 		s_teammain.joingame.generic.flags |= QMF_GRAYED;
+		break;
 	}
 
 	Menu_AddItem( &s_teammain.menu, (void*) &s_teammain.frame );

```

### `openarena-gamecode`  — sha256 `3028df75574e...`, 6409 bytes

_Diff stat: +32 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_team.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_team.c	2026-04-16 22:48:24.191007600 +0100
@@ -27,7 +27,7 @@
 #include "ui_local.h"
 
 
-#define TEAMMAIN_FRAME	"menu/art/cut_frame"
+#define TEAMMAIN_FRAME	"menu/" MENU_ART_DIR "/cut_frame"
 
 #define ID_JOINRED		100
 #define ID_JOINBLUE		101
@@ -47,6 +47,16 @@
 
 static teammain_t	s_teammain;
 
+// bk001204 - unused
+//static menuframework_s	s_teammain_menu;
+//static menuaction_s		s_teammain_orders;
+//static menuaction_s		s_teammain_voice;
+//static menuaction_s		s_teammain_joinred;
+//static menuaction_s		s_teammain_joinblue;
+//static menuaction_s		s_teammain_joingame;
+//static menuaction_s		s_teammain_spectate;
+
+
 /*
 ===============
 TeamMain_MenuEvent
@@ -150,16 +160,34 @@
 	s_teammain.spectate.string           = "SPECTATE";
 	s_teammain.spectate.style            = UI_CENTER|UI_SMALLFONT;
 	s_teammain.spectate.color            = colorRed;
+	y += 20;
 
 	trap_GetConfigString(CS_SERVERINFO, info, MAX_INFO_STRING);   
 	gametype = atoi( Info_ValueForKey( info,"g_gametype" ) );
 			      
 	// set initial states
-	if (gametype == GT_SINGLE_PLAYER  ||  gametype == GT_FFA  ||  gametype == GT_TOURNAMENT) {
+	switch( gametype ) {
+	case GT_SINGLE_PLAYER:
+	case GT_FFA:
+	case GT_LMS:
+	case GT_POSSESSION:
+	case GT_TOURNAMENT:
 		s_teammain.joinred.generic.flags  |= QMF_GRAYED;
 		s_teammain.joinblue.generic.flags |= QMF_GRAYED;
-	} else {
-		s_teammain.joingame.generic.flags |= QMF_GRAYED;
+		break;
+
+	default:
+	case GT_TEAM:
+	case GT_CTF:
+	case GT_1FCTF:
+	case GT_OBELISK:
+	case GT_HARVESTER:
+	case GT_ELIMINATION:
+	case GT_CTF_ELIMINATION:
+	case GT_DOUBLE_D:
+	case GT_DOMINATION:
+		s_teammain.joingame.string           = "AUTO JOIN GAME";
+		break;
 	}
 
 	Menu_AddItem( &s_teammain.menu, (void*) &s_teammain.frame );

```
