# Diff: `code/ui/ui_players.c`
**Canonical:** `wolfcamql-src` (sha256 `9cf5dc946901...`, 37603 bytes)

## Variants

### `quake3-source`  — sha256 `d7734c28ae0f...`, 35844 bytes

_Diff stat: +51 / -101 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_players.c	2026-04-16 20:02:25.818963600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\ui\ui_players.c	2026-04-16 20:02:19.987145400 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -89,13 +89,15 @@
 	}
 
 	if ( weaponNum == WP_MACHINEGUN || weaponNum == WP_GAUNTLET || weaponNum == WP_BFG ) {
-		COM_StripExtension( item->world_model[0], path, sizeof(path) );
-		Q_strcat( path, sizeof(path), "_barrel.md3" );
+		strcpy( path, item->world_model[0] );
+		COM_StripExtension( path, path );
+		strcat( path, "_barrel.md3" );
 		pi->barrelModel = trap_R_RegisterModel( path );
 	}
 
-	COM_StripExtension( item->world_model[0], path, sizeof(path) );
-	Q_strcat( path, sizeof(path), "_flash.md3" );
+	strcpy( path, item->world_model[0] );
+	COM_StripExtension( path, path );
+	strcat( path, "_flash.md3" );
 	pi->flashModel = trap_R_RegisterModel( path );
 
 	switch( weaponNum ) {
@@ -331,8 +333,8 @@
 	}
 
 	// cast away const because of compiler problems
-	MatrixMultiply( entity->axis, lerped.axis, tempAxis );
-	MatrixMultiply( tempAxis, ((refEntity_t *)parent)->axis, entity->axis );
+	MatrixMultiply( entity->axis, ((refEntity_t *)parent)->axis, tempAxis );
+	MatrixMultiply( lerped.axis, tempAxis, entity->axis );
 }
 
 
