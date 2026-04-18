# Diff: `code/q3_ui/ui_players.c`
**Canonical:** `wolfcamql-src` (sha256 `b5223dd84bf2...`, 33713 bytes)

## Variants

### `quake3-source`  — sha256 `25fdb8cbc879...`, 31193 bytes

_Diff stat: +48 / -136 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_players.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_players.c	2026-04-16 20:02:19.949613500 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -88,13 +88,15 @@
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
@@ -330,8 +332,8 @@
 	}
 
 	// cast away const because of compiler problems
-	MatrixMultiply( entity->axis, lerped.axis, tempAxis );
-	MatrixMultiply( tempAxis, ((refEntity_t *)parent)->axis, entity->axis );
+	MatrixMultiply( entity->axis, ((refEntity_t *)parent)->axis, tempAxis );
+	MatrixMultiply( lerped.axis, tempAxis, entity->axis );
 }
 
 
@@ -363,7 +365,7 @@
 ===============
 */
 static void UI_RunLerpFrame( playerInfo_t *ci, lerpFrame_t *lf, int newAnimation ) {
-	int			f, numFrames;
+	int			f;
 	animation_t	*anim;
 
 	// see if the animation sequence is switching
@@ -379,41 +381,25 @@
 
 		// get the next frame based on the animation
 		anim = lf->animation;
-		if ( !anim->frameLerp ) {
-			return;			// shouldn't happen
-		}
 		if ( dp_realtime < lf->animationTime ) {
 			lf->frameTime = lf->animationTime;		// initial lerp
 		} else {
 			lf->frameTime = lf->oldFrameTime + anim->frameLerp;
 		}
 		f = ( lf->frameTime - lf->animationTime ) / anim->frameLerp;
-
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
@@ -631,16 +617,6 @@
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
@@ -713,12 +689,12 @@
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
@@ -732,10 +708,10 @@
 
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
@@ -760,9 +736,9 @@
 	refdef.width = w;
 	refdef.height = h;
 
-	refdef.fov_x = (int)((float)refdef.width / uis.xscale / 640.0f * 90.0f);
-	xx = refdef.width / uis.xscale / tan( refdef.fov_x / 360 * M_PI );
-	refdef.fov_y = atan2( refdef.height / uis.yscale, xx );
+	refdef.fov_x = (int)((float)refdef.width / 640.0f * 90.0f);
+	xx = refdef.width / tan( refdef.fov_x / 360 * M_PI );
+	refdef.fov_y = atan2( refdef.height, xx );
 	refdef.fov_y *= ( 360 / M_PI );
 
 	// calculate distance so the player nearly fills the box
@@ -795,10 +771,6 @@
 	VectorCopy( origin, legs.lightingOrigin );
 	legs.renderfx = renderfx;
 	VectorCopy (legs.origin, legs.oldorigin);
-	legs.shaderRGBA[0] = 255;
-	legs.shaderRGBA[1] = 255;
-	legs.shaderRGBA[2] = 0;
-	legs.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &legs );
 
@@ -821,10 +793,6 @@
 	UI_PositionRotatedEntityOnTag( &torso, &legs, pi->legsModel, "tag_torso");
 
 	torso.renderfx = renderfx;
-	torso.shaderRGBA[0] = 255;
-	torso.shaderRGBA[1] = 255;
-	torso.shaderRGBA[2] = 150;
-	torso.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &torso );
 
@@ -871,6 +839,10 @@
 		angles[YAW] = 0;
 		angles[PITCH] = 0;
 		angles[ROLL] = UI_MachinegunSpinAngle( pi );
+		if( pi->realWeapon == WP_GAUNTLET || pi->realWeapon == WP_BFG ) {
+			angles[PITCH] = angles[ROLL];
+			angles[ROLL] = 0;
+		}
 		AnglesToAxis( angles, barrel.axis );
 
 		UI_PositionRotatedEntityOnTag( &barrel, &gun, pi->weaponModel, "tag_barrel");
