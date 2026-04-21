# Diff: `code/game/g_target.c`
**Canonical:** `wolfcamql-src` (sha256 `9d431c52a5b0...`, 13186 bytes)
Also identical in: ioquake3

## Variants

### `quake3-source`  — sha256 `34249fdb42c4...`, 13165 bytes

_Diff stat: +3 / -3 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_target.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_target.c	2026-04-16 20:02:19.910572800 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -102,7 +102,7 @@
 }
 
 void SP_target_delay( gentity_t *ent ) {
-	// check delay for backwards compatibility
+	// check delay for backwards compatability
 	if ( !G_SpawnFloat( "delay", "0", &ent->wait ) ) {
 		G_SpawnFloat( "wait", "1", &ent->wait );
 	}
@@ -206,7 +206,7 @@
 		G_Error( "target_speaker without a noise key at %s", vtos( ent->s.origin ) );
 	}
 
-	// force all client relative sounds to be "activator" speakers that
+	// force all client reletive sounds to be "activator" speakers that
 	// play on the entity that activates it
 	if ( s[0] == '*' ) {
 		ent->spawnflags |= 8;

```

### `openarena-engine`  — sha256 `4d29bd667d5e...`, 13186 bytes

_Diff stat: +1 / -1 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_target.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_target.c	2026-04-16 22:48:25.751046300 +0100
@@ -102,7 +102,7 @@
 }
 
 void SP_target_delay( gentity_t *ent ) {
-	// check delay for backwards compatibility
+	// check delay for backwards compatability
 	if ( !G_SpawnFloat( "delay", "0", &ent->wait ) ) {
 		G_SpawnFloat( "wait", "1", &ent->wait );
 	}

```

### `openarena-gamecode`  — sha256 `68fbce8dfc92...`, 13358 bytes

_Diff stat: +8 / -6 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_target.c	2026-04-16 20:02:25.199156400 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_target.c	2026-04-16 22:48:24.175987200 +0100
@@ -102,7 +102,7 @@
 }
 
 void SP_target_delay( gentity_t *ent ) {
-	// check delay for backwards compatibility
+	// check delay for backwards compatability
 	if ( !G_SpawnFloat( "delay", "0", &ent->wait ) ) {
 		G_SpawnFloat( "wait", "1", &ent->wait );
 	}
@@ -206,7 +206,7 @@
 		G_Error( "target_speaker without a noise key at %s", vtos( ent->s.origin ) );
 	}
 
-	// force all client relative sounds to be "activator" speakers that
+	// force all client reletive sounds to be "activator" speakers that
 	// play on the entity that activates it
 	if ( s[0] == '*' ) {
 		ent->spawnflags |= 8;
@@ -360,8 +360,9 @@
 The activator will be teleported away.
 */
 void SP_target_teleporter( gentity_t *self ) {
-	if (!self->targetname)
+	if (!self->targetname) {
 		G_Printf("untargeted %s at %s\n", self->classname, vtos(self->s.origin));
+	}
 
 	self->use = target_teleporter_use;
 }
@@ -424,6 +425,7 @@
 {
 	int i;
 	int n;
+        //static char *gametypeNames[] = {"ffa", "tournament", "single", "team", "ctf", "oneflag", "obelisk", "harvester", "elimination", "ctf", "lms", "dd", "dom"};
 
 	if (level.locationLinked) 
 		return;
@@ -435,9 +437,9 @@
 	trap_SetConfigstring( CS_LOCATIONS, "unknown" );
 
 	for (i = 0, ent = g_entities, n = 1;
-			i < level.num_entities;
-			i++, ent++) {
-		if (ent->classname && !Q_stricmp(ent->classname, "target_location")) {
+		i < level.num_entities;
+		i++, ent++) {
+		if (ent->classname && Q_strequal(ent->classname, "target_location") ) {
 			// lets overload some variables!
 			ent->health = n; // use for location marking
 			trap_SetConfigstring( CS_LOCATIONS + n, ent->message );

```
