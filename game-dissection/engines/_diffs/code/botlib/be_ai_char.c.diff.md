# Diff: `code/botlib/be_ai_char.c`
**Canonical:** `wolfcamql-src` (sha256 `c340e51c5cbb...`, 23902 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `8abfc14bf33f...`, 23958 bytes

_Diff stat: +21 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_char.c	2026-04-16 20:02:25.121907000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ai_char.c	2026-04-16 20:02:19.850388800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,7 +29,7 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "l_log.h"
 #include "l_memory.h"
 #include "l_utils.h"
@@ -38,11 +38,11 @@
 #include "l_struct.h"
 #include "l_libvar.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
-#include "be_ai_char.h"
+#include "../game/be_ai_char.h"
 
 #define MAX_CHARACTERISTICS		80
 
@@ -106,8 +106,8 @@
 {
 	int i;
 
-	Log_Write("%s\n", ch->filename);
-	Log_Write("skill %.1f\n", ch->skill);
+	Log_Write("%s", ch->filename);
+	Log_Write("skill %d\n", ch->skill);
 	Log_Write("{\n");
 	for (i = 0; i < MAX_CHARACTERISTICS; i++)
 	{
@@ -222,7 +222,7 @@
 	source = LoadSourceFile(charfile);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", charfile);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", charfile);
 		return NULL;
 	} //end if
 	ch = (bot_character_t *) GetClearedMemory(sizeof(bot_character_t) +
@@ -247,7 +247,7 @@
 				return NULL;
 			} //end if
 			//if it's the correct skill
-			if (skill < 0 || (int)token.intvalue == skill)
+			if (skill < 0 || token.intvalue == skill)
 			{
 				foundcharacter = qtrue;
 				ch->skill = token.intvalue;
@@ -256,7 +256,7 @@
 					if (!strcmp(token.string, "}")) break;
 					if (token.type != TT_NUMBER || !(token.subtype & TT_INTEGER))
 					{
-						SourceError(source, "expected integer index, found %s", token.string);
+						SourceError(source, "expected integer index, found %s\n", token.string);
 						FreeSource(source);
 						BotFreeCharacterStrings(ch);
 						FreeMemory(ch);
@@ -265,7 +265,7 @@
 					index = token.intvalue;
 					if (index < 0 || index > MAX_CHARACTERISTICS)
 					{
-						SourceError(source, "characteristic index out of range [0, %d]", MAX_CHARACTERISTICS);
+						SourceError(source, "characteristic index out of range [0, %d]\n", MAX_CHARACTERISTICS);
 						FreeSource(source);
 						BotFreeCharacterStrings(ch);
 						FreeMemory(ch);
@@ -273,7 +273,7 @@
 					} //end if
 					if (ch->c[index].type)
 					{
-						SourceError(source, "characteristic %d already initialized", index);
+						SourceError(source, "characteristic %d already initialized\n", index);
 						FreeSource(source);
 						BotFreeCharacterStrings(ch);
 						FreeMemory(ch);
@@ -308,7 +308,7 @@
 					} //end else if
 					else
 					{
-						SourceError(source, "expected integer, float or string, found %s", token.string);
+						SourceError(source, "expected integer, float or string, found %s\n", token.string);
 						FreeSource(source);
 						BotFreeCharacterStrings(ch);
 						FreeMemory(ch);
@@ -336,7 +336,7 @@
 		} //end if
 		else
 		{
-			SourceError(source, "unknown definition %s", token.string);
+			SourceError(source, "unknown definition %s\n", token.string);
 			FreeSource(source);
 			BotFreeCharacterStrings(ch);
 			FreeMemory(ch);
@@ -416,7 +416,7 @@
 		//
 		botimport.Print(PRT_MESSAGE, "loaded skill %d from %s\n", intskill, charfile);
 #ifdef DEBUG
-		if (botDeveloper)
+		if (bot_developer)
 		{
 			botimport.Print(PRT_MESSAGE, "skill %d loaded in %d msec from %s\n", intskill, Sys_MilliSeconds() - starttime, charfile);
 		} //end if
@@ -713,7 +713,7 @@
 	} //end else if
 	else
 	{
-		botimport.Print(PRT_ERROR, "characteristic %d is not an integer\n", index);
+		botimport.Print(PRT_ERROR, "characteristic %d is not a integer\n", index);
 		return 0;
 	} //end else if
 //	return 0;
@@ -758,12 +758,16 @@
 	//an integer will be converted to a float
 	if (ch->c[index].type == CT_STRING)
 	{
-		Q_strncpyz(buf, ch->c[index].value.string, size);
+		strncpy(buf, ch->c[index].value.string, size-1);
+		buf[size-1] = '\0';
+		return;
 	} //end if
 	else
 	{
 		botimport.Print(PRT_ERROR, "characteristic %d is not a string\n", index);
+		return;
 	} //end else if
+	return;
 } //end of the function Characteristic_String
 //===========================================================================
 //

```

### `quake3e`  — sha256 `2e9b7980ed96...`, 26191 bytes

_Diff stat: +158 / -48 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_char.c	2026-04-16 20:02:25.121907000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_char.c	2026-04-16 20:02:26.898996600 +0100
@@ -69,12 +69,16 @@
 //a bot character
 typedef struct bot_character_s
 {
+	bot_characteristic_t c[MAX_CHARACTERISTICS];
 	char filename[MAX_QPATH];
 	float skill;
-	bot_characteristic_t c[1];		//variable sized
+	int refcnt;
+	int reftime;
 } bot_character_t;
 
-bot_character_t *botcharacters[MAX_CLIENTS + 1];
+#define MAX_HANDLES (MAX_CLIENTS*2)
+
+bot_character_t *botcharacters[MAX_HANDLES + 1];
 
 //========================================================================
 //
@@ -82,9 +86,9 @@
 // Returns:				-
 // Changes Globals:		-
 //========================================================================
-bot_character_t *BotCharacterFromHandle(int handle)
+static bot_character_t *BotCharacterFromHandle(int handle)
 {
-	if (handle <= 0 || handle > MAX_CLIENTS)
+	if (handle <= 0 || handle > MAX_HANDLES)
 	{
 		botimport.Print(PRT_FATAL, "character handle %d out of range\n", handle);
 		return NULL;
@@ -102,7 +106,30 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void BotDumpCharacter(bot_character_t *ch)
+static bot_character_t *BotReferenceHandle( int handle, int refmod )
+{
+	bot_character_t *ch;
+
+	if ( handle > 0 && handle <= MAX_HANDLES )
+	{
+		ch = botcharacters[ handle ];
+		if ( ch )
+		{
+			ch->refcnt += refmod;
+			if ( ch->refcnt == 0 )
+				ch->reftime = botimport.Sys_Milliseconds();
+		}
+	}
+
+	return NULL;
+}
+//===========================================================================
+//
+// Parameter:			-
+// Returns:				-
+// Changes Globals:		-
+//===========================================================================
+static void BotDumpCharacter( const bot_character_t *ch )
 {
 	int i;
 
@@ -126,7 +153,7 @@
 // Returns:				-
 // Changes Globals:		-
 //========================================================================
-void BotFreeCharacterStrings(bot_character_t *ch)
+static void BotFreeCharacterStrings(bot_character_t *ch)
 {
 	int i;
 
@@ -144,9 +171,9 @@
 // Returns:				-
 // Changes Globals:		-
 //========================================================================
-void BotFreeCharacter2(int handle)
+static void BotFreeCharacter2(int handle)
 {
-	if (handle <= 0 || handle > MAX_CLIENTS)
+	if (handle <= 0 || handle > MAX_HANDLES)
 	{
 		botimport.Print(PRT_FATAL, "character handle %d out of range\n", handle);
 		return;
@@ -166,18 +193,72 @@
 // Returns:				-
 // Changes Globals:		-
 //========================================================================
-void BotFreeCharacter(int handle)
+void BotFreeCharacter( int handle )
 {
-	if (!LibVarGetValue("bot_reloadcharacters")) return;
-	BotFreeCharacter2(handle);
+	bot_character_t *ch;
+
+	ch = BotCharacterFromHandle( handle );
+	if ( ch )
+	{
+		if ( ch->refcnt > 0 )
+			ch->refcnt--;
+		//else
+		//	botimport.Print( PRT_FATAL, "INVALID REFERENCE COUNT FOR HANDLE %d\n", handle );
+
+		if ( ch->refcnt )
+			return; // we can't release referenced characters
+	}
+	else
+		return;
+
+	if ( !LibVarGetValue( "bot_reloadcharacters" ) )
+		return;
+
+	BotFreeCharacter2( handle );
 } //end of the function BotFreeCharacter
+//========================================================================
+//
+// Parameter:			-
+// Returns:				-
+// Changes Globals:		-
+//========================================================================
+static int BotReleaseUnreferencedHandle( void )
+{
+	const bot_character_t *ch;
+	int handle, now, t, r;
+
+	r = t = 0;
+	now = botimport.Sys_Milliseconds();
+	for ( handle = 1; handle <= MAX_HANDLES; handle++ )
+	{
+		ch = botcharacters[ handle ];
+		if ( ch && ch->refcnt == 0 )
+		{
+			if ( r == 0 || now - ch->reftime > t )
+			{
+				t = now - ch->reftime;
+				r = handle;
+			}
+		}
+	}
+
+	if ( r != 0 )
+	{
+		BotFreeCharacter2( r );
+		return r;
+	}
+
+	return 0;
+}
+
+
 //===========================================================================
 //
 // Parameter:			-
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-void BotDefaultCharacteristics(bot_character_t *ch, bot_character_t *defaultch)
+static void BotDefaultCharacteristics(bot_character_t *ch, bot_character_t *defaultch)
 {
 	int i;
 
@@ -209,7 +290,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-bot_character_t *BotLoadCharacterFromFile(char *charfile, int skill)
+static bot_character_t *BotLoadCharacterFromFile(const char *charfile, int skill)
 {
 	int indent, index, foundcharacter;
 	bot_character_t *ch;
@@ -224,11 +305,12 @@
 	{
 		botimport.Print(PRT_ERROR, "couldn't load %s\n", charfile);
 		return NULL;
-	} //end if
-	ch = (bot_character_t *) GetClearedMemory(sizeof(bot_character_t) +
-					MAX_CHARACTERISTICS * sizeof(bot_characteristic_t));
-	strcpy(ch->filename, charfile);
-	while(PC_ReadToken(source, &token))
+	}
+
+	ch = (bot_character_t *) GetClearedMemory( sizeof( *ch ) );
+	Q_strncpyz( ch->filename, charfile, sizeof( ch->filename ) );
+
+	while(PC_ReadToken( source, &token))
 	{
 		if (!strcmp(token.string, "skill"))
 		{
@@ -263,7 +345,7 @@
 						return NULL;
 					} //end if
 					index = token.intvalue;
-					if (index < 0 || index > MAX_CHARACTERISTICS)
+					if (index < 0 || index >= MAX_CHARACTERISTICS)
 					{
 						SourceError(source, "characteristic index out of range [0, %d]", MAX_CHARACTERISTICS);
 						FreeSource(source);
@@ -359,15 +441,15 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int BotFindCachedCharacter(char *charfile, float skill)
+static int BotFindCachedCharacter(const char *charfile, float skill)
 {
 	int handle;
 
-	for (handle = 1; handle <= MAX_CLIENTS; handle++)
+	for (handle = 1; handle <= MAX_HANDLES; handle++)
 	{
 		if ( !botcharacters[handle] ) continue;
 		if ( strcmp( botcharacters[handle]->filename, charfile ) == 0 &&
-			(skill < 0 || fabs(botcharacters[handle]->skill - skill) < 0.01) )
+			(skill < 0.0f || fabsf(botcharacters[handle]->skill - skill) < 0.01f) )
 		{
 			return handle;
 		} //end if
@@ -380,7 +462,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int BotLoadCachedCharacter(char *charfile, float skill, int reload)
+static int BotLoadCachedCharacter(const char *charfile, float skill, int reload)
 {
 	int handle, cachedhandle, intskill;
 	bot_character_t *ch = NULL;
@@ -391,11 +473,18 @@
 #endif //DEBUG
 
 	//find a free spot for a character
-	for (handle = 1; handle <= MAX_CLIENTS; handle++)
+	for (handle = 1; handle <= MAX_HANDLES; handle++)
 	{
 		if (!botcharacters[handle]) break;
 	} //end for
-	if (handle > MAX_CLIENTS) return 0;
+
+	if ( handle > MAX_HANDLES )
+	{
+		handle = BotReleaseUnreferencedHandle();
+		if ( !handle )
+			return 0;
+	}
+
 	//try to load a cached character with the given skill
 	if (!reload)
 	{
@@ -407,7 +496,7 @@
 		} //end if
 	} //end else
 	//
-	intskill = (int) (skill + 0.5);
+	intskill = (int) (skill + 0.5f);
 	//try to load the character with the given skill
 	ch = BotLoadCharacterFromFile(charfile, intskill);
 	if (ch)
@@ -493,18 +582,21 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int BotLoadCharacterSkill(char *charfile, float skill)
+static int BotLoadCharacterSkill(const char *charfile, float skill)
 {
 	int ch, defaultch;
 
-	defaultch = BotLoadCachedCharacter(DEFAULT_CHARACTER, skill, qfalse);
-	ch = BotLoadCachedCharacter(charfile, skill, LibVarGetValue("bot_reloadcharacters"));
+	defaultch = BotLoadCachedCharacter( DEFAULT_CHARACTER, skill, qfalse );
+	BotReferenceHandle( defaultch, 1 );
+	ch = BotLoadCachedCharacter( charfile, skill, LibVarGetValue( "bot_reloadcharacters" ) );
+	BotReferenceHandle( ch, 1 );
 
 	if (defaultch && ch)
 	{
 		BotDefaultCharacteristics(botcharacters[ch], botcharacters[defaultch]);
 	} //end if
 
+	BotReferenceHandle( defaultch, -1 );
 	return ch;
 } //end of the function BotLoadCharacterSkill
 //===========================================================================
@@ -513,43 +605,53 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int BotInterpolateCharacters(int handle1, int handle2, float desiredskill)
+static int BotInterpolateCharacters(int handle1, int handle2, float desiredskill)
 {
 	bot_character_t *ch1, *ch2, *out;
 	int i, handle;
-	float scale;
+	float scale, v1, v2;
 
 	ch1 = BotCharacterFromHandle(handle1);
 	ch2 = BotCharacterFromHandle(handle2);
 	if (!ch1 || !ch2)
 		return 0;
 	//find a free spot for a character
-	for (handle = 1; handle <= MAX_CLIENTS; handle++)
+	for (handle = 1; handle <= MAX_HANDLES; handle++)
 	{
 		if (!botcharacters[handle]) break;
 	} //end for
-	if (handle > MAX_CLIENTS) return 0;
-	out = (bot_character_t *) GetClearedMemory(sizeof(bot_character_t) +
-					MAX_CHARACTERISTICS * sizeof(bot_characteristic_t));
+
+	if ( handle > MAX_HANDLES )
+	{
+		handle = BotReleaseUnreferencedHandle();
+		if ( !handle )
+			return 0;
+	}
+
+	out = (bot_character_t *) GetClearedMemory( sizeof( *out ) );
 	out->skill = desiredskill;
-	strcpy(out->filename, ch1->filename);
+	Q_strncpyz( out->filename, ch1->filename, sizeof( out->filename ) );
 	botcharacters[handle] = out;
 
 	scale = (float) (desiredskill - ch1->skill) / (ch2->skill - ch1->skill);
 	for (i = 0; i < MAX_CHARACTERISTICS; i++)
 	{
-		//
-		if (ch1->c[i].type == CT_FLOAT && ch2->c[i].type == CT_FLOAT)
+		if (ch1->c[i].type == CT_FLOAT && (ch2->c[i].type == CT_FLOAT || ch2->c[i].type == CT_INTEGER) )
 		{
 			out->c[i].type = CT_FLOAT;
-			out->c[i].value._float = ch1->c[i].value._float +
-								(ch2->c[i].value._float - ch1->c[i].value._float) * scale;
-		} //end if
+			v1 = ch1->c[i].value._float;
+			// convert second value from integer to float
+			if ( ch2->c[i].type == CT_INTEGER )
+				v2 = ch2->c[i].value.integer;
+			else
+				v2 = ch2->c[i].value._float;
+			out->c[i].value._float = v1 + (v2 - v1) * scale;
+		}
 		else if (ch1->c[i].type == CT_INTEGER)
 		{
 			out->c[i].type = CT_INTEGER;
 			out->c[i].value.integer = ch1->c[i].value.integer;
-		} //end else if
+		}
 		else if (ch1->c[i].type == CT_STRING)
 		{
 			out->c[i].type = CT_STRING;
@@ -565,7 +667,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int BotLoadCharacter(char *charfile, float skill)
+int BotLoadCharacter(const char *charfile, float skill)
 {
 	int firstskill, secondskill, handle;
 
@@ -582,6 +684,7 @@
 	if (handle)
 	{
 		botimport.Print(PRT_MESSAGE, "loaded cached skill %f from %s\n", skill, charfile);
+		BotReferenceHandle( handle, 1 );
 		return handle;
 	} //end if
 	if (skill < 4.0)
@@ -601,8 +704,15 @@
 		if (!secondskill) return firstskill;
 	} //end else
 	//interpolate between the two skills
-	handle = BotInterpolateCharacters(firstskill, secondskill, skill);
-	if (!handle) return 0;
+	handle = BotInterpolateCharacters( firstskill, secondskill, skill );
+	BotReferenceHandle( firstskill, -1 );
+	BotReferenceHandle( secondskill, -1 );
+
+	if ( !handle )
+		return 0;
+
+	BotReferenceHandle( handle, 1 );
+
 	//write the character to the log file
 	BotDumpCharacter(botcharacters[handle]);
 	//
@@ -614,7 +724,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int CheckCharacteristicIndex(int character, int index)
+static int CheckCharacteristicIndex(int character, int index)
 {
 	bot_character_t *ch;
 
@@ -758,7 +868,7 @@
 	//an integer will be converted to a float
 	if (ch->c[index].type == CT_STRING)
 	{
-		Q_strncpyz(buf, ch->c[index].value.string, size);
+		Q_strncpyz( buf, ch->c[index].value.string, size );
 	} //end if
 	else
 	{
@@ -775,7 +885,7 @@
 {
 	int handle;
 
-	for (handle = 1; handle <= MAX_CLIENTS; handle++)
+	for (handle = 1; handle <= MAX_HANDLES; handle++)
 	{
 		if (botcharacters[handle])
 		{

```

### `openarena-engine`  — sha256 `3ccdbbf2a6a9...`, 23920 bytes

_Diff stat: +4 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_char.c	2026-04-16 20:02:25.121907000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_char.c	2026-04-16 22:48:25.712695500 +0100
@@ -222,7 +222,7 @@
 	source = LoadSourceFile(charfile);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", charfile);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", charfile);
 		return NULL;
 	} //end if
 	ch = (bot_character_t *) GetClearedMemory(sizeof(bot_character_t) +
@@ -247,7 +247,7 @@
 				return NULL;
 			} //end if
 			//if it's the correct skill
-			if (skill < 0 || (int)token.intvalue == skill)
+			if (skill < 0 || token.intvalue == skill)
 			{
 				foundcharacter = qtrue;
 				ch->skill = token.intvalue;
@@ -758,7 +758,8 @@
 	//an integer will be converted to a float
 	if (ch->c[index].type == CT_STRING)
 	{
-		Q_strncpyz(buf, ch->c[index].value.string, size);
+		strncpy(buf, ch->c[index].value.string, size-1);
+		buf[size-1] = '\0';
 	} //end if
 	else
 	{

```
