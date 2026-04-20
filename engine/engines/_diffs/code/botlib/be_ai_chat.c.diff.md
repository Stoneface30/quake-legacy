# Diff: `code/botlib/be_ai_chat.c`
**Canonical:** `wolfcamql-src` (sha256 `fafe4f20275e...`, 89890 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `839aa978c2c5...`, 89573 bytes

_Diff stat: +67 / -81 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_chat.c	2026-04-16 20:02:25.122907200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ai_chat.c	2026-04-16 20:02:19.851388600 +0100
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
 #include "l_memory.h"
 #include "l_libvar.h"
 #include "l_script.h"
@@ -38,12 +38,12 @@
 #include "l_utils.h"
 #include "l_log.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
-#include "be_ea.h"
-#include "be_ai_chat.h"
+#include "../game/be_ea.h"
+#include "../game/be_ai_chat.h"
 
 
 //escape character
@@ -342,7 +342,7 @@
 	m->handle = cs->handle;
 	m->time = AAS_Time();
 	m->type = type;
-	Q_strncpyz(m->message, message, MAX_MESSAGE_SIZE);
+	strncpy(m->message, message, MAX_MESSAGE_SIZE);
 	m->next = NULL;
 	if (cs->lastmessage)
 	{
@@ -367,26 +367,13 @@
 int BotNextConsoleMessage(int chatstate, bot_consolemessage_t *cm)
 {
 	bot_chatstate_t *cs;
-	bot_consolemessage_t *firstmsg;
 
 	cs = BotChatStateFromHandle(chatstate);
 	if (!cs) return 0;
-	if ((firstmsg = cs->firstmessage))
+	if (cs->firstmessage)
 	{
-		cm->handle = firstmsg->handle;
-		cm->time = firstmsg->time;
-		cm->type = firstmsg->type;
-		Q_strncpyz(cm->message, firstmsg->message,
-			   sizeof(cm->message));
-		
-		/* We omit setting the two pointers in cm because pointer
-		 * size in the VM differs between the size in the engine on
-		 * 64 bit machines, which would lead to a buffer overflow if
-		 * this functions is called from the VM. The pointers are
-		 * of no interest to functions calling
-		 * BotNextConsoleMessage anyways.
-		 */
-		
+		Com_Memcpy(cm, cs->firstmessage, sizeof(bot_consolemessage_t));
+		cm->next = cm->prev = NULL;
 		return cm->handle;
 	} //end if
 	return 0;
@@ -553,11 +540,11 @@
 
 	//find the synonym in the string
 	str = StringContainsWord(string, synonym, qfalse);
-	//if the synonym occurred in the string
+	//if the synonym occured in the string
 	while(str)
 	{
 		//if the synonym isn't part of the replacement which is already in the string
-		//useful for abbreviations
+		//usefull for abreviations
 		str2 = StringContainsWord(string, replacement, qfalse);
 		while(str2)
 		{
@@ -629,7 +616,7 @@
 		source = LoadSourceFile(filename);
 		if (!source)
 		{
-			botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+			botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 			return NULL;
 		} //end if
 		//
@@ -673,7 +660,7 @@
 				else if (!strcmp(token.string, "["))
 				{
 					size += sizeof(bot_synonymlist_t);
-					if (pass && ptr)
+					if (pass)
 					{
 						syn = (bot_synonymlist_t *) ptr;
 						ptr += sizeof(bot_synonymlist_t);
@@ -688,7 +675,6 @@
 					lastsynonym = NULL;
 					while(1)
 					{
-						size_t len;
 						if (!PC_ExpectTokenString(source, "(") ||
 							!PC_ExpectTokenType(source, TT_STRING, 0, &token))
 						{
@@ -698,19 +684,17 @@
 						StripDoubleQuotes(token.string);
 						if (strlen(token.string) <= 0)
 						{
-							SourceError(source, "empty string");
+							SourceError(source, "empty string", token.string);
 							FreeSource(source);
 							return NULL;
 						} //end if
-						len = strlen(token.string) + 1;
-						len = PAD(len, sizeof(long));
-						size += sizeof(bot_synonym_t) + len;
-						if (pass && ptr)
+						size += sizeof(bot_synonym_t) + strlen(token.string) + 1;
+						if (pass)
 						{
 							synonym = (bot_synonym_t *) ptr;
 							ptr += sizeof(bot_synonym_t);
 							synonym->string = ptr;
-							ptr += len;
+							ptr += strlen(token.string) + 1;
 							strcpy(synonym->string, token.string);
 							//
 							if (lastsynonym) lastsynonym->next = synonym;
@@ -725,7 +709,7 @@
 							FreeSource(source);
 							return NULL;
 						} //end if
-						if (pass && ptr)
+						if (pass)
 						{
 							synonym->weight = token.floatvalue;
 							syn->totalweight += synonym->weight;
@@ -739,7 +723,7 @@
 					} //end while
 					if (numsynonyms < 2)
 					{
-						SourceError(source, "synonym must have at least two entries");
+						SourceError(source, "synonym must have at least two entries\n");
 						FreeSource(source);
 						return NULL;
 					} //end if
@@ -844,6 +828,7 @@
 			if (!(syn->context & context)) continue;
 			for (synonym = syn->firstsynonym->next; synonym; synonym = synonym->next)
 			{
+				str2 = synonym->string;
 				//if the synonym is not at the front of the string continue
 				str2 = StringContainsWord(str1, synonym->string, qfalse);
 				if (!str2 || str2 != str1) continue;
@@ -891,7 +876,7 @@
 			StripDoubleQuotes(token.string);
 			if (strlen(ptr) + strlen(token.string) + 1 > MAX_MESSAGE_SIZE)
 			{
-				SourceError(source, "chat message too long");
+				SourceError(source, "chat message too long\n");
 				return qfalse;
 			} //end if
 			strcat(ptr, token.string);
@@ -901,7 +886,7 @@
 		{
 			if (strlen(ptr) + 7 > MAX_MESSAGE_SIZE)
 			{
-				SourceError(source, "chat message too long");
+				SourceError(source, "chat message too long\n");
 				return qfalse;
 			} //end if
 			sprintf(&ptr[strlen(ptr)], "%cv%ld%c", ESCAPE_CHAR, token.intvalue, ESCAPE_CHAR);
@@ -911,14 +896,14 @@
 		{
 			if (strlen(ptr) + 7 > MAX_MESSAGE_SIZE)
 			{
-				SourceError(source, "chat message too long");
+				SourceError(source, "chat message too long\n");
 				return qfalse;
 			} //end if
 			sprintf(&ptr[strlen(ptr)], "%cr%s%c", ESCAPE_CHAR, token.string, ESCAPE_CHAR);
 		} //end else if
 		else
 		{
-			SourceError(source, "unknown message component %s", token.string);
+			SourceError(source, "unknown message component %s\n", token.string);
 			return qfalse;
 		} //end else
 		if (PC_CheckTokenString(source, ";")) break;
@@ -984,7 +969,7 @@
 		source = LoadSourceFile(filename);
 		if (!source)
 		{
-			botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+			botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 			return NULL;
 		} //end if
 		//
@@ -993,22 +978,19 @@
 		//
 		while(PC_ReadToken(source, &token))
 		{
-			size_t len;
 			if (token.type != TT_NAME)
 			{
 				SourceError(source, "unknown random %s", token.string);
 				FreeSource(source);
 				return NULL;
 			} //end if
-			len = strlen(token.string) + 1;
-			len = PAD(len, sizeof(long));
-			size += sizeof(bot_randomlist_t) + len;
-			if (pass && ptr)
+			size += sizeof(bot_randomlist_t) + strlen(token.string) + 1;
+			if (pass)
 			{
 				random = (bot_randomlist_t *) ptr;
 				ptr += sizeof(bot_randomlist_t);
 				random->string = ptr;
-				ptr += len;
+				ptr += strlen(token.string) + 1;
 				strcpy(random->string, token.string);
 				random->firstrandomstring = NULL;
 				random->numstrings = 0;
@@ -1030,15 +1012,13 @@
 					FreeSource(source);
 					return NULL;
 				} //end if
-				len = strlen(chatmessagestring) + 1;
-				len = PAD(len, sizeof(long));
-				size += sizeof(bot_randomstring_t) + len;
-				if (pass && ptr)
+				size += sizeof(bot_randomstring_t) + strlen(chatmessagestring) + 1;
+				if (pass)
 				{
 					randomstring = (bot_randomstring_t *) ptr;
 					ptr += sizeof(bot_randomstring_t);
 					randomstring->string = ptr;
-					ptr += len;
+					ptr += strlen(chatmessagestring) + 1;
 					strcpy(randomstring->string, chatmessagestring);
 					//
 					random->numstrings++;
@@ -1172,16 +1152,16 @@
 	{
 		if (token.type == TT_NUMBER && (token.subtype & TT_INTEGER))
 		{
-			if (token.intvalue >= MAX_MATCHVARIABLES)
+			if (token.intvalue < 0 || token.intvalue >= MAX_MATCHVARIABLES)
 			{
-				SourceError(source, "can't have more than %d match variables", MAX_MATCHVARIABLES);
+				SourceError(source, "can't have more than %d match variables\n", MAX_MATCHVARIABLES);
 				FreeSource(source);
 				BotFreeMatchPieces(firstpiece);
 				return NULL;
 			} //end if
 			if (lastwasvariable)
 			{
-				SourceError(source, "not allowed to have adjacent variables");
+				SourceError(source, "not allowed to have adjacent variables\n");
 				FreeSource(source);
 				BotFreeMatchPieces(firstpiece);
 				return NULL;
@@ -1237,7 +1217,7 @@
 		} //end if
 		else
 		{
-			SourceError(source, "invalid token %s", token.string);
+			SourceError(source, "invalid token %s\n", token.string);
 			FreeSource(source);
 			BotFreeMatchPieces(firstpiece);
 			return NULL;
@@ -1286,7 +1266,7 @@
 	source = LoadSourceFile(matchfile);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", matchfile);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", matchfile);
 		return NULL;
 	} //end if
 	//
@@ -1297,7 +1277,7 @@
 	{
 		if (token.type != TT_NUMBER || !(token.subtype & TT_INTEGER))
 		{
-			SourceError(source, "expected integer, found %s", token.string);
+			SourceError(source, "expected integer, found %s\n", token.string);
 			BotFreeMatchTemplates(matches);
 			FreeSource(source);
 			return NULL;
@@ -1437,7 +1417,7 @@
 		//if the last piece was a variable string
 		if (lastvariable >= 0)
 		{
-        		assert( match->variables[lastvariable].offset >= 0 );
+        		assert( match->variables[lastvariable].offset >= 0 ); // bk001204
 			match->variables[lastvariable].length =
 				strlen(&match->string[ (int) match->variables[lastvariable].offset]);
 		} //end if
@@ -1456,7 +1436,7 @@
 	int i;
 	bot_matchtemplate_t *ms;
 
-	Q_strncpyz(match->string, str, MAX_MESSAGE_SIZE);
+	strncpy(match->string, str, MAX_MESSAGE_SIZE);
 	//remove any trailing enters
 	while(strlen(match->string) &&
 			match->string[strlen(match->string)-1] == '\n')
@@ -1498,13 +1478,15 @@
 	{
 		if (match->variables[variable].length < size)
 			size = match->variables[variable].length+1;
-		assert( match->variables[variable].offset >= 0 );
-		Q_strncpyz(buf, &match->string[ (int) match->variables[variable].offset], size);
+		assert( match->variables[variable].offset >= 0 ); // bk001204
+		strncpy(buf, &match->string[ (int) match->variables[variable].offset], size-1);
+		buf[size-1] = '\0';
 	} //end if
 	else
 	{
 		strcpy(buf, "");
 	} //end else
+	return;
 } //end of the function BotMatchVariable
 //===========================================================================
 //
@@ -1857,7 +1839,7 @@
 	source = LoadSourceFile(filename);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 		return NULL;
 	} //end if
 	//
@@ -1988,7 +1970,7 @@
 	botimport.Print(PRT_MESSAGE, "loaded %s\n", filename);
 	//
 	//BotDumpReplyChat(replychatlist);
-	if (botDeveloper)
+	if (bot_developer)
 	{
 		BotCheckReplyChatIntegrety(replychatlist);
 	} //end if
@@ -2056,7 +2038,7 @@
 		source = LoadSourceFile(chatfile);
 		if (!source)
 		{
-			botimport.Print(PRT_ERROR, "couldn't load %s\n", chatfile);
+			botimport.Print(PRT_ERROR, "counldn't load %s\n", chatfile);
 			return NULL;
 		} //end if
 		//chat structure
@@ -2077,7 +2059,7 @@
 					return NULL;
 				} //end if
 				StripDoubleQuotes(token.string);
-				//after the chat name we expect an opening brace
+				//after the chat name we expect a opening brace
 				if (!PC_ExpectTokenString(source, "{"))
 				{
 					FreeSource(source);
@@ -2098,7 +2080,7 @@
 						if (!strcmp(token.string, "}")) break;
 						if (strcmp(token.string, "type"))
 						{
-							SourceError(source, "expected type found %s", token.string);
+							SourceError(source, "expected type found %s\n", token.string);
 							FreeSource(source);
 							return NULL;
 						} //end if
@@ -2110,10 +2092,10 @@
 							return NULL;
 						} //end if
 						StripDoubleQuotes(token.string);
-						if (pass && ptr)
+						if (pass)
 						{
 							chattype = (bot_chattype_t *) ptr;
-							Q_strncpyz(chattype->name, token.string, MAX_CHATTYPE_NAME);
+							strncpy(chattype->name, token.string, MAX_CHATTYPE_NAME);
 							chattype->firstchatmessage = NULL;
 							//add the chat type to the chat
 							chattype->next = chat->types;
@@ -2125,15 +2107,12 @@
 						//read the chat messages
 						while(!PC_CheckTokenString(source, "}"))
 						{
-							size_t len;
 							if (!BotLoadChatMessage(source, chatmessagestring))
 							{
 								FreeSource(source);
 								return NULL;
 							} //end if
-							len = strlen(chatmessagestring) + 1;
-							len = PAD(len, sizeof(long));
-							if (pass && ptr)
+							if (pass)
 							{
 								chatmessage = (bot_chatmessage_t *) ptr;
 								chatmessage->time = -2*CHATMESSAGE_RECENTTIME;
@@ -2144,11 +2123,11 @@
 								ptr += sizeof(bot_chatmessage_t);
 								chatmessage->chatmessage = ptr;
 								strcpy(chatmessage->chatmessage, chatmessagestring);
-								ptr += len;
+								ptr += strlen(chatmessagestring) + 1;
 								//the number of chat messages increased
 								chattype->numchatmessages++;
 							} //end if
-							size += sizeof(bot_chatmessage_t) + len;
+							size += sizeof(bot_chatmessage_t) + strlen(chatmessagestring) + 1;
 						} //end if
 					} //end while
 				} //end if
@@ -2169,7 +2148,7 @@
 			} //end if
 			else
 			{
-				SourceError(source, "unknown definition %s", token.string);
+				SourceError(source, "unknown definition %s\n", token.string);
 				FreeSource(source);
 				return NULL;
 			} //end else
@@ -2187,14 +2166,14 @@
 	botimport.Print(PRT_MESSAGE, "loaded %s from %s\n", chatname, chatfile);
 	//
 	//BotDumpInitialChat(chat);
-	if (botDeveloper)
+	if (bot_developer)
 	{
 		BotCheckInitialChatIntegrety(chat);
 	} //end if
 #ifdef DEBUG
 	botimport.Print(PRT_MESSAGE, "initial chats loaded in %d msec\n", Sys_MilliSeconds() - starttime);
 #endif //DEBUG
-	//character was read successfully
+	//character was read succesfully
 	return chat;
 } //end of the function BotLoadInitialChat
 //===========================================================================
@@ -2312,7 +2291,7 @@
 					} //end if
 					if (match->variables[num].offset >= 0)
 					{
-					        assert( match->variables[num].offset >= 0 );
+					        assert( match->variables[num].offset >= 0 ); // bk001204
 						ptr = &match->string[ (int) match->variables[num].offset];
 						for (i = 0; i < match->variables[num].length; i++)
 						{
@@ -2580,6 +2559,7 @@
 		strcat(match.string, var7);
 		match.variables[7].offset = index;
 		match.variables[7].length = strlen(var7);
+		index += strlen(var7);
 	}
  	//
 	BotConstructChatMessage(cs, message, mcontext, &match, 0, qfalse);
@@ -2762,6 +2742,7 @@
 			strcat(bestmatch.string, var7);
 			bestmatch.variables[7].offset = index;
 			bestmatch.variables[7].length = strlen(var7);
+			index += strlen(var7);
 		}
 		if (LibVarGetValue("bot_testrchat"))
 		{
@@ -2845,7 +2826,8 @@
 	if (!cs) return;
 
 	BotRemoveTildes(cs->chatmessage);
-	Q_strncpyz(buf, cs->chatmessage, size);
+	strncpy(buf, cs->chatmessage, size-1);
+	buf[size-1] = '\0';
 	//clear the chat message from the state
 	strcpy(cs->chatmessage, "");
 } //end of the function BotGetChatMessage
@@ -2881,7 +2863,9 @@
 	cs = BotChatStateFromHandle(chatstate);
 	if (!cs) return;
 	cs->client = client;
-	Q_strncpyz(cs->name, name, sizeof(cs->name));
+	Com_Memset(cs->name, 0, sizeof(cs->name));
+	strncpy(cs->name, name, sizeof(cs->name));
+	cs->name[sizeof(cs->name)-1] = '\0';
 } //end of the function BotSetChatName
 //===========================================================================
 //
@@ -2930,6 +2914,7 @@
 //========================================================================
 void BotFreeChatState(int handle)
 {
+	bot_chatstate_t *cs;
 	bot_consolemessage_t m;
 	int h;
 
@@ -2943,6 +2928,7 @@
 		botimport.Print(PRT_FATAL, "invalid chat state %d\n", handle);
 		return;
 	} //end if
+	cs = botchatstates[handle];
 	if (LibVarGetValue("bot_reloadcharacters"))
 	{
 		BotFreeChatFile(handle);

```

### `quake3e`  — sha256 `5f01aa6c74d8...`, 92599 bytes

_Diff stat: +462 / -329 lines_

_(full diff is 49727 bytes — see files directly)_

### `openarena-engine`  — sha256 `1176bd0bac73...`, 90009 bytes

_Diff stat: +17 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_chat.c	2026-04-16 20:02:25.122907200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_chat.c	2026-04-16 22:48:25.713694700 +0100
@@ -342,7 +342,7 @@
 	m->handle = cs->handle;
 	m->time = AAS_Time();
 	m->type = type;
-	Q_strncpyz(m->message, message, MAX_MESSAGE_SIZE);
+	strncpy(m->message, message, MAX_MESSAGE_SIZE);
 	m->next = NULL;
 	if (cs->lastmessage)
 	{
@@ -553,11 +553,11 @@
 
 	//find the synonym in the string
 	str = StringContainsWord(string, synonym, qfalse);
-	//if the synonym occurred in the string
+	//if the synonym occured in the string
 	while(str)
 	{
 		//if the synonym isn't part of the replacement which is already in the string
-		//useful for abbreviations
+		//usefull for abreviations
 		str2 = StringContainsWord(string, replacement, qfalse);
 		while(str2)
 		{
@@ -629,7 +629,7 @@
 		source = LoadSourceFile(filename);
 		if (!source)
 		{
-			botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+			botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 			return NULL;
 		} //end if
 		//
@@ -984,7 +984,7 @@
 		source = LoadSourceFile(filename);
 		if (!source)
 		{
-			botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+			botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 			return NULL;
 		} //end if
 		//
@@ -1286,7 +1286,7 @@
 	source = LoadSourceFile(matchfile);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", matchfile);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", matchfile);
 		return NULL;
 	} //end if
 	//
@@ -1456,7 +1456,7 @@
 	int i;
 	bot_matchtemplate_t *ms;
 
-	Q_strncpyz(match->string, str, MAX_MESSAGE_SIZE);
+	strncpy(match->string, str, MAX_MESSAGE_SIZE);
 	//remove any trailing enters
 	while(strlen(match->string) &&
 			match->string[strlen(match->string)-1] == '\n')
@@ -1499,7 +1499,8 @@
 		if (match->variables[variable].length < size)
 			size = match->variables[variable].length+1;
 		assert( match->variables[variable].offset >= 0 );
-		Q_strncpyz(buf, &match->string[ (int) match->variables[variable].offset], size);
+		strncpy(buf, &match->string[ (int) match->variables[variable].offset], size-1);
+		buf[size-1] = '\0';
 	} //end if
 	else
 	{
@@ -1857,7 +1858,7 @@
 	source = LoadSourceFile(filename);
 	if (!source)
 	{
-		botimport.Print(PRT_ERROR, "couldn't load %s\n", filename);
+		botimport.Print(PRT_ERROR, "counldn't load %s\n", filename);
 		return NULL;
 	} //end if
 	//
@@ -2056,7 +2057,7 @@
 		source = LoadSourceFile(chatfile);
 		if (!source)
 		{
-			botimport.Print(PRT_ERROR, "couldn't load %s\n", chatfile);
+			botimport.Print(PRT_ERROR, "counldn't load %s\n", chatfile);
 			return NULL;
 		} //end if
 		//chat structure
@@ -2113,7 +2114,7 @@
 						if (pass && ptr)
 						{
 							chattype = (bot_chattype_t *) ptr;
-							Q_strncpyz(chattype->name, token.string, MAX_CHATTYPE_NAME);
+							strncpy(chattype->name, token.string, MAX_CHATTYPE_NAME);
 							chattype->firstchatmessage = NULL;
 							//add the chat type to the chat
 							chattype->next = chat->types;
@@ -2845,7 +2846,8 @@
 	if (!cs) return;
 
 	BotRemoveTildes(cs->chatmessage);
-	Q_strncpyz(buf, cs->chatmessage, size);
+	strncpy(buf, cs->chatmessage, size-1);
+	buf[size-1] = '\0';
 	//clear the chat message from the state
 	strcpy(cs->chatmessage, "");
 } //end of the function BotGetChatMessage
@@ -2881,7 +2883,9 @@
 	cs = BotChatStateFromHandle(chatstate);
 	if (!cs) return;
 	cs->client = client;
-	Q_strncpyz(cs->name, name, sizeof(cs->name));
+	Com_Memset(cs->name, 0, sizeof(cs->name));
+	strncpy(cs->name, name, sizeof(cs->name));
+	cs->name[sizeof(cs->name)-1] = '\0';
 } //end of the function BotSetChatName
 //===========================================================================
 //

```
