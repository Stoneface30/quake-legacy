# Diff: `code/botlib/be_ai_gen.c`
**Canonical:** `wolfcamql-src` (sha256 `e9701a87120a...`, 4075 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `563e0eb266d0...`, 4088 bytes

_Diff stat: +8 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_gen.c	2026-04-16 20:02:25.122907200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_ai_gen.c	2026-04-16 20:02:19.851388600 +0100
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
 #include "l_log.h"
 #include "l_utils.h"
@@ -37,11 +37,11 @@
 #include "l_precomp.h"
 #include "l_struct.h"
 #include "aasfile.h"
-#include "botlib.h"
-#include "be_aas.h"
+#include "../game/botlib.h"
+#include "../game/be_aas.h"
 #include "be_aas_funcs.h"
 #include "be_interface.h"
-#include "be_ai_gen.h"
+#include "../game/be_ai_gen.h"
 
 //===========================================================================
 //
@@ -51,7 +51,7 @@
 //===========================================================================
 int GeneticSelection(int numranks, float *rankings)
 {
-	float sum;
+	float sum, select;
 	int i, index;
 
 	sum = 0;
@@ -62,9 +62,9 @@
 	} //end for
 	if (sum > 0)
 	{
-		//select a bot where the ones with the highest rankings have
+		//select a bot where the ones with the higest rankings have
 		//the highest chance of being selected
-		//sum *= random();
+		select = random() * sum;
 		for (i = 0; i < numranks; i++)
 		{
 			if (rankings[i] < 0) continue;

```

### `quake3e`  — sha256 `ccba162e84c3...`, 4088 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_gen.c	2026-04-16 20:02:25.122907200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_ai_gen.c	2026-04-16 20:02:26.899996300 +0100
@@ -49,7 +49,7 @@
 // Returns:				-
 // Changes Globals:		-
 //===========================================================================
-int GeneticSelection(int numranks, float *rankings)
+static int GeneticSelection(int numranks, const float *rankings)
 {
 	float sum;
 	int i, index;

```

### `openarena-engine`  — sha256 `0c03b4f1e449...`, 4074 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_ai_gen.c	2026-04-16 20:02:25.122907200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\botlib\be_ai_gen.c	2026-04-16 22:48:25.713694700 +0100
@@ -62,7 +62,7 @@
 	} //end for
 	if (sum > 0)
 	{
-		//select a bot where the ones with the highest rankings have
+		//select a bot where the ones with the higest rankings have
 		//the highest chance of being selected
 		//sum *= random();
 		for (i = 0; i < numranks; i++)

```