@@ -952,7 +924,7 @@
 UI_ParseAnimationFile
 ======================
 */
-static qboolean UI_ParseAnimationFile( const char *filename, playerInfo_t *pi ) {
+static qboolean UI_ParseAnimationFile( const char *filename, animation_t *animations ) {
 	char		*text_p, *prev;
 	int			len;
 	int			i;
@@ -961,15 +933,9 @@
 	int			skip;
 	char		text[20000];
 	fileHandle_t	f;
-	animation_t	*animations;
-
-	animations = pi->animations;
 
 	memset( animations, 0, sizeof( animation_t ) * MAX_ANIMATIONS );
 
-	pi->fixedlegs = qfalse;
-	pi->fixedtorso = qfalse;
-
 	// load the file
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( len <= 0 ) {
@@ -977,7 +943,6 @@
 	}
 	if ( len >= ( sizeof( text ) - 1 ) ) {
 		Com_Printf( "File %s too long\n", filename );
-		trap_FS_FCloseFile( f );
 		return qfalse;
 	}
 	trap_FS_Read( text, len, f );
@@ -992,35 +957,29 @@
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
@@ -1029,24 +988,14 @@
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
@@ -1054,32 +1003,24 @@
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
@@ -1091,7 +1032,7 @@
 	}
 
 	if ( i != MAX_ANIMATIONS ) {
-		Com_Printf( "Error parsing animation file: %s\n", filename );
+		Com_Printf( "Error parsing animation file: %s", filename );
 		return qfalse;
 	}
 
@@ -1153,8 +1094,7 @@
 	}
 
 	// if any skins failed to load, fall back to default