@@ -364,7 +366,7 @@
 ===============
 */
 static void UI_RunLerpFrame( playerInfo_t *ci, lerpFrame_t *lf, int newAnimation ) {
-	int			f, numFrames;
+	int			f;
 	animation_t	*anim;
 
 	// see if the animation sequence is switching
@@ -380,40 +382,25 @@
 
 		// get the next frame based on the animation
 		anim = lf->animation;
-		if ( !anim->frameLerp ) {
-			return;         // shouldn't happen
-		}
 		if ( dp_realtime < lf->animationTime ) {
 			lf->frameTime = lf->animationTime;		// initial lerp
 		} else {
 			lf->frameTime = lf->oldFrameTime + anim->frameLerp;
 		}
 		f = ( lf->frameTime - lf->animationTime ) / anim->frameLerp;
-		numFrames = anim->numFrames;
-		if (anim->flipflop) {
-			numFrames *= 2;
-		}
-		if ( f >= numFrames ) {
-			f -= numFrames;
+		if ( f >= anim->numFrames ) {
+			f -= anim->numFrames;
 			if ( anim->loopFrames ) {
 				f %= anim->loopFrames;
 				f += anim->numFrames - anim->loopFrames;
 			} else {
-				f = numFrames - 1;
+				f = anim->numFrames - 1;
 				// the animation is stuck at the end, so it
 				// can immediately transition to another sequence
 				lf->frameTime = dp_realtime;
 			}
 		}
-		if ( anim->reversed ) {
-			lf->frame = anim->firstFrame + anim->numFrames - 1 - f;
-		}
-		else if (anim->flipflop && f>=anim->numFrames) {
-			lf->frame = anim->firstFrame + anim->numFrames - 1 - (f%anim->numFrames);
-		}
-		else {
-			lf->frame = anim->firstFrame + f;
-		}
+		lf->frame = anim->firstFrame + f;
 		if ( dp_realtime > lf->frameTime ) {
 			lf->frameTime = dp_realtime;
 		}
@@ -631,16 +618,6 @@
 	UI_SwingAngles( dest, 15, 30, 0.1f, &pi->torso.pitchAngle, &pi->torso.pitching );
 	torsoAngles[PITCH] = pi->torso.pitchAngle;
 
-	if ( pi->fixedtorso ) {
-		torsoAngles[PITCH] = 0.0f;
-	}
-
-	if ( pi->fixedlegs ) {
-		legsAngles[YAW] = torsoAngles[YAW];
-		legsAngles[PITCH] = 0.0f;
-		legsAngles[ROLL] = 0.0f;
-	}
-
 	// pull the angles back out of the hierarchial chain
 	AnglesSubtract( headAngles, torsoAngles, headAngles );
 	AnglesSubtract( torsoAngles, legsAngles, torsoAngles );
@@ -713,12 +690,12 @@
 */
 void UI_DrawPlayer( float x, float y, float w, float h, playerInfo_t *pi, int time ) {
 	refdef_t		refdef;
-	refEntity_t		legs = {0};
-	refEntity_t		torso = {0};
-	refEntity_t		head = {0};
-	refEntity_t		gun = {0};
-	refEntity_t		barrel = {0};
-	refEntity_t		flash = {0};
+	refEntity_t		legs;
+	refEntity_t		torso;
+	refEntity_t		head;
+	refEntity_t		gun;
+	refEntity_t		barrel;
+	refEntity_t		flash;
 	vec3_t			origin;
 	int				renderfx;
 	vec3_t			mins = {-16, -16, -24};
@@ -737,10 +714,10 @@
 
 	dp_realtime = time;
 
-	if ( pi->pendingWeapon != WP_NUM_WEAPONS && dp_realtime > pi->weaponTimer ) {
+	if ( pi->pendingWeapon != -1 && dp_realtime > pi->weaponTimer ) {
 		pi->weapon = pi->pendingWeapon;
 		pi->lastWeapon = pi->pendingWeapon;
-		pi->pendingWeapon = WP_NUM_WEAPONS;
+		pi->pendingWeapon = -1;
 		pi->weaponTimer = 0;
 		if( pi->currentWeapon != pi->weapon ) {
 			trap_S_StartLocalSound( weaponChangeSound, CHAN_LOCAL );
@@ -765,9 +742,9 @@
 	refdef.width = w;
 	refdef.height = h;
 
-	refdef.fov_x = (int)((float)refdef.width / uiInfo.uiDC.xscale / 640.0f * 90.0f);
-	xx = refdef.width / uiInfo.uiDC.xscale / tan( refdef.fov_x / 360 * M_PI );
-	refdef.fov_y = atan2( refdef.height / uiInfo.uiDC.yscale, xx );
+	refdef.fov_x = (int)((float)refdef.width / 640.0f * 90.0f);
+	xx = refdef.width / tan( refdef.fov_x / 360 * M_PI );
+	refdef.fov_y = atan2( refdef.height, xx );
 	refdef.fov_y *= ( 360 / (float)M_PI );
 
 	// calculate distance so the player nearly fills the box
@@ -868,6 +845,10 @@
 		angles[YAW] = 0;
 		angles[PITCH] = 0;
 		angles[ROLL] = UI_MachinegunSpinAngle( pi );
+		if( pi->realWeapon == WP_GAUNTLET || pi->realWeapon == WP_BFG ) {
+			angles[PITCH] = angles[ROLL];
+			angles[ROLL] = 0;
+		}
 		AnglesToAxis( angles, barrel.axis );
 
 		UI_PositionRotatedEntityOnTag( &barrel, &gun, pi->weaponModel, "tag_barrel");
@@ -926,7 +907,7 @@
 static qboolean	UI_FileExists(const char *filename) {
 	int len;
 
-	len = trap_FS_FOpenFile( filename, NULL, FS_READ );
+	len = trap_FS_FOpenFile( filename, 0, FS_READ );
 	if (len>0) {
 		return qtrue;
 	}
@@ -991,7 +972,7 @@
 ==========================
 */
 static qboolean	UI_RegisterClientSkin( playerInfo_t *pi, const char *modelName, const char *skinName, const char *headModelName, const char *headSkinName , const char *teamName) {
-	char		filename[MAX_QPATH];
+	char		filename[MAX_QPATH*2];
 
 	if (teamName && *teamName) {
 		Com_sprintf( filename, sizeof( filename ), "models/players/%s/%s/lower_%s.skin", modelName, teamName, skinName );
@@ -1040,7 +1021,7 @@
 UI_ParseAnimationFile
 ======================
 */
-static qboolean UI_ParseAnimationFile( const char *filename, playerInfo_t *pi ) {
+static qboolean UI_ParseAnimationFile( const char *filename, animation_t *animations ) {
 	char		*text_p, *prev;
 	int			len;
 	int			i;
@@ -1049,15 +1030,9 @@
 	int			skip;
 	char		text[20000];
 	fileHandle_t	f;
-	animation_t *animations;
-
-	animations = pi->animations;
 
 	memset( animations, 0, sizeof( animation_t ) * MAX_ANIMATIONS );
 
-	pi->fixedlegs = qfalse;
-	pi->fixedtorso = qfalse;
-
 	// load the file
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( len <= 0 ) {
@@ -1065,7 +1040,6 @@
 	}
 	if ( len >= ( sizeof( text ) - 1 ) ) {
 		Com_Printf( "File %s too long\n", filename );
-		trap_FS_FCloseFile( f );
 		return qfalse;
 	}
 	trap_FS_Read( text, len, f );
@@ -1082,35 +1056,29 @@
 	while ( 1 ) {
 		prev = text_p;	// so we can unget
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		if ( !Q_stricmp( token, "footsteps" ) ) {
 			token = COM_Parse( &text_p );
-			if ( !token[0] ) {
+			if ( !token ) {
 				break;
 			}
 			continue;
 		} else if ( !Q_stricmp( token, "headoffset" ) ) {
 			for ( i = 0 ; i < 3 ; i++ ) {
 				token = COM_Parse( &text_p );
-				if ( !token[0] ) {
+				if ( !token ) {
 					break;
 				}
 			}
 			continue;
 		} else if ( !Q_stricmp( token, "sex" ) ) {
 			token = COM_Parse( &text_p );
-			if ( !token[0] ) {
+			if ( !token ) {
 				break;
 			}
 			continue;
-		} else if ( !Q_stricmp( token, "fixedlegs" ) ) {
-			pi->fixedlegs = qtrue;
-			continue;
-		} else if ( !Q_stricmp( token, "fixedtorso" ) ) {
-			pi->fixedtorso = qtrue;
-			continue;
 		}
 
 		// if it is a number, start parsing animations
@@ -1119,24 +1087,14 @@
 			break;
 		}
 
-		Com_Printf( "unknown token '%s' in %s\n", token, filename );
+		Com_Printf( "unknown token '%s' is %s\n", token, filename );
 	}
 
 	// read information for each frame
 	for ( i = 0 ; i < MAX_ANIMATIONS ; i++ ) {
 
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
-			if( i >= TORSO_GETFLAG && i <= TORSO_NEGATIVE ) {
-				animations[i].firstFrame = animations[TORSO_GESTURE].firstFrame;
-				animations[i].frameLerp = animations[TORSO_GESTURE].frameLerp;
-				animations[i].initialLerp = animations[TORSO_GESTURE].initialLerp;
-				animations[i].loopFrames = animations[TORSO_GESTURE].loopFrames;
-				animations[i].numFrames = animations[TORSO_GESTURE].numFrames;
-				animations[i].reversed = qfalse;
-				animations[i].flipflop = qfalse;
-				continue;
-			}
+		if ( !token ) {
 			break;
 		}
 		animations[i].firstFrame = atoi( token );
@@ -1144,32 +1102,24 @@
 		if ( i == LEGS_WALKCR ) {
 			skip = animations[LEGS_WALKCR].firstFrame - animations[TORSO_GESTURE].firstFrame;
 		}
-		if ( i >= LEGS_WALKCR && i<TORSO_GETFLAG) {
+		if ( i >= LEGS_WALKCR ) {
 			animations[i].firstFrame -= skip;
 		}
 
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		animations[i].numFrames = atoi( token );
 
-		animations[i].reversed = qfalse;
-		animations[i].flipflop = qfalse;
-		// if numFrames is negative the animation is reversed
-		if (animations[i].numFrames < 0) {
-			animations[i].numFrames = -animations[i].numFrames;
-			animations[i].reversed = qtrue;
-		}
-
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		animations[i].loopFrames = atoi( token );
 
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		fps = atof( token );
@@ -1181,7 +1131,7 @@
 	}
 
 	if ( i != MAX_ANIMATIONS ) {
-		Com_Printf( "Error parsing animation file: %s\n", filename );
+		Com_Printf( "Error parsing animation file: %s", filename );
 		return qfalse;
 	}
 
@@ -1253,7 +1203,7 @@
 		}
 	}
 
-	if (headModelName[0] == '*' ) {
+	if (headModelName && headModelName[0] == '*' ) {
 		Com_sprintf( filename, sizeof( filename ), "models/players/heads/%s/%s.md3", &headModelName[1], &headModelName[1] );
 	}
 	else {
@@ -1280,9 +1230,9 @@
 
 	// load the animations
 	Com_sprintf( filename, sizeof( filename ), "models/players/%s/animation.cfg", modelName );
-	if ( !UI_ParseAnimationFile( filename, pi ) ) {
+	if ( !UI_ParseAnimationFile( filename, pi->animations ) ) {
 		Com_sprintf( filename, sizeof( filename ), "models/players/characters/%s/animation.cfg", modelName );
-		if ( !UI_ParseAnimationFile( filename, pi ) ) {
+		if ( !UI_ParseAnimationFile( filename, pi->animations ) ) {
 			Com_Printf( "Failed to load animation file %s\n", filename );
 			return qfalse;
 		}
@@ -1303,7 +1253,7 @@
 	pi->weapon = WP_MACHINEGUN;
 	pi->currentWeapon = pi->weapon;
 	pi->lastWeapon = pi->weapon;
-	pi->pendingWeapon = WP_NUM_WEAPONS;
+	pi->pendingWeapon = -1;
 	pi->weaponTimer = 0;
 	pi->chat = qfalse;
 	pi->newModel = qtrue;
@@ -1342,11 +1292,11 @@
 		pi->torso.yawAngle = viewAngles[YAW];
 		pi->torso.yawing = qfalse;
 
-		if ( weaponNumber != WP_NUM_WEAPONS ) {
+		if ( weaponNumber != -1 ) {
 			pi->weapon = weaponNumber;
 			pi->currentWeapon = weaponNumber;
 			pi->lastWeapon = weaponNumber;
-			pi->pendingWeapon = WP_NUM_WEAPONS;
+			pi->pendingWeapon = -1;
 			pi->weaponTimer = 0;
 			UI_PlayerInfo_SetWeapon( pi, pi->weapon );
 		}
@@ -1355,8 +1305,8 @@
 	}
 
 	// weapon
-	if ( weaponNumber == WP_NUM_WEAPONS ) {
-		pi->pendingWeapon = WP_NUM_WEAPONS;
+	if ( weaponNumber == -1 ) {
+		pi->pendingWeapon = -1;
 		pi->weaponTimer = 0;
 	}
 	else if ( weaponNumber != WP_NONE ) {

```

### `ioquake3`  — sha256 `c204dc1077a8...`, 37596 bytes

_Diff stat: +3 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_players.c	2026-04-16 20:02:25.818963600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\ui\ui_players.c	2026-04-16 20:02:21.813550900 +0100
@@ -381,7 +381,7 @@
 		// get the next frame based on the animation
 		anim = lf->animation;
 		if ( !anim->frameLerp ) {
-			return;         // shouldn't happen
+			return;		// shouldn't happen
 		}
 		if ( dp_realtime < lf->animationTime ) {
 			lf->frameTime = lf->animationTime;		// initial lerp
@@ -389,6 +389,7 @@
 			lf->frameTime = lf->oldFrameTime + anim->frameLerp;
 		}
 		f = ( lf->frameTime - lf->animationTime ) / anim->frameLerp;
+
 		numFrames = anim->numFrames;
 		if (anim->flipflop) {
 			numFrames *= 2;
@@ -771,7 +772,7 @@
 	refdef.fov_y *= ( 360 / (float)M_PI );
 
 	// calculate distance so the player nearly fills the box
-	len = 0.7 * ( maxs[2] - mins[2] );		
+	len = 0.7 * ( maxs[2] - mins[2] );
 	origin[0] = len / tan( DEG2RAD(refdef.fov_x) * 0.5 );
 	origin[1] = 0.5 * ( mins[1] + maxs[1] );
 	origin[2] = -0.5 * ( mins[2] + maxs[2] );

```

### `openarena-engine`  — sha256 `b9600ea08774...`, 36054 bytes

_Diff stat: +37 / -86 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\ui\ui_players.c	2026-04-16 20:02:25.818963600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\ui\ui_players.c	2026-04-16 22:48:25.960096000 +0100
@@ -89,13 +89,15 @@
 	}
 
 	if ( weaponNum == WP_MACHINEGUN || weaponNum == WP_GAUNTLET || weaponNum == WP_BFG ) {
-		COM_StripExtension( item->world_model[0], path, sizeof(path) );
-		Q_strcat( path, sizeof(path), "_barrel.md3" );
+		strcpy( path, item->world_model[0] );
+		COM_StripExtension(path, path, sizeof(path));
+		strcat( path, "_barrel.md3" );
 		pi->barrelModel = trap_R_RegisterModel( path );
 	}
 
-	COM_StripExtension( item->world_model[0], path, sizeof(path) );
-	Q_strcat( path, sizeof(path), "_flash.md3" );
+	strcpy( path, item->world_model[0] );
+	COM_StripExtension(path, path, sizeof(path));
+	strcat( path, "_flash.md3" );
 	pi->flashModel = trap_R_RegisterModel( path );
 
 	switch( weaponNum ) {
@@ -304,7 +306,7 @@
 	}
 
 	// cast away const because of compiler problems
-	MatrixMultiply( lerped.axis, ((refEntity_t*)parent)->axis, entity->axis );
+	Q_MatrixMultiply( lerped.axis, ((refEntity_t*)parent)->axis, entity->axis );
 	entity->backlerp = parent->backlerp;
 }
 
@@ -331,8 +333,8 @@
 	}
 
 	// cast away const because of compiler problems
-	MatrixMultiply( entity->axis, lerped.axis, tempAxis );
-	MatrixMultiply( tempAxis, ((refEntity_t *)parent)->axis, entity->axis );
+	Q_MatrixMultiply( entity->axis, ((refEntity_t *)parent)->axis, tempAxis );
+	Q_MatrixMultiply( lerped.axis, tempAxis, entity->axis );
 }
 
 
@@ -364,7 +366,7 @@
 ===============
 */
 static void UI_RunLerpFrame( playerInfo_t *ci, lerpFrame_t *lf, int newAnimation ) {
-	int			f, numFrames;
+	int			f;
 	animation_t	*anim;
 
 	// see if the animation sequence is switching
@@ -380,40 +382,25 @@
 
 		// get the next frame based on the animation
 		anim = lf->animation;
-		if ( !anim->frameLerp ) {
-			return;         // shouldn't happen
-		}
 		if ( dp_realtime < lf->animationTime ) {
 			lf->frameTime = lf->animationTime;		// initial lerp
 		} else {
 			lf->frameTime = lf->oldFrameTime + anim->frameLerp;
 		}
 		f = ( lf->frameTime - lf->animationTime ) / anim->frameLerp;
-		numFrames = anim->numFrames;
-		if (anim->flipflop) {
-			numFrames *= 2;
-		}
-		if ( f >= numFrames ) {
-			f -= numFrames;
+		if ( f >= anim->numFrames ) {
+			f -= anim->numFrames;
 			if ( anim->loopFrames ) {
 				f %= anim->loopFrames;
 				f += anim->numFrames - anim->loopFrames;
 			} else {
-				f = numFrames - 1;
+				f = anim->numFrames - 1;
 				// the animation is stuck at the end, so it
 				// can immediately transition to another sequence
 				lf->frameTime = dp_realtime;
 			}
 		}
-		if ( anim->reversed ) {
-			lf->frame = anim->firstFrame + anim->numFrames - 1 - f;
-		}
-		else if (anim->flipflop && f>=anim->numFrames) {
-			lf->frame = anim->firstFrame + anim->numFrames - 1 - (f%anim->numFrames);
-		}
-		else {
-			lf->frame = anim->firstFrame + f;
-		}
+		lf->frame = anim->firstFrame + f;
 		if ( dp_realtime > lf->frameTime ) {
 			lf->frameTime = dp_realtime;
 		}
@@ -631,16 +618,6 @@
 	UI_SwingAngles( dest, 15, 30, 0.1f, &pi->torso.pitchAngle, &pi->torso.pitching );
 	torsoAngles[PITCH] = pi->torso.pitchAngle;
 
-	if ( pi->fixedtorso ) {
-		torsoAngles[PITCH] = 0.0f;
-	}
-
-	if ( pi->fixedlegs ) {
-		legsAngles[YAW] = torsoAngles[YAW];
-		legsAngles[PITCH] = 0.0f;
-		legsAngles[ROLL] = 0.0f;
-	}
-
 	// pull the angles back out of the hierarchial chain
 	AnglesSubtract( headAngles, torsoAngles, headAngles );
 	AnglesSubtract( torsoAngles, legsAngles, torsoAngles );
@@ -713,12 +690,12 @@
 */
 void UI_DrawPlayer( float x, float y, float w, float h, playerInfo_t *pi, int time ) {
 	refdef_t		refdef;
-	refEntity_t		legs = {0};
-	refEntity_t		torso = {0};
-	refEntity_t		head = {0};
-	refEntity_t		gun = {0};
-	refEntity_t		barrel = {0};
-	refEntity_t		flash = {0};
+	refEntity_t		legs;
+	refEntity_t		torso;
+	refEntity_t		head;
+	refEntity_t		gun;
+	refEntity_t		barrel;
+	refEntity_t		flash;
 	vec3_t			origin;
 	int				renderfx;
 	vec3_t			mins = {-16, -16, -24};
@@ -771,7 +748,7 @@
 	refdef.fov_y *= ( 360 / (float)M_PI );
 
 	// calculate distance so the player nearly fills the box
-	len = 0.7 * ( maxs[2] - mins[2] );		
+	len = 0.7 * ( maxs[2] - mins[2] );
 	origin[0] = len / tan( DEG2RAD(refdef.fov_x) * 0.5 );
 	origin[1] = 0.5 * ( mins[1] + maxs[1] );
 	origin[2] = -0.5 * ( mins[2] + maxs[2] );
@@ -868,6 +845,10 @@
 		angles[YAW] = 0;
 		angles[PITCH] = 0;
 		angles[ROLL] = UI_MachinegunSpinAngle( pi );
+		if( pi->realWeapon == WP_GAUNTLET || pi->realWeapon == WP_BFG ) {
+			angles[PITCH] = angles[ROLL];
+			angles[ROLL] = 0;
+		}
 		AnglesToAxis( angles, barrel.axis );
 
 		UI_PositionRotatedEntityOnTag( &barrel, &gun, pi->weaponModel, "tag_barrel");
@@ -1040,7 +1021,7 @@
 UI_ParseAnimationFile
 ======================
 */
-static qboolean UI_ParseAnimationFile( const char *filename, playerInfo_t *pi ) {
+static qboolean UI_ParseAnimationFile( const char *filename, animation_t *animations ) {
 	char		*text_p, *prev;
 	int			len;
 	int			i;
@@ -1049,15 +1030,9 @@
 	int			skip;
 	char		text[20000];
 	fileHandle_t	f;
-	animation_t *animations;
-
-	animations = pi->animations;
 
 	memset( animations, 0, sizeof( animation_t ) * MAX_ANIMATIONS );
 
-	pi->fixedlegs = qfalse;
-	pi->fixedtorso = qfalse;
-
 	// load the file
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( len <= 0 ) {
@@ -1082,35 +1057,29 @@
 	while ( 1 ) {
 		prev = text_p;	// so we can unget
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		if ( !Q_stricmp( token, "footsteps" ) ) {
 			token = COM_Parse( &text_p );
-			if ( !token[0] ) {
+			if ( !token ) {
 				break;
 			}
 			continue;
 		} else if ( !Q_stricmp( token, "headoffset" ) ) {
 			for ( i = 0 ; i < 3 ; i++ ) {
 				token = COM_Parse( &text_p );
-				if ( !token[0] ) {
+				if ( !token ) {
 					break;
 				}
 			}
 			continue;
 		} else if ( !Q_stricmp( token, "sex" ) ) {
 			token = COM_Parse( &text_p );
-			if ( !token[0] ) {
+			if ( !token ) {
 				break;
 			}
 			continue;
-		} else if ( !Q_stricmp( token, "fixedlegs" ) ) {
-			pi->fixedlegs = qtrue;
-			continue;
-		} else if ( !Q_stricmp( token, "fixedtorso" ) ) {
-			pi->fixedtorso = qtrue;
-			continue;
 		}
 
 		// if it is a number, start parsing animations
@@ -1126,17 +1095,7 @@
 	for ( i = 0 ; i < MAX_ANIMATIONS ; i++ ) {
 
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
-			if( i >= TORSO_GETFLAG && i <= TORSO_NEGATIVE ) {
-				animations[i].firstFrame = animations[TORSO_GESTURE].firstFrame;
-				animations[i].frameLerp = animations[TORSO_GESTURE].frameLerp;
-				animations[i].initialLerp = animations[TORSO_GESTURE].initialLerp;
-				animations[i].loopFrames = animations[TORSO_GESTURE].loopFrames;
-				animations[i].numFrames = animations[TORSO_GESTURE].numFrames;
-				animations[i].reversed = qfalse;
-				animations[i].flipflop = qfalse;
-				continue;
-			}
+		if ( !token ) {
 			break;
 		}
 		animations[i].firstFrame = atoi( token );
@@ -1144,32 +1103,24 @@
 		if ( i == LEGS_WALKCR ) {
 			skip = animations[LEGS_WALKCR].firstFrame - animations[TORSO_GESTURE].firstFrame;
 		}
-		if ( i >= LEGS_WALKCR && i<TORSO_GETFLAG) {
+		if ( i >= LEGS_WALKCR ) {
 			animations[i].firstFrame -= skip;
 		}
 
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		animations[i].numFrames = atoi( token );
 
-		animations[i].reversed = qfalse;
-		animations[i].flipflop = qfalse;
-		// if numFrames is negative the animation is reversed
-		if (animations[i].numFrames < 0) {
-			animations[i].numFrames = -animations[i].numFrames;
-			animations[i].reversed = qtrue;
-		}
-
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		animations[i].loopFrames = atoi( token );
 
 		token = COM_Parse( &text_p );
-		if ( !token[0] ) {
+		if ( !token ) {
 			break;
 		}
 		fps = atof( token );
@@ -1280,9 +1231,9 @@
 
 	// load the animations
 	Com_sprintf( filename, sizeof( filename ), "models/players/%s/animation.cfg", modelName );
-	if ( !UI_ParseAnimationFile( filename, pi ) ) {
+	if ( !UI_ParseAnimationFile( filename, pi->animations ) ) {
 		Com_sprintf( filename, sizeof( filename ), "models/players/characters/%s/animation.cfg", modelName );
-		if ( !UI_ParseAnimationFile( filename, pi ) ) {
+		if ( !UI_ParseAnimationFile( filename, pi->animations ) ) {
 			Com_Printf( "Failed to load animation file %s\n", filename );
 			return qfalse;
 		}

```

### `openarena-gamecode`  — sha256 `ce885deaa66d...`, 56434 bytes

_Diff stat: +802 / -37 lines_

_(full diff is 26847 bytes — see files directly)_
