# Diff: `code/botlib/be_ai_goal.h`
**Canonical:** `wolfcamql-src` (sha256 `220ce2ce70ae...`, 5002 bytes)
Also identical in: ioquake3, openarena-engine, openarena-gamecode

## Variants

### `quake3e`  — sha256 `d7e35d2beb92...`, 5038 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_goal.h	2026-04-16 20:02:25.124411900 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_goal.h	2026-04-16 20:02:26.901008000 +0100
@@ -80,16 +80,16 @@
 int BotChooseNBGItem(int goalstate, vec3_t origin, int *inventory, int travelflags,
 							bot_goal_t *ltg, float maxtime);
 //returns true if the bot touches the goal
-int BotTouchingGoal(vec3_t origin, bot_goal_t *goal);
+int BotTouchingGoal(const vec3_t origin, const bot_goal_t *goal);
 //returns true if the goal should be visible but isn't
 int BotItemGoalInVisButNotVisible(int viewer, vec3_t eye, vec3_t viewangles, bot_goal_t *goal);
 //search for a goal for the given classname, the index can be used
 //as a start point for the search when multiple goals are available with that same classname
-int BotGetLevelItemGoal(int index, char *classname, bot_goal_t *goal);
+int BotGetLevelItemGoal(int index, const char *classname, bot_goal_t *goal);
 //get the next camp spot in the map
 int BotGetNextCampSpotGoal(int num, bot_goal_t *goal);
 //get the map location with the given name
-int BotGetMapLocationGoal(char *name, bot_goal_t *goal);
+int BotGetMapLocationGoal(const char *name, bot_goal_t *goal);
 //returns the avoid goal time
 float BotAvoidGoalTime(int goalstate, int number);
 //set the avoid goal time
@@ -101,11 +101,11 @@
 //interbreed the goal fuzzy logic
 void BotInterbreedGoalFuzzyLogic(int parent1, int parent2, int child);
 //save the goal fuzzy logic to disk
-void BotSaveGoalFuzzyLogic(int goalstate, char *filename);
+void BotSaveGoalFuzzyLogic(int goalstate, const char *filename);
 //mutate the goal fuzzy logic
 void BotMutateGoalFuzzyLogic(int goalstate, float range);
 //loads item weights for the bot
-int BotLoadItemWeights(int goalstate, char *filename);
+int BotLoadItemWeights(int goalstate, const char *filename);
 //frees the item weights of the bot
 void BotFreeItemWeights(int goalstate);
 //returns the handle of a newly allocated goal state

```
