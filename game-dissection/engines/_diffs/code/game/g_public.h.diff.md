# Diff: `code/game/g_public.h`
**Canonical:** `wolfcamql-src` (sha256 `394616fedc73...`, 14998 bytes)

## Variants

### `quake3-source`  — sha256 `11d155ea41a0...`, 14794 bytes

_Diff stat: +6 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_public.h	2026-04-16 20:02:25.197155700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\game\g_public.h	2026-04-16 20:02:19.908574000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -54,8 +54,7 @@
 
 
 typedef struct {
-	entityState_t   unused;                 // apparently this field was put here accidentally
-	                                        //  (and is kept only for compatibility, as a struct pad)
+	entityState_t	s;				// communicated by server to clients
 
 	qboolean	linked;				// qfalse if not in any good cluster
 	int			linkcount;
@@ -83,9 +82,9 @@
 
 	// when a trace call is made and passEntityNum != ENTITYNUM_NONE,
 	// an ent will be excluded from testing if:
-	// ent->s.number == passEntityNum       (don't interact with self)
-	// ent->r.ownerNum == passEntityNum     (don't interact with your own missiles)
-	// entity[ent->r.ownerNum].r.ownerNum == passEntityNum  (don't interact with other missiles from owner)
+	// ent->s.number == passEntityNum	(don't interact with self)
+	// ent->s.ownerNum = passEntityNum	(don't interact with your own missiles)
+	// entity[ent->s.ownerNum].ownerNum = passEntityNum	(don't interact with other missiles from owner)
 	int			ownerNum;
 } entityShared_t;
 
@@ -226,14 +225,10 @@
 
 	G_TRACECAPSULE,	// ( trace_t *results, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask );
 	G_ENTITY_CONTACTCAPSULE,	// ( const vec3_t mins, const vec3_t maxs, const gentity_t *ent );
-
+	
 	// 1.32
 	G_FS_SEEK,
 
-#if Q3_VM
-	acos = 114,
-#endif
-
 	BOTLIB_SETUP = 200,				// ( void );
 	BOTLIB_SHUTDOWN,				// ( void );
 	BOTLIB_LIBVAR_SET,

```

### `openarena-engine`  — sha256 `c3fa27ed5a08...`, 14905 bytes
Also identical in: ioquake3

_Diff stat: +6 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_public.h	2026-04-16 20:02:25.197155700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\g_public.h	2026-04-16 22:48:25.748537400 +0100
@@ -54,8 +54,8 @@
 
 
 typedef struct {
-	entityState_t   unused;                 // apparently this field was put here accidentally
-	                                        //  (and is kept only for compatibility, as a struct pad)
+	entityState_t	unused;			// apparently this field was put here accidentally
+									//  (and is kept only for compatibility, as a struct pad)
 
 	qboolean	linked;				// qfalse if not in any good cluster
 	int			linkcount;
@@ -83,9 +83,9 @@
 
 	// when a trace call is made and passEntityNum != ENTITYNUM_NONE,
 	// an ent will be excluded from testing if:
-	// ent->s.number == passEntityNum       (don't interact with self)
-	// ent->r.ownerNum == passEntityNum     (don't interact with your own missiles)
-	// entity[ent->r.ownerNum].r.ownerNum == passEntityNum  (don't interact with other missiles from owner)
+	// ent->s.number == passEntityNum	(don't interact with self)
+	// ent->r.ownerNum == passEntityNum	(don't interact with your own missiles)
+	// entity[ent->r.ownerNum].r.ownerNum == passEntityNum	(don't interact with other missiles from owner)
 	int			ownerNum;
 } entityShared_t;
 
@@ -226,14 +226,10 @@
 
 	G_TRACECAPSULE,	// ( trace_t *results, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask );
 	G_ENTITY_CONTACTCAPSULE,	// ( const vec3_t mins, const vec3_t maxs, const gentity_t *ent );
-
+	
 	// 1.32
 	G_FS_SEEK,
 
-#if Q3_VM
-	acos = 114,
-#endif
-
 	BOTLIB_SETUP = 200,				// ( void );
 	BOTLIB_SHUTDOWN,				// ( void );
 	BOTLIB_LIBVAR_SET,

```

