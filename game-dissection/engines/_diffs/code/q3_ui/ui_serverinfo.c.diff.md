# Diff: `code/q3_ui/ui_serverinfo.c`
**Canonical:** `wolfcamql-src` (sha256 `0c3f98b37269...`, 7070 bytes)
Also identical in: ioquake3, openarena-engine

## Variants

### `quake3-source`  — sha256 `5638cd5c7c22...`, 7048 bytes

_Diff stat: +5 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_serverinfo.c	2026-04-16 20:02:25.211503700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_serverinfo.c	2026-04-16 20:02:19.951678800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -82,8 +82,8 @@
 			return;
 		}
 		
-		// use first empty available slot
-		if (!adrstr[0] && !best)
+		// use first empty or non-numeric available slot
+		if ((adrstr[0]  < '0' || adrstr[0] > '9' ) && !best)
 			best = i+1;
 	}
 
@@ -128,11 +128,11 @@
 	const char		*s;
 	char			key[MAX_INFO_KEY];
 	char			value[MAX_INFO_VALUE];
-	int				i = 0, y;
+	int				y;
 
 	y = SCREEN_HEIGHT/2 - s_serverinfo.numlines*(SMALLCHAR_HEIGHT)/2 - 20;
 	s = s_serverinfo.info;
-	while ( s && i < s_serverinfo.numlines ) {
+	while ( s ) {
 		Info_NextPair( &s, key, value );
 		if ( !key[0] ) {
 			break;
@@ -144,7 +144,6 @@
 		UI_DrawString(SCREEN_WIDTH*0.50 + 8,y,value,UI_LEFT|UI_SMALLFONT,text_color_normal);
 
 		y += SMALLCHAR_HEIGHT;
-		i++;
 	}
 
 	Menu_Draw( &s_serverinfo.menu );

```

### `openarena-gamecode`  — sha256 `ac3ec25a00c7...`, 7175 bytes

_Diff stat: +9 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_serverinfo.c	2026-04-16 20:02:25.211503700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_serverinfo.c	2026-04-16 22:48:24.186499300 +0100
@@ -22,10 +22,10 @@
 //
 #include "ui_local.h"
 
-#define SERVERINFO_FRAMEL	"menu/art/frame2_l"
-#define SERVERINFO_FRAMER	"menu/art/frame1_r"
-#define SERVERINFO_BACK0	"menu/art/back_0"
-#define SERVERINFO_BACK1	"menu/art/back_1"
+#define SERVERINFO_FRAMEL	"menu/" MENU_ART_DIR "/frame2_l"
+#define SERVERINFO_FRAMER	"menu/" MENU_ART_DIR "/frame1_r"
+#define SERVERINFO_BACK0	"menu/" MENU_ART_DIR "/back_0"
+#define SERVERINFO_BACK1	"menu/" MENU_ART_DIR "/back_1"
 
 static char* serverinfo_artlist[] =
 {
@@ -76,14 +76,14 @@
 	for (i=0; i<MAX_FAVORITESERVERS; i++)
 	{
 		trap_Cvar_VariableStringBuffer( va("server%d",i+1), adrstr, sizeof(adrstr) );
-		if (!Q_stricmp(serverbuff,adrstr))
+		if (Q_strequal(serverbuff,adrstr))
 		{
 			// already in list
 			return;
 		}
 		
-		// use first empty available slot
-		if (!adrstr[0] && !best)
+		// use first empty or non-numeric available slot
+		if ((adrstr[0]  < '0' || adrstr[0] > '9' ) && !best)
 			best = i+1;
 	}
 
@@ -128,7 +128,7 @@
 	const char		*s;
 	char			key[MAX_INFO_KEY];
 	char			value[MAX_INFO_VALUE];
-	int				i = 0, y;
+	int			i=0,y;
 
 	y = SCREEN_HEIGHT/2 - s_serverinfo.numlines*(SMALLCHAR_HEIGHT)/2 - 20;
 	s = s_serverinfo.info;
@@ -144,7 +144,7 @@
 		UI_DrawString(SCREEN_WIDTH*0.50 + 8,y,value,UI_LEFT|UI_SMALLFONT,text_color_normal);
 
 		y += SMALLCHAR_HEIGHT;
-		i++;
+                i++;
 	}
 
 	Menu_Draw( &s_serverinfo.menu );

```
