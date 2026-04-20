# Diff: `code/botlib/be_ai_chat.h`
**Canonical:** `wolfcamql-src` (sha256 `358600d743c7...`, 4615 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3e`  — sha256 `7491be51b9e8...`, 4781 bytes

_Diff stat: +9 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_chat.h	2026-04-16 20:02:25.122907200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_chat.h	2026-04-16 20:02:26.899996300 +0100
@@ -75,7 +75,7 @@
 //frees the chatstate
 void BotFreeChatState(int handle);
 //adds a console message to the chat state
-void BotQueueConsoleMessage(int chatstate, int type, char *message);
+void BotQueueConsoleMessage(int chatstate, int type, const char *message);
 //removes the console message from the chat state
 void BotRemoveConsoleMessage(int chatstate, int handle);
 //returns the next console message from the state
@@ -83,11 +83,11 @@
 //returns the number of console messages currently stored in the state
 int BotNumConsoleMessages(int chatstate);
 //selects a chat message of the given type
-void BotInitialChat(int chatstate, char *type, int mcontext, char *var0, char *var1, char *var2, char *var3, char *var4, char *var5, char *var6, char *var7);
+void BotInitialChat(int chatstate, const char *type, int mcontext, const char *var0, const char *var1, const char *var2, const char *var3, const char *var4, const char *var5, const char *var6, const char *var7);
 //returns the number of initial chat messages of the given type
-int BotNumInitialChats(int chatstate, char *type);
+int BotNumInitialChats(int chatstate, const char *type);
 //find and select a reply for the given message
-int BotReplyChat(int chatstate, char *message, int mcontext, int vcontext, char *var0, char *var1, char *var2, char *var3, char *var4, char *var5, char *var6, char *var7);
+int BotReplyChat(int chatstate, const char *message, int mcontext, int vcontext, const char *var0, const char *var1, const char *var2, const char *var3, const char *var4, const char *var5, const char *var6, const char *var7);
 //returns the length of the currently selected chat message
 int BotChatLength(int chatstate);
 //enters the selected chat message
@@ -95,19 +95,19 @@
 //get the chat message ready to be output
 void BotGetChatMessage(int chatstate, char *buf, int size);
 //checks if the first string contains the second one, returns index into first string or -1 if not found
-int StringContains(char *str1, char *str2, int casesensitive);
+int StringContains(const char *str1, const char *str2, int casesensitive);
 //finds a match for the given string using the match templates
-int BotFindMatch(char *str, bot_match_t *match, unsigned long int context);
+int BotFindMatch(const char *str, bot_match_t *match, unsigned long int context);
 //returns a variable from a match
 void BotMatchVariable(bot_match_t *match, int variable, char *buf, int size);
 //unify all the white spaces in the string
 void UnifyWhiteSpaces(char *string);
 //replace all the context related synonyms in the string
-void BotReplaceSynonyms(char *string, unsigned long int context);
+void BotReplaceSynonyms(char *string, int size, unsigned long int context);
 //loads a chat file for the chat state
-int BotLoadChatFile(int chatstate, char *chatfile, char *chatname);
+int BotLoadChatFile(int chatstate, const char *chatfile, const char *chatname);
 //store the gender of the bot in the chat state
 void BotSetChatGender(int chatstate, int gender);
 //store the bot name in the chat state
-void BotSetChatName(int chatstate, char *name, int client);
+void BotSetChatName(int chatstate, const char *name, int client);
 

```
