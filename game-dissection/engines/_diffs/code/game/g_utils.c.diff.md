# Diff: `code/game/g_utils.c`
**Canonical:** `wolfcamql-src` (sha256 `e4c679c7e5a7...`, 15548 bytes)

## Variants

### `quake3-source`  — sha256 `8fdebd93b897...`, 15157 bytes

_Diff stat: +7 / -21 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_utils.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_utils.c	2026-04-16 20:02:19.912079900 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -54,12 +54,12 @@
 	}
 }
 
-const char *BuildShaderStateConfig(void) {
+const char *BuildShaderStateConfig() {
 	static char	buff[MAX_STRING_CHARS*4];
 	char out[(MAX_QPATH * 2) + 5];
 	int i;
   
-	memset(buff, 0, sizeof(buff));
+	memset(buff, 0, MAX_STRING_CHARS);
 	for (i = 0; i < remapCount; i++) {
 		Com_sprintf(out, (MAX_QPATH * 2) + 5, "%s=%s:%5.2f@", remappedShaders[i].oldShader, remappedShaders[i].newShader, remappedShaders[i].timeOffset);
 		Q_strcat( buff, sizeof( buff ), out);
@@ -118,8 +118,7 @@
 }
 
 int G_SoundIndex( char *name ) {
-	//return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue) + 1;
-	return G_FindConfigstringIndex (name, CS_SOUNDS - 1, MAX_SOUNDS, qtrue);
+	return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue);
 }
 
 //=====================================================================
@@ -392,6 +391,7 @@
 	gentity_t	*e;
 
 	e = NULL;	// shut up warning
+	i = 0;		// shut up warning
 	for ( force = 0 ; force < 2 ; force++ ) {
 		// if we go through all entities and can't find one to free,
 		// override the normal minimum times before use
@@ -411,20 +411,11 @@
 			G_InitGentity( e );
 			return e;
 		}
-		if ( level.num_entities < ENTITYNUM_MAX_NORMAL ) {
+		if ( i != MAX_GENTITIES ) {
 			break;
 		}
 	}
-	if ( level.num_entities == ENTITYNUM_MAX_NORMAL ) {
-		for (i = MAX_CLIENTS;  i < level.num_entities;  i++) {
-			e = &g_entities[i];
-			if (e->inuse) {
-				continue;
-			}
-			G_InitGentity(e);
-			return e;
-		}
-
+	if ( i == ENTITYNUM_MAX_NORMAL ) {
 		for (i = 0; i < MAX_GENTITIES; i++) {
 			G_Printf("%4i: %s\n", i, g_entities[i].classname);
 		}
@@ -451,11 +442,6 @@
 	int			i;
 	gentity_t	*e;
 
-	if ( level.num_entities < ENTITYNUM_MAX_NORMAL ) {
-		// can open a new slot if needed
-		return qtrue;
-	}
-
 	e = &g_entities[MAX_CLIENTS];
 	for ( i = MAX_CLIENTS; i < level.num_entities; i++, e++) {
 		if ( e->inuse ) {

```

### `ioquake3`  — sha256 `e59ae82f1733...`, 15301 bytes

_Diff stat: +1 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_utils.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\g_utils.c	2026-04-16 20:02:21.549421400 +0100
@@ -118,8 +118,7 @@
 }
 
 int G_SoundIndex( char *name ) {
-	//return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue) + 1;
-	return G_FindConfigstringIndex (name, CS_SOUNDS - 1, MAX_SOUNDS, qtrue);
+	return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue);
 }
 
 //=====================================================================
@@ -416,15 +415,6 @@
 		}
 	}
 	if ( level.num_entities == ENTITYNUM_MAX_NORMAL ) {
-		for (i = MAX_CLIENTS;  i < level.num_entities;  i++) {
-			e = &g_entities[i];
-			if (e->inuse) {
-				continue;
-			}
-			G_InitGentity(e);
-			return e;
-		}
-
 		for (i = 0; i < MAX_GENTITIES; i++) {
 			G_Printf("%4i: %s\n", i, g_entities[i].classname);
 		}

```

### `openarena-engine`  — sha256 `ccc4d3b85b65...`, 15182 bytes

_Diff stat: +5 / -19 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_utils.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_utils.c	2026-04-16 22:48:25.752047200 +0100
@@ -59,7 +59,7 @@
 	char out[(MAX_QPATH * 2) + 5];
 	int i;
   
-	memset(buff, 0, sizeof(buff));
+	memset(buff, 0, MAX_STRING_CHARS);
 	for (i = 0; i < remapCount; i++) {
 		Com_sprintf(out, (MAX_QPATH * 2) + 5, "%s=%s:%5.2f@", remappedShaders[i].oldShader, remappedShaders[i].newShader, remappedShaders[i].timeOffset);
 		Q_strcat( buff, sizeof( buff ), out);
@@ -118,8 +118,7 @@
 }
 
 int G_SoundIndex( char *name ) {
-	//return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue) + 1;
-	return G_FindConfigstringIndex (name, CS_SOUNDS - 1, MAX_SOUNDS, qtrue);
+	return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue);
 }
 
 //=====================================================================
@@ -392,6 +391,7 @@
 	gentity_t	*e;
 
 	e = NULL;	// shut up warning
+	i = 0;		// shut up warning
 	for ( force = 0 ; force < 2 ; force++ ) {
 		// if we go through all entities and can't find one to free,
 		// override the normal minimum times before use
@@ -411,20 +411,11 @@
 			G_InitGentity( e );
 			return e;
 		}
-		if ( level.num_entities < ENTITYNUM_MAX_NORMAL ) {
+		if ( i != MAX_GENTITIES ) {
 			break;
 		}
 	}
-	if ( level.num_entities == ENTITYNUM_MAX_NORMAL ) {
-		for (i = MAX_CLIENTS;  i < level.num_entities;  i++) {
-			e = &g_entities[i];
-			if (e->inuse) {
-				continue;
-			}
-			G_InitGentity(e);
-			return e;
-		}
-
+	if ( i == ENTITYNUM_MAX_NORMAL ) {
 		for (i = 0; i < MAX_GENTITIES; i++) {
 			G_Printf("%4i: %s\n", i, g_entities[i].classname);
 		}
@@ -451,11 +442,6 @@
 	int			i;
 	gentity_t	*e;
 
-	if ( level.num_entities < ENTITYNUM_MAX_NORMAL ) {
-		// can open a new slot if needed
-		return qtrue;
-	}
-
 	e = &g_entities[MAX_CLIENTS];
 	for ( i = MAX_CLIENTS; i < level.num_entities; i++, e++) {
 		if ( e->inuse ) {

```

### `openarena-gamecode`  — sha256 `c36a8c9a4835...`, 16234 bytes

_Diff stat: +102 / -62 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_utils.c	2026-04-16 20:02:25.200156200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_utils.c	2026-04-16 22:48:24.177987400 +0100
@@ -25,9 +25,9 @@
 #include "g_local.h"
 
 typedef struct {
-  char oldShader[MAX_QPATH];
-  char newShader[MAX_QPATH];
-  float timeOffset;
+	char oldShader[MAX_QPATH];
+	char newShader[MAX_QPATH];
+	float timeOffset;
 } shaderRemap_t;
 
 #define MAX_SHADER_REMAPS 128
@@ -35,11 +35,12 @@
 int remapCount = 0;
 shaderRemap_t remappedShaders[MAX_SHADER_REMAPS];
 
-void AddRemap(const char *oldShader, const char *newShader, float timeOffset) {
+void AddRemap(const char *oldShader, const char *newShader, float timeOffset)
+{
 	int i;
 
 	for (i = 0; i < remapCount; i++) {
-		if (Q_stricmp(oldShader, remappedShaders[i].oldShader) == 0) {
+		if ( Q_strequal(oldShader, remappedShaders[i].oldShader) ) {
 			// found it, just update this one
 			strcpy(remappedShaders[i].newShader,newShader);
 			remappedShaders[i].timeOffset = timeOffset;
@@ -54,12 +55,13 @@
 	}
 }
 
-const char *BuildShaderStateConfig(void) {
+const char *BuildShaderStateConfig(void)
+{
 	static char	buff[MAX_STRING_CHARS*4];
 	char out[(MAX_QPATH * 2) + 5];
 	int i;
-  
-	memset(buff, 0, sizeof(buff));
+
+	memset(buff, 0, MAX_STRING_CHARS);
 	for (i = 0; i < remapCount; i++) {
 		Com_sprintf(out, (MAX_QPATH * 2) + 5, "%s=%s:%5.2f@", remappedShaders[i].oldShader, remappedShaders[i].newShader, remappedShaders[i].timeOffset);
 		Q_strcat( buff, sizeof( buff ), out);
@@ -81,7 +83,8 @@
 
 ================
 */
-int G_FindConfigstringIndex( char *name, int start, int max, qboolean create ) {
+int G_FindConfigstringIndex( char *name, int start, int max, qboolean create )
+{
 	int		i;
 	char	s[MAX_STRING_CHARS];
 
@@ -94,7 +97,7 @@
 		if ( !s[0] ) {
 			break;
 		}
-		if ( !strcmp( s, name ) ) {
+		if ( strequals( s, name ) ) {
 			return i;
 		}
 	}
@@ -113,13 +116,14 @@
 }
 
 
-int G_ModelIndex( char *name ) {
+int G_ModelIndex( char *name )
+{
 	return G_FindConfigstringIndex (name, CS_MODELS, MAX_MODELS, qtrue);
 }
 
-int G_SoundIndex( char *name ) {
-	//return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue) + 1;
-	return G_FindConfigstringIndex (name, CS_SOUNDS - 1, MAX_SOUNDS, qtrue);
+int G_SoundIndex( char *name )
+{
+	return G_FindConfigstringIndex (name, CS_SOUNDS, MAX_SOUNDS, qtrue);
 }
 
 //=====================================================================
@@ -132,7 +136,8 @@
 Broadcasts a command to only a specific team
 ================
 */
-void G_TeamCommand( team_t team, char *cmd ) {
+void G_TeamCommand( team_t team, char *cmd )
+{
 	int		i;
 
 	for ( i = 0 ; i < level.maxclients ; i++ ) {
@@ -166,14 +171,13 @@
 	else
 		from++;
 
-	for ( ; from < &g_entities[level.num_entities] ; from++)
-	{
+	for ( ; from < &g_entities[level.num_entities] ; from++) {
 		if (!from->inuse)
 			continue;
 		s = *(char **) ((byte *)from + fieldofs);
 		if (!s)
 			continue;
-		if (!Q_stricmp (s, match))
+		if (Q_strequal (s, match))
 			return from;
 	}
 
@@ -196,14 +200,12 @@
 	int		num_choices = 0;
 	gentity_t	*choice[MAXCHOICES];
 
-	if (!targetname)
-	{
+	if (!targetname) {
 		G_Printf("G_PickTarget called with NULL targetname\n");
 		return NULL;
 	}
 
-	while(1)
-	{
+	while(1) {
 		ent = G_Find (ent, FOFS(targetname), targetname);
 		if (!ent)
 			break;
@@ -212,8 +214,7 @@
 			break;
 	}
 
-	if (!num_choices)
-	{
+	if (!num_choices) {
 		G_Printf("G_PickTarget: target %s not found\n", targetname);
 		return NULL;
 	}
@@ -233,9 +234,10 @@
 
 ==============================
 */
-void G_UseTargets( gentity_t *ent, gentity_t *activator ) {
+void G_UseTargets( gentity_t *ent, gentity_t *activator )
+{
 	gentity_t		*t;
-	
+
 	if ( !ent ) {
 		return;
 	}
@@ -254,7 +256,8 @@
 	while ( (t = G_Find (t, FOFS(targetname), ent->target)) != NULL ) {
 		if ( t == ent ) {
 			G_Printf ("WARNING: Entity used itself.\n");
-		} else {
+		}
+		else {
 			if ( t->use ) {
 				t->use (t, ent, activator);
 			}
@@ -275,7 +278,8 @@
 for making temporary vectors for function calls
 =============
 */
-float	*tv( float x, float y, float z ) {
+float	*tv( float x, float y, float z )
+{
 	static	int		index;
 	static	vec3_t	vecs[8];
 	float	*v;
@@ -301,7 +305,8 @@
 for printing vectors
 =============
 */
-char	*vtos( const vec3_t v ) {
+char	*vtos( const vec3_t v )
+{
 	static	int		index;
 	static	char	str[8][32];
 	char	*s;
@@ -326,7 +331,8 @@
 instead of an orientation.
 ===============
 */
-void G_SetMovedir( vec3_t angles, vec3_t movedir ) {
+void G_SetMovedir( vec3_t angles, vec3_t movedir )
+{
 	static vec3_t VEC_UP		= {0, -1, 0};
 	static vec3_t MOVEDIR_UP	= {0, 0, 1};
 	static vec3_t VEC_DOWN		= {0, -2, 0};
@@ -334,26 +340,32 @@
 
 	if ( VectorCompare (angles, VEC_UP) ) {
 		VectorCopy (MOVEDIR_UP, movedir);
-	} else if ( VectorCompare (angles, VEC_DOWN) ) {
+	}
+	else if ( VectorCompare (angles, VEC_DOWN) ) {
 		VectorCopy (MOVEDIR_DOWN, movedir);
-	} else {
+	}
+	else {
 		AngleVectors (angles, movedir, NULL, NULL);
 	}
 	VectorClear( angles );
 }
 
 
-float vectoyaw( const vec3_t vec ) {
+float vectoyaw( const vec3_t vec )
+{
 	float	yaw;
-	
+
 	if (vec[YAW] == 0 && vec[PITCH] == 0) {
 		yaw = 0;
-	} else {
+	}
+	else {
 		if (vec[PITCH]) {
 			yaw = ( atan2( vec[YAW], vec[PITCH]) * 180 / M_PI );
-		} else if (vec[YAW] > 0) {
+		}
+		else if (vec[YAW] > 0) {
 			yaw = 90;
-		} else {
+		}
+		else {
 			yaw = 270;
 		}
 		if (yaw < 0) {
@@ -365,7 +377,8 @@
 }
 
 
-void G_InitGentity( gentity_t *e ) {
+void G_InitGentity( gentity_t *e )
+{
 	e->inuse = qtrue;
 	e->classname = "noclass";
 	e->s.number = e - g_entities;
@@ -387,7 +400,8 @@
 angles and bad trails.
 =================
 */
-gentity_t *G_Spawn( void ) {
+gentity_t *G_Spawn( void )
+{
 	int			i, force;
 	gentity_t	*e;
 
@@ -416,27 +430,18 @@
 		}
 	}
 	if ( level.num_entities == ENTITYNUM_MAX_NORMAL ) {
-		for (i = MAX_CLIENTS;  i < level.num_entities;  i++) {
-			e = &g_entities[i];
-			if (e->inuse) {
-				continue;
-			}
-			G_InitGentity(e);
-			return e;
-		}
-
 		for (i = 0; i < MAX_GENTITIES; i++) {
 			G_Printf("%4i: %s\n", i, g_entities[i].classname);
 		}
 		G_Error( "G_Spawn: no free entities" );
 	}
-	
+
 	// open up a new slot
 	level.num_entities++;
 
 	// let the server system know that there are more entities
-	trap_LocateGameData( level.gentities, level.num_entities, sizeof( gentity_t ), 
-		&level.clients[0].ps, sizeof( level.clients[0] ) );
+	trap_LocateGameData( level.gentities, level.num_entities, sizeof( gentity_t ),
+	                     &level.clients[0].ps, sizeof( level.clients[0] ) );
 
 	G_InitGentity( e );
 	return e;
@@ -447,7 +452,8 @@
 G_EntitiesFree
 =================
 */
-qboolean G_EntitiesFree( void ) {
+qboolean G_EntitiesFree( void )
+{
 	int			i;
 	gentity_t	*e;
 
@@ -475,7 +481,8 @@
 Marks the entity as free
 =================
 */
-void G_FreeEntity( gentity_t *ed ) {
+void G_FreeEntity( gentity_t *ed )
+{
 	trap_UnlinkEntity (ed);		// unlink from world
 
 	if ( ed->neverFree ) {
@@ -497,7 +504,8 @@
 must be taken if the origin is right on a surface (snap towards start vector first)
 =================
 */
-gentity_t *G_TempEntity( vec3_t origin, int event ) {
+gentity_t *G_TempEntity( const vec3_t origin, int event )
+{
 	gentity_t		*e;
 	vec3_t		snapped;
 
@@ -536,7 +544,8 @@
 of ent.  Ent should be unlinked before calling this!
 =================
 */
-void G_KillBox (gentity_t *ent) {
+void G_KillBox (gentity_t *ent)
+{
 	int			i, num;
 	int			touch[MAX_GENTITIES];
 	gentity_t	*hit;
@@ -554,7 +563,7 @@
 
 		// nail it
 		G_Damage ( hit, ent, ent, NULL, NULL,
-			100000, DAMAGE_NO_PROTECTION, MOD_TELEFRAG);
+		           100000, DAMAGE_NO_PROTECTION, MOD_TELEFRAG);
 	}
 
 }
@@ -570,7 +579,8 @@
 Adds an event+parm and twiddles the event counter
 ===============
 */
-void G_AddPredictableEvent( gentity_t *ent, int event, int eventParm ) {
+void G_AddPredictableEvent( gentity_t *ent, int event, int eventParm )
+{
 	if ( !ent->client ) {
 		return;
 	}
@@ -585,7 +595,8 @@
 Adds an event+parm and twiddles the event counter
 ===============
 */
-void G_AddEvent( gentity_t *ent, int event, int eventParm ) {
+void G_AddEvent( gentity_t *ent, int event, int eventParm )
+{
 	int		bits;
 
 	if ( !event ) {
@@ -600,7 +611,8 @@
 		ent->client->ps.externalEvent = event | bits;
 		ent->client->ps.externalEventParm = eventParm;
 		ent->client->ps.externalEventTime = level.time;
-	} else {
+	}
+	else {
 		bits = ent->s.event & EV_EVENT_BITS;
 		bits = ( bits + EV_EVENT_BIT1 ) & EV_EVENT_BITS;
 		ent->s.event = event | bits;
@@ -615,13 +627,39 @@
 G_Sound
 =============
 */
-void G_Sound( gentity_t *ent, int channel, int soundIndex ) {
+void G_Sound( gentity_t *ent, int channel, int soundIndex )
+{
 	gentity_t	*te;
 
 	te = G_TempEntity( ent->r.currentOrigin, EV_GENERAL_SOUND );
 	te->s.eventParm = soundIndex;
 }
 
+/*
+=============
+G_GlobalSound
+KK-OAX G_SoundIndex must first be called.
+=============
+*/
+void G_GlobalSound( int soundIndex )
+{
+	gentity_t  *te;
+	//Let's avoid the S_FindName error if soundIndex is 0.
+	//Sago: And let's check that the sound index is within the allowed range.
+	if( ( soundIndex <= 0 ) ||  soundIndex >= MAX_SOUNDS ) {
+		if (g_developer.integer){
+			//Display this message when debugging
+			G_Printf( "GlobalSound: Error, no soundIndex specified. Check your code!\n" );
+		}
+		return;
+	}
+	//Spawn a Temporary Entity at the origin point for Intermission with the event EV_GLOBAL_SOUND
+	te = G_TempEntity( level.intermission_origin, EV_GLOBAL_SOUND );
+	//Add the soundIndex to the parameters for the EV_GLOBAL_SOUND event we are calling
+	te->s.eventParm = soundIndex;
+	//Broadcast the sound event.
+	te->r.svFlags |= SVF_BROADCAST;
+}
 
 //==============================================================================
 
@@ -633,7 +671,8 @@
 Sets the pos trajectory for a fixed position
 ================
 */
-void G_SetOrigin( gentity_t *ent, vec3_t origin ) {
+void G_SetOrigin( gentity_t *ent, vec3_t origin )
+{
 	VectorCopy( origin, ent->s.pos.trBase );
 	ent->s.pos.trType = TR_STATIONARY;
 	ent->s.pos.trTime = 0;
@@ -651,7 +690,8 @@
   with r_debugSurface set to 2
 ================
 */
-int DebugLine(vec3_t start, vec3_t end, int color) {
+int DebugLine(vec3_t start, vec3_t end, int color)
+{
 	vec3_t points[4], dir, cross, up = {0, 0, 1};
 	float dot;
 

```