### `quake3e`  — sha256 `3544ba222847...`, 15152 bytes

_Diff stat: +26 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_public.h	2026-04-16 20:02:25.197155700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\game\g_public.h	2026-04-16 20:02:26.917521900 +0100
@@ -48,23 +48,22 @@
 #define SVF_NOTSINGLECLIENT		0x00000800	// send entity to everyone but one client
 											// (entityShared_t->singleClient)
 
-
+#define SVF_SELF_PORTAL2		0x00020000  // merge a second pvs at entity->r.s.origin2 into snapshots
 
 //===============================================================
 
 
 typedef struct {
-	entityState_t   unused;                 // apparently this field was put here accidentally
-	                                        //  (and is kept only for compatibility, as a struct pad)
+	entityState_t	s;				// communicated by server to clients
 
 	qboolean	linked;				// qfalse if not in any good cluster
 	int			linkcount;
 
 	int			svFlags;			// SVF_NOCLIENT, SVF_BROADCAST, etc
 
-	// only send to this client when SVF_SINGLECLIENT is set	
+	// only send to this client when SVF_SINGLECLIENT is set
 	// if SVF_CLIENTMASK is set, use bitmask for clients to send to (maxclients must be <= 32, up to the mod to enforce this)
-	int			singleClient;		
+	int			singleClient;
 
 	qboolean	bmodel;				// if false, assume an explicit mins / maxs bounding box
 									// only set by trap_SetBrushModel
@@ -77,15 +76,15 @@
 	// currentOrigin will be used for all collision detection and world linking.
 	// it will not necessarily be the same as the trajectory evaluation for the current
 	// time, because each entity must be moved one at a time after time is advanced
-	// to avoid simultanious collision issues
+	// to avoid simultaneous collision issues
 	vec3_t		currentOrigin;
 	vec3_t		currentAngles;
 
 	// when a trace call is made and passEntityNum != ENTITYNUM_NONE,
 	// an ent will be excluded from testing if:
-	// ent->s.number == passEntityNum       (don't interact with self)
-	// ent->r.ownerNum == passEntityNum     (don't interact with your own missiles)
-	// entity[ent->r.ownerNum].r.ownerNum == passEntityNum  (don't interact with other missiles from owner)
+	// ent->s.number == passEntityNum	(don't interact with self)
+	// ent->s.ownerNum = passEntityNum	(don't interact with your own missiles)
+	// entity[ent->s.ownerNum].ownerNum = passEntityNum	(don't interact with other missiles from owner)
 	int			ownerNum;
 } entityShared_t;
 
@@ -151,7 +150,7 @@
 	G_DROP_CLIENT,		// ( int clientNum, const char *reason );
 	// kick a client off the server with a message
 
-	G_SEND_SERVER_COMMAND,	// ( int clientNum, const char *fmt, ... );
+	G_SEND_SERVER_COMMAND,	// ( int clientNum, const char *text );
 	// reliably sends a command string to be interpreted by the given
 	// client.  If clientNum is -1, it will be sent to all clients
 
@@ -196,7 +195,7 @@
 	// if it is not passed to linkentity.  If the size, position, or
 	// solidity changes, it must be relinked.
 
-	G_UNLINKENTITY,		// ( gentity_t *ent );		
+	G_UNLINKENTITY,		// ( gentity_t *ent );
 	// call before removing an interactive entity
 
 	G_ENTITIES_IN_BOX,	// ( const vec3_t mins, const vec3_t maxs, gentity_t **list, int maxcount );
@@ -230,9 +229,13 @@
 	// 1.32
 	G_FS_SEEK,
 
