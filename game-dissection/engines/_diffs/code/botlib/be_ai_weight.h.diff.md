# Diff: `code/botlib/be_ai_weight.h`
**Canonical:** `wolfcamql-src` (sha256 `b0871bfc623f...`, 2991 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `2115a534e01b...`, 2971 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weight.h	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ai_weight.h	2026-04-16 20:02:19.853390000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -64,7 +64,7 @@
 weightconfig_t *ReadWeightConfig(char *filename);
 //free a weight configuration
 void FreeWeightConfig(weightconfig_t *config);
-//writes a weight configuration, returns true if successful
+//writes a weight configuration, returns true if successfull
 qboolean WriteWeightConfig(char *filename, weightconfig_t *config);
 //find the fuzzy weight with the given name
 int FindFuzzyWeight(weightconfig_t *wc, char *name);

```

### `quake3e`  — sha256 `1d837210d512...`, 3009 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weight.h	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_weight.h	2026-04-16 20:02:26.902995100 +0100
@@ -32,7 +32,7 @@
 #define WT_BALANCE			1
 #define MAX_WEIGHTS			128
 
-//fuzzy seperator
+//fuzzy separator
 typedef struct fuzzyseperator_s
 {
 	int index;
@@ -61,13 +61,13 @@
 } weightconfig_t;
 
 //reads a weight configuration
-weightconfig_t *ReadWeightConfig(char *filename);
+weightconfig_t *ReadWeightConfig(const char *filename);
 //free a weight configuration
 void FreeWeightConfig(weightconfig_t *config);
 //writes a weight configuration, returns true if successful
 qboolean WriteWeightConfig(char *filename, weightconfig_t *config);
 //find the fuzzy weight with the given name
-int FindFuzzyWeight(weightconfig_t *wc, char *name);
+int FindFuzzyWeight(const weightconfig_t *wc, const char *name);
 //returns the fuzzy weight for the given inventory and weight
 float FuzzyWeight(int *inventory, weightconfig_t *wc, int weightnum);
 float FuzzyWeightUndecided(int *inventory, weightconfig_t *wc, int weightnum);

```

### `openarena-engine`  — sha256 `b5fc42dc844e...`, 2992 bytes
Also identical in: openarena-gamecode

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_weight.h	2026-04-16 20:02:25.126417100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_weight.h	2026-04-16 22:48:25.715695800 +0100
@@ -64,7 +64,7 @@
 weightconfig_t *ReadWeightConfig(char *filename);
 //free a weight configuration
 void FreeWeightConfig(weightconfig_t *config);
-//writes a weight configuration, returns true if successful
+//writes a weight configuration, returns true if successfull
 qboolean WriteWeightConfig(char *filename, weightconfig_t *config);
 //find the fuzzy weight with the given name
 int FindFuzzyWeight(weightconfig_t *wc, char *name);

```
