# Diff: `code/botlib/be_aas_def.h`
**Canonical:** `wolfcamql-src` (sha256 `7495e2ea78b2...`, 8219 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `afbaa2225ecd...`, 8756 bytes

_Diff stat: +26 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_def.h	2026-04-16 20:02:25.114324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\botlib\be_aas_def.h	2026-04-16 20:02:19.845388400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -29,16 +29,34 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
-
 //debugging on
 #define AAS_DEBUG
 
+#define MAX_CLIENTS			64
+#define	MAX_MODELS			256		// these are sent over the net as 8 bits
+#define	MAX_SOUNDS			256		// so they cannot be blindly increased
+#define	MAX_CONFIGSTRINGS	1024
+
+#define	CS_SCORES			32
+#define	CS_MODELS			(CS_SCORES+MAX_CLIENTS)
+#define	CS_SOUNDS			(CS_MODELS+MAX_MODELS)
+
 #define DF_AASENTNUMBER(x)		(x - aasworld.entities)
 #define DF_NUMBERAASENT(x)		(&aasworld.entities[x])
 #define DF_AASENTCLIENT(x)		(x - aasworld.entities - 1)
 #define DF_CLIENTAASENT(x)		(&aasworld.entities[x + 1])
 
+#ifndef MAX_PATH
+	#define MAX_PATH				MAX_QPATH
+#endif
+
+//string index (for model, sound and image index)
+typedef struct aas_stringindex_s
+{
+	int numindexes;
+	char **index;
+} aas_stringindex_t;
+
 //structure to link entities to areas and areas to entities
 typedef struct aas_link_s
 {
@@ -183,8 +201,8 @@
 	float time;
 	int numframes;
 	//name of the aas file
-	char filename[MAX_QPATH];
-	char mapname[MAX_QPATH];
+	char filename[MAX_PATH];
+	char mapname[MAX_PATH];
 	//bounding boxes
 	int numbboxes;
 	aas_bbox_t *bboxes;
@@ -239,6 +257,9 @@
 	int maxentities;
 	int maxclients;
 	aas_entity_t *entities;
+	//string indexes
+	char *configstrings[MAX_CONFIGSTRINGS];
+	int indexessetup;
 	//index to retrieve travel flag for a travel type
 	int travelflagfortype[MAX_TRAVELTYPES];
 	//travel flags for each area based on contents

```

### `quake3e`  — sha256 `4a4adc58611e...`, 8277 bytes
Also identical in: openarena-engine

_Diff stat: +6 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_def.h	2026-04-16 20:02:25.114324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\botlib\be_aas_def.h	2026-04-16 20:02:26.892281200 +0100
@@ -39,6 +39,10 @@
 #define DF_AASENTCLIENT(x)		(x - aasworld.entities - 1)
 #define DF_CLIENTAASENT(x)		(&aasworld.entities[x + 1])
 
+#ifndef MAX_PATH
+	#define MAX_PATH				MAX_QPATH
+#endif
+
 //structure to link entities to areas and areas to entities
 typedef struct aas_link_s
 {
@@ -183,8 +187,8 @@
 	float time;
 	int numframes;
 	//name of the aas file
-	char filename[MAX_QPATH];
-	char mapname[MAX_QPATH];
+	char filename[MAX_PATH];
+	char mapname[MAX_PATH];
 	//bounding boxes
 	int numbboxes;
 	aas_bbox_t *bboxes;

```

### `openarena-gamecode`  — sha256 `f69b9f960bfd...`, 8777 bytes

_Diff stat: +25 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\botlib\be_aas_def.h	2026-04-16 20:02:25.114324400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\botlib\be_aas_def.h	2026-04-16 22:48:24.140256100 +0100
@@ -29,16 +29,34 @@
  *
  *****************************************************************************/
 
-#include "../qcommon/q_shared.h"
-
 //debugging on
 #define AAS_DEBUG
 
+#define MAX_CLIENTS			64
+#define	MAX_MODELS			256		// these are sent over the net as 8 bits
+#define	MAX_SOUNDS			256		// so they cannot be blindly increased
+#define	MAX_CONFIGSTRINGS	1024
+
+#define	CS_SCORES			32
+#define	CS_MODELS			(CS_SCORES+MAX_CLIENTS)
+#define	CS_SOUNDS			(CS_MODELS+MAX_MODELS)
+
 #define DF_AASENTNUMBER(x)		(x - aasworld.entities)
 #define DF_NUMBERAASENT(x)		(&aasworld.entities[x])
 #define DF_AASENTCLIENT(x)		(x - aasworld.entities - 1)
 #define DF_CLIENTAASENT(x)		(&aasworld.entities[x + 1])
 
+#ifndef MAX_PATH
+	#define MAX_PATH				MAX_QPATH
+#endif
+
+//string index (for model, sound and image index)
+typedef struct aas_stringindex_s
+{
+	int numindexes;
+	char **index;
+} aas_stringindex_t;
+
 //structure to link entities to areas and areas to entities
 typedef struct aas_link_s
 {
@@ -183,8 +201,8 @@
 	float time;
 	int numframes;
 	//name of the aas file
-	char filename[MAX_QPATH];
-	char mapname[MAX_QPATH];
+	char filename[MAX_PATH];
+	char mapname[MAX_PATH];
 	//bounding boxes
 	int numbboxes;
 	aas_bbox_t *bboxes;
@@ -239,6 +257,9 @@
 	int maxentities;
 	int maxclients;
 	aas_entity_t *entities;
+	//string indexes
+	char *configstrings[MAX_CONFIGSTRINGS];
+	int indexessetup;
 	//index to retrieve travel flag for a travel type
 	int travelflagfortype[MAX_TRAVELTYPES];
 	//travel flags for each area based on contents

```
