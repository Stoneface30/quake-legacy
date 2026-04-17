# Diff: `code/botlib/be_ea.c`
**Canonical:** `wolfcamql-src` (sha256 `f7c8f0b5c233...`, 14139 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `24df56b42e7f...`, 14871 bytes

_Diff stat: +37 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ea.c	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ea.c	2026-04-16 20:02:19.853390000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,16 +29,17 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_memory.h"
 #include "l_script.h"
 #include "l_precomp.h"
 #include "l_struct.h"
-#include "botlib.h"
+#include "../game/botlib.h"
 #include "be_interface.h"
-#include "be_ea.h"
 
 #define MAX_USERMOVE				400
+#define MAX_COMMANDARGUMENTS		10
+#define ACTION_JUMPEDLASTFRAME		128
 
 bot_input_t *botinputs;
 
@@ -414,6 +415,24 @@
 //===========================================================================
 void EA_EndRegular(int client, float thinktime)
 {
+/*
+	bot_input_t *bi;
+	int jumped = qfalse;
+
+	bi = &botinputs[client];
+
+	bi->actionflags &= ~ACTION_JUMPEDLASTFRAME;
+
+	bi->thinktime = thinktime;
+	botimport.BotInput(client, bi);
+
+	bi->thinktime = 0;
+	VectorClear(bi->dir);
+	bi->speed = 0;
+	jumped = bi->actionflags & ACTION_JUMP;
+	bi->actionflags = 0;
+	if (jumped) bi->actionflags |= ACTION_JUMPEDLASTFRAME;
+*/
 } //end of the function EA_EndRegular
 //===========================================================================
 //
@@ -424,10 +443,23 @@
 void EA_GetInput(int client, float thinktime, bot_input_t *input)
 {
 	bot_input_t *bi;
+//	int jumped = qfalse;
 
 	bi = &botinputs[client];
+
+//	bi->actionflags &= ~ACTION_JUMPEDLASTFRAME;
+
 	bi->thinktime = thinktime;
 	Com_Memcpy(input, bi, sizeof(bot_input_t));
+
+	/*
+	bi->thinktime = 0;
+	VectorClear(bi->dir);
+	bi->speed = 0;
+	jumped = bi->actionflags & ACTION_JUMP;
+	bi->actionflags = 0;
+	if (jumped) bi->actionflags |= ACTION_JUMPEDLASTFRAME;
+	*/
 } //end of the function EA_GetInput
 //===========================================================================
 //
@@ -441,6 +473,7 @@
 	int jumped = qfalse;
 
 	bi = &botinputs[client];
+	bi->actionflags &= ~ACTION_JUMPEDLASTFRAME;
 
 	bi->thinktime = 0;
 	VectorClear(bi->dir);

```

### `quake3e`  — sha256 `de6ee3ff61d4...`, 14264 bytes

_Diff stat: +19 / -18 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ea.c	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ea.c	2026-04-16 20:02:26.902995100 +0100
@@ -39,8 +39,9 @@
 #include "be_ea.h"
 
 #define MAX_USERMOVE				400
+#define MAX_COMMANDARGUMENTS		10
 
-bot_input_t *botinputs;
+static bot_input_t *botinputs;
 
 //===========================================================================
 //
@@ -48,9 +49,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EA_Say(int client, char *str)
+void EA_Say( int client, const char *str )
 {
-	botimport.BotClientCommand(client, va("say %s", str) );
+	botimport.BotClientCommand( client, va( "say %s", str ) );
 } //end of the function EA_Say
 //===========================================================================
 //
@@ -58,9 +59,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EA_SayTeam(int client, char *str)
+void EA_SayTeam( int client, const char *str )
 {
-	botimport.BotClientCommand(client, va("say_team %s", str));
+	botimport.BotClientCommand( client, va( "say_team %s", str ) );
 } //end of the function EA_SayTeam
 //===========================================================================
 //
@@ -68,9 +69,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EA_Tell(int client, int clientto, char *str)
+void EA_Tell( int client, int clientto, const char *str )
 {
-	botimport.BotClientCommand(client, va("tell %d, %s", clientto, str));
+	botimport.BotClientCommand( client, va( "tell %d, %s", clientto, str ) );
 } //end of the function EA_SayTeam
 //===========================================================================
 //
@@ -78,9 +79,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EA_UseItem(int client, char *it)
+void EA_UseItem( int client, const char *it )
 {
-	botimport.BotClientCommand(client, va("use %s", it));
+	botimport.BotClientCommand( client, va( "use %s", it ) );
 } //end of the function EA_UseItem
 //===========================================================================
 //
@@ -88,9 +89,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EA_DropItem(int client, char *it)
+void EA_DropItem( int client, const char *it )
 {
-	botimport.BotClientCommand(client, va("drop %s", it));
+	botimport.BotClientCommand( client, va( "drop %s", it ) );
 } //end of the function EA_DropItem
 //===========================================================================
 //
@@ -98,9 +99,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EA_UseInv(int client, char *inv)
+void EA_UseInv( int client, const char *inv )
 {
-	botimport.BotClientCommand(client, va("invuse %s", inv));
+	botimport.BotClientCommand( client, va( "invuse %s", inv ) );
 } //end of the function EA_UseInv
 //===========================================================================
 //
@@ -108,9 +109,9 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void EA_DropInv(int client, char *inv)
+void EA_DropInv( int client, const char *inv )
 {
-	botimport.BotClientCommand(client, va("invdrop %s", inv));
+	botimport.BotClientCommand( client, va( "invdrop %s", inv ) );
 } //end of the function EA_DropInv
 //===========================================================================
 //
@@ -132,9 +133,9 @@
 // Returns:					-
 // Changes Globals:		-
 //===========================================================================
-void EA_Command(int client, char *command)
+void EA_Command( int client, const char *command )
 {
-	botimport.BotClientCommand(client, command);
+	botimport.BotClientCommand( client, command );
 } //end of the function EA_Command
 //===========================================================================
 //
@@ -438,7 +439,7 @@
 void EA_ResetInput(int client)
 {
 	bot_input_t *bi;
-	int jumped = qfalse;
+	int jumped;
 
 	bi = &botinputs[client];
 

```

### `openarena-engine`  — sha256 `1eff911848d3...`, 14173 bytes

_Diff stat: +1 / -0 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ea.c	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ea.c	2026-04-16 22:48:25.716695400 +0100
@@ -39,6 +39,7 @@
 #include "be_ea.h"
 
 #define MAX_USERMOVE				400
+#define MAX_COMMANDARGUMENTS		10
 
 bot_input_t *botinputs;
 

```
