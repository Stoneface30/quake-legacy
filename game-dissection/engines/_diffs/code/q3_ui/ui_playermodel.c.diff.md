# Diff: `code/q3_ui/ui_playermodel.c`
**Canonical:** `wolfcamql-src` (sha256 `303a4279afb6...`, 21682 bytes)

## Variants

### `quake3-source`  — sha256 `57a6ea2d423e...`, 21493 bytes

_Diff stat: +8 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_playermodel.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_playermodel.c	2026-04-16 20:02:19.949613500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -339,14 +339,14 @@
 		Q_strncpyz(s_playermodel.modelskin,buffptr,pdest-buffptr+1);
 		strcat(s_playermodel.modelskin,pdest + 5);
 
-		// separate the model name
+		// seperate the model name
 		maxlen = pdest-buffptr;
 		if (maxlen > 16)
 			maxlen = 16;
 		Q_strncpyz( s_playermodel.modelname.string, buffptr, maxlen );
 		Q_strupr( s_playermodel.modelname.string );
 
-		// separate the skin name
+		// seperate the skin name
 		maxlen = strlen(pdest+5)+1;
 		if (maxlen > 16)
 			maxlen = 16;
@@ -391,7 +391,7 @@
 	int		numfiles;
 	char	dirlist[2048];
 	char	filelist[2048];
-	char	skinname[MAX_QPATH];
+	char	skinname[64];
 	char*	dirptr;
 	char*	fileptr;
 	int		i;