-	//if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
-	if (!UI_RegisterClientSkin(pi, modelName, "color")) {
+	if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
 		if ( !UI_RegisterClientSkin( pi, modelName, "default" ) ) {
 			Com_Printf( "Failed to load skin file: %s : %s\n", modelName, skinName );
 			return qfalse;
@@ -1163,7 +1103,7 @@
 
 	// load the animations
 	Com_sprintf( filename, sizeof( filename ), "models/players/%s/animation.cfg", modelName );
-	if ( !UI_ParseAnimationFile( filename, pi ) ) {
+	if ( !UI_ParseAnimationFile( filename, pi->animations ) ) {
 		Com_Printf( "Failed to load animation file %s\n", filename );
 		return qfalse;
 	}
@@ -1183,7 +1123,7 @@
 	pi->weapon = WP_MACHINEGUN;
 	pi->currentWeapon = pi->weapon;
 	pi->lastWeapon = pi->weapon;
-	pi->pendingWeapon = WP_NUM_WEAPONS;
+	pi->pendingWeapon = -1;
 	pi->weaponTimer = 0;
 	pi->chat = qfalse;
 	pi->newModel = qtrue;
@@ -1199,37 +1139,9 @@
 void UI_PlayerInfo_SetInfo( playerInfo_t *pi, int legsAnim, int torsoAnim, vec3_t viewAngles, vec3_t moveAngles, weapon_t weaponNumber, qboolean chat ) {
 	int			currentAnim;
 	weapon_t	weaponNum;
-	int c;
 
 	pi->chat = chat;
 
-	c = (int)trap_Cvar_VariableValue( "color1" );
-
-	VectorClear( pi->color1 );
-
-	//FIXME wc ql
-	if( c < 1 || c > 7 ) {
-		VectorSet( pi->color1, 1, 1, 1 );
-	}
-	else {
-		if( c & 1 ) {
-			pi->color1[2] = 1.0f;
-		}
-
-		if( c & 2 ) {
-			pi->color1[1] = 1.0f;
-		}
-
-		if( c & 4 ) {
-			pi->color1[0] = 1.0f;
-		}
-	}
-
-	pi->c1RGBA[0] = 255 * pi->color1[0];
-	pi->c1RGBA[1] = 255 * pi->color1[1];
-	pi->c1RGBA[2] = 255 * pi->color1[2];
-	pi->c1RGBA[3] = 255;
-
 	// view angles
 	VectorCopy( viewAngles, pi->viewAngles );
 
@@ -1250,11 +1162,11 @@
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
@@ -1263,8 +1175,8 @@
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

### `ioquake3`  — sha256 `c8b18741d78a...`, 33731 bytes

_Diff stat: +17 / -15 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_players.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_players.c	2026-04-16 20:02:21.557593600 +0100
@@ -380,7 +380,7 @@
 		// get the next frame based on the animation
 		anim = lf->animation;
 		if ( !anim->frameLerp ) {
-			return;			// shouldn't happen
+			return;		// shouldn't happen
 		}
 		if ( dp_realtime < lf->animationTime ) {
 			lf->frameTime = lf->animationTime;		// initial lerp
@@ -795,10 +795,6 @@
 	VectorCopy( origin, legs.lightingOrigin );
 	legs.renderfx = renderfx;
 	VectorCopy (legs.origin, legs.oldorigin);
-	legs.shaderRGBA[0] = 255;
-	legs.shaderRGBA[1] = 255;
-	legs.shaderRGBA[2] = 0;
-	legs.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &legs );
 
@@ -821,10 +817,6 @@
 	UI_PositionRotatedEntityOnTag( &torso, &legs, pi->legsModel, "tag_torso");
 
 	torso.renderfx = renderfx;
-	torso.shaderRGBA[0] = 255;
-	torso.shaderRGBA[1] = 255;
-	torso.shaderRGBA[2] = 150;
-	torso.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &torso );
 
@@ -851,6 +843,12 @@
 	if ( pi->currentWeapon != WP_NONE ) {
 		memset( &gun, 0, sizeof(gun) );
 		gun.hModel = pi->weaponModel;
+		if( pi->currentWeapon == WP_RAILGUN ) {
+			Byte4Copy( pi->c1RGBA, gun.shaderRGBA );
+		}
+		else {
+			Byte4Copy( colorWhite, gun.shaderRGBA );
+		}
 		VectorCopy( origin, gun.lightingOrigin );
 		UI_PositionEntityOnTag( &gun, &torso, pi->torsoModel, "tag_weapon");
 		gun.renderfx = renderfx;
@@ -885,6 +883,12 @@
 		if ( pi->flashModel ) {
 			memset( &flash, 0, sizeof(flash) );
 			flash.hModel = pi->flashModel;
+			if( pi->currentWeapon == WP_RAILGUN ) {
+				Byte4Copy( pi->c1RGBA, flash.shaderRGBA );
+			}
+			else {
+				Byte4Copy( colorWhite, flash.shaderRGBA );
+			}
 			VectorCopy( origin, flash.lightingOrigin );
 			UI_PositionEntityOnTag( &flash, &gun, pi->weaponModel, "tag_flash");
 			flash.renderfx = renderfx;
@@ -961,7 +965,7 @@
 	int			skip;
 	char		text[20000];
 	fileHandle_t	f;
-	animation_t	*animations;
+	animation_t *animations;
 
 	animations = pi->animations;
 
@@ -1153,8 +1157,7 @@
 	}
 
 	// if any skins failed to load, fall back to default
-	//if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
-	if (!UI_RegisterClientSkin(pi, modelName, "color")) {
+	if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
 		if ( !UI_RegisterClientSkin( pi, modelName, "default" ) ) {
 			Com_Printf( "Failed to load skin file: %s : %s\n", modelName, skinName );
 			return qfalse;
@@ -1199,15 +1202,14 @@
 void UI_PlayerInfo_SetInfo( playerInfo_t *pi, int legsAnim, int torsoAnim, vec3_t viewAngles, vec3_t moveAngles, weapon_t weaponNumber, qboolean chat ) {
 	int			currentAnim;
 	weapon_t	weaponNum;
-	int c;
+	int			c;
 
 	pi->chat = chat;
 
 	c = (int)trap_Cvar_VariableValue( "color1" );
-
+ 
 	VectorClear( pi->color1 );
 
-	//FIXME wc ql
 	if( c < 1 || c > 7 ) {
 		VectorSet( pi->color1, 1, 1, 1 );
 	}

```

### `openarena-engine`  — sha256 `b667ca7990d6...`, 32181 bytes

_Diff stat: +50 / -98 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_players.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_players.c	2026-04-16 22:48:25.897193700 +0100
@@ -88,13 +88,15 @@
 	}
 
 	if ( weaponNum == WP_MACHINEGUN || weaponNum == WP_GAUNTLET || weaponNum == WP_BFG ) {
-		COM_StripExtension( item->world_model[0], path, sizeof(path) );
-		Q_strcat( path, sizeof(path), "_barrel.md3" );
+		strcpy( path, item->world_model[0] );
+		COM_StripExtension( path, path, sizeof(path) );
+		strcat( path, "_barrel.md3" );
 		pi->barrelModel = trap_R_RegisterModel( path );
 	}
 
-	COM_StripExtension( item->world_model[0], path, sizeof(path) );
-	Q_strcat( path, sizeof(path), "_flash.md3" );
+	strcpy( path, item->world_model[0] );
+	COM_StripExtension( path, path, sizeof(path) );
+	strcat( path, "_flash.md3" );
 	pi->flashModel = trap_R_RegisterModel( path );
 
 	switch( weaponNum ) {
@@ -303,7 +305,7 @@
 	}
 
 	// cast away const because of compiler problems
-	MatrixMultiply( lerped.axis, ((refEntity_t*)parent)->axis, entity->axis );
+	Q_MatrixMultiply( lerped.axis, ((refEntity_t*)parent)->axis, entity->axis );
 	entity->backlerp = parent->backlerp;
 }
 
@@ -330,8 +332,8 @@
 	}
 
 	// cast away const because of compiler problems
-	MatrixMultiply( entity->axis, lerped.axis, tempAxis );
-	MatrixMultiply( tempAxis, ((refEntity_t *)parent)->axis, entity->axis );
+	Q_MatrixMultiply( entity->axis, ((refEntity_t *)parent)->axis, tempAxis );
+	Q_MatrixMultiply( lerped.axis, tempAxis, entity->axis );
 }
 
 
@@ -363,7 +365,7 @@
 ===============
 */
 static void UI_RunLerpFrame( playerInfo_t *ci, lerpFrame_t *lf, int newAnimation ) {
-	int			f, numFrames;
+	int			f;
 	animation_t	*anim;
 
 	// see if the animation sequence is switching
@@ -379,41 +381,25 @@
 
 		// get the next frame based on the animation
 		anim = lf->animation;
-		if ( !anim->frameLerp ) {
-			return;			// shouldn't happen
-		}
 		if ( dp_realtime < lf->animationTime ) {
 			lf->frameTime = lf->animationTime;		// initial lerp
 		} else {
 			lf->frameTime = lf->oldFrameTime + anim->frameLerp;
 		}
 		f = ( lf->frameTime - lf->animationTime ) / anim->frameLerp;
-
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
@@ -631,16 +617,6 @@
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
@@ -713,12 +689,12 @@
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
@@ -795,10 +771,6 @@
 	VectorCopy( origin, legs.lightingOrigin );
 	legs.renderfx = renderfx;
 	VectorCopy (legs.origin, legs.oldorigin);
-	legs.shaderRGBA[0] = 255;
-	legs.shaderRGBA[1] = 255;
-	legs.shaderRGBA[2] = 0;
-	legs.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &legs );
 
@@ -821,10 +793,6 @@
 	UI_PositionRotatedEntityOnTag( &torso, &legs, pi->legsModel, "tag_torso");
 
 	torso.renderfx = renderfx;
-	torso.shaderRGBA[0] = 255;
-	torso.shaderRGBA[1] = 255;
-	torso.shaderRGBA[2] = 150;
-	torso.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &torso );
 
@@ -851,6 +819,12 @@
 	if ( pi->currentWeapon != WP_NONE ) {
 		memset( &gun, 0, sizeof(gun) );
 		gun.hModel = pi->weaponModel;
+		if( pi->currentWeapon == WP_RAILGUN ) {
+			Byte4Copy( pi->c1RGBA, gun.shaderRGBA );
+		}
+		else {
+			Byte4Copy( colorWhite, gun.shaderRGBA );
+		}
 		VectorCopy( origin, gun.lightingOrigin );
 		UI_PositionEntityOnTag( &gun, &torso, pi->torsoModel, "tag_weapon");
 		gun.renderfx = renderfx;
@@ -871,6 +845,10 @@
 		angles[YAW] = 0;
 		angles[PITCH] = 0;
 		angles[ROLL] = UI_MachinegunSpinAngle( pi );
+		if( pi->realWeapon == WP_GAUNTLET || pi->realWeapon == WP_BFG ) {
+			angles[PITCH] = angles[ROLL];
+			angles[ROLL] = 0;
+		}
 		AnglesToAxis( angles, barrel.axis );
 
 		UI_PositionRotatedEntityOnTag( &barrel, &gun, pi->weaponModel, "tag_barrel");
@@ -885,6 +863,12 @@
 		if ( pi->flashModel ) {
 			memset( &flash, 0, sizeof(flash) );
 			flash.hModel = pi->flashModel;
+			if( pi->currentWeapon == WP_RAILGUN ) {
+				Byte4Copy( pi->c1RGBA, flash.shaderRGBA );
+			}
+			else {
+				Byte4Copy( colorWhite, flash.shaderRGBA );
+			}
 			VectorCopy( origin, flash.lightingOrigin );
 			UI_PositionEntityOnTag( &flash, &gun, pi->weaponModel, "tag_flash");
 			flash.renderfx = renderfx;
@@ -952,7 +936,7 @@
 UI_ParseAnimationFile
 ======================
 */
-static qboolean UI_ParseAnimationFile( const char *filename, playerInfo_t *pi ) {
+static qboolean UI_ParseAnimationFile( const char *filename, animation_t *animations ) {
 	char		*text_p, *prev;
 	int			len;
 	int			i;
@@ -961,15 +945,9 @@
 	int			skip;
 	char		text[20000];
 	fileHandle_t	f;
-	animation_t	*animations;
-
-	animations = pi->animations;
 
 	memset( animations, 0, sizeof( animation_t ) * MAX_ANIMATIONS );
 
-	pi->fixedlegs = qfalse;
-	pi->fixedtorso = qfalse;
-
 	// load the file
 	len = trap_FS_FOpenFile( filename, &f, FS_READ );
 	if ( len <= 0 ) {
@@ -992,35 +970,29 @@
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
@@ -1036,17 +1008,7 @@
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
@@ -1054,32 +1016,24 @@
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
@@ -1153,8 +1107,7 @@
 	}
 
 	// if any skins failed to load, fall back to default
-	//if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
-	if (!UI_RegisterClientSkin(pi, modelName, "color")) {
+	if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
 		if ( !UI_RegisterClientSkin( pi, modelName, "default" ) ) {
 			Com_Printf( "Failed to load skin file: %s : %s\n", modelName, skinName );
 			return qfalse;
@@ -1163,7 +1116,7 @@
 
 	// load the animations
 	Com_sprintf( filename, sizeof( filename ), "models/players/%s/animation.cfg", modelName );
-	if ( !UI_ParseAnimationFile( filename, pi ) ) {
+	if ( !UI_ParseAnimationFile( filename, pi->animations ) ) {
 		Com_Printf( "Failed to load animation file %s\n", filename );
 		return qfalse;
 	}
@@ -1199,15 +1152,14 @@
 void UI_PlayerInfo_SetInfo( playerInfo_t *pi, int legsAnim, int torsoAnim, vec3_t viewAngles, vec3_t moveAngles, weapon_t weaponNumber, qboolean chat ) {
 	int			currentAnim;
 	weapon_t	weaponNum;
-	int c;
+	int			c;
 
 	pi->chat = chat;
 
 	c = (int)trap_Cvar_VariableValue( "color1" );
-
+ 
 	VectorClear( pi->color1 );
 
-	//FIXME wc ql
 	if( c < 1 || c > 7 ) {
 		VectorSet( pi->color1, 1, 1, 1 );
 	}

```

### `openarena-gamecode`  — sha256 `3052ffb49c8b...`, 32895 bytes

_Diff stat: +16 / -58 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_players.c	2026-04-16 20:02:25.209499800 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\q3_ui\ui_players.c	2026-04-16 22:48:24.185499000 +0100
@@ -89,12 +89,12 @@
 
 	if ( weaponNum == WP_MACHINEGUN || weaponNum == WP_GAUNTLET || weaponNum == WP_BFG ) {
 		COM_StripExtension( item->world_model[0], path, sizeof(path) );
-		Q_strcat( path, sizeof(path), "_barrel.md3" );
+		strcat( path, "_barrel.md3" );
 		pi->barrelModel = trap_R_RegisterModel( path );
 	}
 
 	COM_StripExtension( item->world_model[0], path, sizeof(path) );
-	Q_strcat( path, sizeof(path), "_flash.md3" );
+	strcat( path, "_flash.md3" );
 	pi->flashModel = trap_R_RegisterModel( path );
 
 	switch( weaponNum ) {
@@ -380,7 +380,7 @@
 		// get the next frame based on the animation
 		anim = lf->animation;
 		if ( !anim->frameLerp ) {
-			return;			// shouldn't happen
+			return;		// shouldn't happen
 		}
 		if ( dp_realtime < lf->animationTime ) {
 			lf->frameTime = lf->animationTime;		// initial lerp
@@ -388,7 +388,6 @@
 			lf->frameTime = lf->oldFrameTime + anim->frameLerp;
 		}
 		f = ( lf->frameTime - lf->animationTime ) / anim->frameLerp;
-
 		numFrames = anim->numFrames;
 		if (anim->flipflop) {
 			numFrames *= 2;
@@ -518,7 +517,7 @@
 			*swinging = qfalse;
 		}
 		*angle = AngleMod( *angle + move );
-	} else if ( swing < 0 ) {
+	} else {
 		move = uis.frametime * scale * -speed;
 		if ( move <= swing ) {
 			move = swing;
@@ -630,11 +629,9 @@
 	}
 	UI_SwingAngles( dest, 15, 30, 0.1f, &pi->torso.pitchAngle, &pi->torso.pitching );
 	torsoAngles[PITCH] = pi->torso.pitchAngle;
-
 	if ( pi->fixedtorso ) {
 		torsoAngles[PITCH] = 0.0f;
 	}
-
 	if ( pi->fixedlegs ) {
 		legsAngles[YAW] = torsoAngles[YAW];
 		legsAngles[PITCH] = 0.0f;
@@ -713,12 +710,12 @@
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
@@ -795,10 +792,6 @@
 	VectorCopy( origin, legs.lightingOrigin );
 	legs.renderfx = renderfx;
 	VectorCopy (legs.origin, legs.oldorigin);
-	legs.shaderRGBA[0] = 255;
-	legs.shaderRGBA[1] = 255;
-	legs.shaderRGBA[2] = 0;
-	legs.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &legs );
 
@@ -821,10 +814,6 @@
 	UI_PositionRotatedEntityOnTag( &torso, &legs, pi->legsModel, "tag_torso");
 
 	torso.renderfx = renderfx;
-	torso.shaderRGBA[0] = 255;
-	torso.shaderRGBA[1] = 255;
-	torso.shaderRGBA[2] = 150;
-	torso.shaderRGBA[3] = 255;
 
 	trap_R_AddRefEntityToScene( &torso );
 
@@ -961,12 +950,10 @@
 	int			skip;
 	char		text[20000];
 	fileHandle_t	f;
-	animation_t	*animations;
-
+	animation_t *animations;
 	animations = pi->animations;
 
 	memset( animations, 0, sizeof( animation_t ) * MAX_ANIMATIONS );
-
 	pi->fixedlegs = qfalse;
 	pi->fixedtorso = qfalse;
 
@@ -995,13 +982,13 @@
 		if ( !token[0] ) {
 			break;
 		}
-		if ( !Q_stricmp( token, "footsteps" ) ) {
+		if ( Q_strequal( token, "footsteps" ) ) {
 			token = COM_Parse( &text_p );
 			if ( !token[0] ) {
 				break;
 			}
 			continue;
-		} else if ( !Q_stricmp( token, "headoffset" ) ) {
+		} else if ( Q_strequal( token, "headoffset" ) ) {
 			for ( i = 0 ; i < 3 ; i++ ) {
 				token = COM_Parse( &text_p );
 				if ( !token[0] ) {
@@ -1009,7 +996,7 @@
 				}
 			}
 			continue;
-		} else if ( !Q_stricmp( token, "sex" ) ) {
+		} else if ( Q_strequal( token, "sex" ) ) {
 			token = COM_Parse( &text_p );
 			if ( !token[0] ) {
 				break;
@@ -1090,7 +1077,7 @@
 		animations[i].initialLerp = 1000 / fps;
 	}
 
-	if ( i != MAX_ANIMATIONS ) {
+	if ( i != MAX_ANIMATIONS - (TORSO_NEGATIVE - TORSO_GETFLAG + 1) ) {
 		Com_Printf( "Error parsing animation file: %s\n", filename );
 		return qfalse;
 	}
@@ -1153,8 +1140,7 @@
 	}
 
 	// if any skins failed to load, fall back to default
-	//if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
-	if (!UI_RegisterClientSkin(pi, modelName, "color")) {
+	if ( !UI_RegisterClientSkin( pi, modelName, skinName ) ) {
 		if ( !UI_RegisterClientSkin( pi, modelName, "default" ) ) {
 			Com_Printf( "Failed to load skin file: %s : %s\n", modelName, skinName );
 			return qfalse;
@@ -1199,37 +1185,9 @@
 void UI_PlayerInfo_SetInfo( playerInfo_t *pi, int legsAnim, int torsoAnim, vec3_t viewAngles, vec3_t moveAngles, weapon_t weaponNumber, qboolean chat ) {
 	int			currentAnim;
 	weapon_t	weaponNum;
-	int c;
 
 	pi->chat = chat;
 
-	c = (int)trap_Cvar_VariableValue( "color1" );
-
-	VectorClear( pi->color1 );
-
-	//FIXME wc ql
-	if( c < 1 || c > 7 ) {
-		VectorSet( pi->color1, 1, 1, 1 );
-	}
-	else {
-		if( c & 1 ) {
-			pi->color1[2] = 1.0f;
-		}
-
-		if( c & 2 ) {
-			pi->color1[1] = 1.0f;
-		}
-
-		if( c & 4 ) {
-			pi->color1[0] = 1.0f;
-		}
-	}
-
-	pi->c1RGBA[0] = 255 * pi->color1[0];
-	pi->c1RGBA[1] = 255 * pi->color1[1];
-	pi->c1RGBA[2] = 255 * pi->color1[2];
-	pi->c1RGBA[3] = 255;
-
 	// view angles
 	VectorCopy( viewAngles, pi->viewAngles );
 

```