-#if Q3_VM
-	acos = 114,
-#endif
+	G_MATRIXMULTIPLY = 107,
+	G_ANGLEVECTORS,
+	G_PERPENDICULARVECTOR,
+	G_FLOOR,
+	G_CEIL,
+	G_TESTPRINTINT,
+	G_TESTPRINTFLOAT,
 
 	BOTLIB_SETUP = 200,				// ( void );
 	BOTLIB_SHUTDOWN,				// ( void );
@@ -391,7 +394,11 @@
 	BOTLIB_PC_LOAD_SOURCE,
 	BOTLIB_PC_FREE_SOURCE,
 	BOTLIB_PC_READ_TOKEN,
-	BOTLIB_PC_SOURCE_FILE_AND_LINE
+	BOTLIB_PC_SOURCE_FILE_AND_LINE,
+
+	// engine extensions
+	G_CVAR_SETDESCRIPTION,
+	G_TRAP_GETVALUE = COM_TRAP_GETVALUE
 
 } gameImport_t;
 
@@ -405,7 +412,7 @@
 	// The game should call G_GET_ENTITY_TOKEN to parse through all the
 	// entity configuration text and spawn gentities.
 
-	GAME_SHUTDOWN,	// (void);
+	GAME_SHUTDOWN,	// ( int restart );
 
 	GAME_CLIENT_CONNECT,	// ( int clientNum, qboolean firstTime, qboolean isBot );
 	// return NULL if the client is allowed to connect, otherwise return
@@ -429,6 +436,8 @@
 	// The game can issue trap_argc() / trap_argv() commands to get the command
 	// and parameters.  Return qfalse if the game doesn't recognize it as a command.
 
-	BOTAI_START_FRAME				// ( int time );
+	BOTAI_START_FRAME,				// ( int time );
+
+	GAME_EXPORT_LAST
 } gameExport_t;
 

```

### `openarena-gamecode`  — sha256 `852cf83c9bcc...`, 14815 bytes

_Diff stat: +5 / -10 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\g_public.h	2026-04-16 20:02:25.197155700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\game\g_public.h	2026-04-16 22:48:24.173988500 +0100
@@ -54,8 +54,7 @@
 
 
 typedef struct {
-	entityState_t   unused;                 // apparently this field was put here accidentally
-	                                        //  (and is kept only for compatibility, as a struct pad)
+	entityState_t	s;				// communicated by server to clients
 
 	qboolean	linked;				// qfalse if not in any good cluster
 	int			linkcount;
@@ -83,9 +82,9 @@
 
 	// when a trace call is made and passEntityNum != ENTITYNUM_NONE,
 	// an ent will be excluded from testing if:
-	// ent->s.number == passEntityNum       (don't interact with self)
-	// ent->r.ownerNum == passEntityNum     (don't interact with your own missiles)
-	// entity[ent->r.ownerNum].r.ownerNum == passEntityNum  (don't interact with other missiles from owner)
+	// ent->s.number == passEntityNum	(don't interact with self)
+	// ent->s.ownerNum = passEntityNum	(don't interact with your own missiles)
+	// entity[ent->s.ownerNum].ownerNum = passEntityNum	(don't interact with other missiles from owner)
 	int			ownerNum;
 } entityShared_t;
 
@@ -226,14 +225,10 @@
 
 	G_TRACECAPSULE,	// ( trace_t *results, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask );
 	G_ENTITY_CONTACTCAPSULE,	// ( const vec3_t mins, const vec3_t maxs, const gentity_t *ent );
-
+	
 	// 1.32
 	G_FS_SEEK,
 
-#if Q3_VM
-	acos = 114,
-#endif
-
 	BOTLIB_SETUP = 200,				// ( void );
 	BOTLIB_SHUTDOWN,				// ( void );
 	BOTLIB_LIBVAR_SET,

```