@@ -424,7 +424,7 @@
 		{
 			filelen = strlen(fileptr);
 
-			COM_StripExtension(fileptr,skinname, sizeof(skinname));
+			COM_StripExtension(fileptr,skinname);
 
 			// look for icon_????
 			if (!Q_stricmpn(skinname,"icon_",5))
@@ -468,12 +468,7 @@
 
 	// model
 	trap_Cvar_VariableStringBuffer( "model", s_playermodel.modelskin, 64 );
-
-	// use default skin if none is set
-	if (!strchr(s_playermodel.modelskin, '/')) {
-		Q_strcat(s_playermodel.modelskin, 64, "/default");
-	}
-
+	
 	// find model in our list
 	for (i=0; i<s_playermodel.nummodels; i++)
 	{
@@ -494,14 +489,14 @@
 			s_playermodel.selectedmodel = i;
 			s_playermodel.modelpage     = i/MAX_MODELSPERPAGE;
 
-			// separate the model name
+			// seperate the model name
 			maxlen = pdest-buffptr;
 			if (maxlen > 16)
 				maxlen = 16;
 			Q_strncpyz( s_playermodel.modelname.string, buffptr, maxlen );
 			Q_strupr( s_playermodel.modelname.string );
 
-			// separate the skin name
+			// seperate the skin name
 			maxlen = strlen(pdest+5)+1;
 			if (maxlen > 16)
 				maxlen = 16;

```

### `ioquake3`  — sha256 `f7f8f86f6c1b...`, 21684 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_playermodel.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_playermodel.c	2026-04-16 20:02:21.556592700 +0100
@@ -468,12 +468,12 @@
 
 	// model
 	trap_Cvar_VariableStringBuffer( "model", s_playermodel.modelskin, 64 );
-
+	
 	// use default skin if none is set
 	if (!strchr(s_playermodel.modelskin, '/')) {
 		Q_strcat(s_playermodel.modelskin, 64, "/default");
 	}
-
+	
 	// find model in our list
 	for (i=0; i<s_playermodel.nummodels; i++)
 	{

```

### `openarena-engine`  — sha256 `13c7c5b0099f...`, 21684 bytes

_Diff stat: +6 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_playermodel.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_playermodel.c	2026-04-16 22:48:25.897193700 +0100
@@ -339,14 +339,14 @@
 		Q_strncpyz(s_playermodel.modelskin,buffptr,pdest-buffptr+1);
 		strcat(s_playermodel.modelskin,pdest + 5);
 
-		// separate the model name
+		// seperate the model name
 		maxlen = pdest-buffptr;
 		if (maxlen > 16)
 			maxlen = 16;
 		Q_strncpyz( s_playermodel.modelname.string, buffptr, maxlen );
 		Q_strupr( s_playermodel.modelname.string );
 
-		// separate the skin name
+		// seperate the skin name
 		maxlen = strlen(pdest+5)+1;
 		if (maxlen > 16)
 			maxlen = 16;
@@ -468,12 +468,12 @@
 
 	// model
 	trap_Cvar_VariableStringBuffer( "model", s_playermodel.modelskin, 64 );
-
+	
 	// use default skin if none is set
 	if (!strchr(s_playermodel.modelskin, '/')) {
 		Q_strcat(s_playermodel.modelskin, 64, "/default");
 	}
-
+	
 	// find model in our list
 	for (i=0; i<s_playermodel.nummodels; i++)
 	{
@@ -494,14 +494,14 @@
 			s_playermodel.selectedmodel = i;
 			s_playermodel.modelpage     = i/MAX_MODELSPERPAGE;
 
-			// separate the model name
+			// seperate the model name
 			maxlen = pdest-buffptr;
 			if (maxlen > 16)
 				maxlen = 16;
 			Q_strncpyz( s_playermodel.modelname.string, buffptr, maxlen );
 			Q_strupr( s_playermodel.modelname.string );
 
-			// separate the skin name
+			// seperate the skin name
 			maxlen = strlen(pdest+5)+1;
 			if (maxlen > 16)
 				maxlen = 16;

```

### `openarena-gamecode`  — sha256 `3e478678551f...`, 21792 bytes

_Diff stat: +17 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_playermodel.c	2026-04-16 20:02:25.208502600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_playermodel.c	2026-04-16 22:48:24.184499000 +0100
@@ -22,16 +22,16 @@
 //
 #include "ui_local.h"
 
-#define MODEL_BACK0			"menu/art/back_0"
-#define MODEL_BACK1			"menu/art/back_1"
+#define MODEL_BACK0			"menu/" MENU_ART_DIR "/back_0"
+#define MODEL_BACK1			"menu/" MENU_ART_DIR "/back_1"
 #define MODEL_SELECT		"menu/art/opponents_select"
 #define MODEL_SELECTED		"menu/art/opponents_selected"
-#define MODEL_FRAMEL		"menu/art/frame1_l"
-#define MODEL_FRAMER		"menu/art/frame1_r"
-#define MODEL_PORTS			"menu/art/player_models_ports"
-#define MODEL_ARROWS		"menu/art/gs_arrows_0"
-#define MODEL_ARROWSL		"menu/art/gs_arrows_l"
-#define MODEL_ARROWSR		"menu/art/gs_arrows_r"
+#define MODEL_FRAMEL		"menu/" MENU_ART_DIR "/frame1_l"
+#define MODEL_FRAMER		"menu/" MENU_ART_DIR "/frame1_r"
+#define MODEL_PORTS			"menu/" MENU_ART_DIR "/player_models_ports"
+#define MODEL_ARROWS		"menu/" MENU_ART_DIR "/gs_arrows_0"
+#define MODEL_ARROWSL		"menu/" MENU_ART_DIR "/gs_arrows_l"
+#define MODEL_ARROWSR		"menu/" MENU_ART_DIR "/gs_arrows_r"
 
 #define LOW_MEMORY			(5 * 1024 * 1024)
 
@@ -339,14 +339,14 @@
 		Q_strncpyz(s_playermodel.modelskin,buffptr,pdest-buffptr+1);
 		strcat(s_playermodel.modelskin,pdest + 5);
 
-		// separate the model name
+		// seperate the model name
 		maxlen = pdest-buffptr;
 		if (maxlen > 16)
 			maxlen = 16;
 		Q_strncpyz( s_playermodel.modelname.string, buffptr, maxlen );
 		Q_strupr( s_playermodel.modelname.string );
 
-		// separate the skin name
+		// seperate the skin name
 		maxlen = strlen(pdest+5)+1;
 		if (maxlen > 16)
 			maxlen = 16;
@@ -414,7 +414,7 @@
 		
 		if (dirlen && dirptr[dirlen-1]=='/') dirptr[dirlen-1]='\0';
 
-		if (!strcmp(dirptr,".") || !strcmp(dirptr,".."))
+		if (strequals(dirptr,".") || strequals(dirptr,".."))
 			continue;
 			
 		// iterate all skin files in directory
@@ -427,7 +427,7 @@
 			COM_StripExtension(fileptr,skinname, sizeof(skinname));
 
 			// look for icon_????
-			if (!Q_stricmpn(skinname,"icon_",5))
+			if (Q_strequaln(skinname,"icon_",5))
 			{
 				Com_sprintf( s_playermodel.modelnames[s_playermodel.nummodels++],
 					sizeof( s_playermodel.modelnames[s_playermodel.nummodels] ),
@@ -468,12 +468,12 @@
 
 	// model
 	trap_Cvar_VariableStringBuffer( "model", s_playermodel.modelskin, 64 );
-
+	
 	// use default skin if none is set
 	if (!strchr(s_playermodel.modelskin, '/')) {
 		Q_strcat(s_playermodel.modelskin, 64, "/default");
 	}
-
+	
 	// find model in our list
 	for (i=0; i<s_playermodel.nummodels; i++)
 	{
@@ -488,20 +488,20 @@
 		else
 			continue;
 
-		if (!Q_stricmp( s_playermodel.modelskin, modelskin ))
+		if (Q_strequal( s_playermodel.modelskin, modelskin ))
 		{
 			// found pic, set selection here		
 			s_playermodel.selectedmodel = i;
 			s_playermodel.modelpage     = i/MAX_MODELSPERPAGE;
 
-			// separate the model name
+			// seperate the model name
 			maxlen = pdest-buffptr;
 			if (maxlen > 16)
 				maxlen = 16;
 			Q_strncpyz( s_playermodel.modelname.string, buffptr, maxlen );
 			Q_strupr( s_playermodel.modelname.string );
 
-			// separate the skin name
+			// seperate the skin name
 			maxlen = strlen(pdest+5)+1;
 			if (maxlen > 16)
 				maxlen = 16;

```
