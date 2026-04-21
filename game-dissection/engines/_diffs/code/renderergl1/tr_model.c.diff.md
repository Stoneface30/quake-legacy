# Diff: `code/renderergl1/tr_model.c`
**Canonical:** `wolfcamql-src` (sha256 `7a01f5a28b9c...`, 30758 bytes)

## Variants

### `ioquake3`  — sha256 `5a1373aafabc...`, 29664 bytes

_Diff stat: +19 / -59 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl1\tr_model.c	2026-04-16 20:02:25.245892500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl1\tr_model.c	2026-04-16 20:02:21.600740300 +0100
@@ -75,7 +75,7 @@
 			loaded = R_LoadMD3(mod, lod, buf.u, name);
 		else
 			ri.Printf(PRINT_WARNING,"R_RegisterMD3: unknown fileid for %s\n", name);
-
+		
 		ri.FS_FreeFile(buf.v);
 
 		if(loaded)
@@ -201,8 +201,6 @@
 
 //===============================================================================
 
-char LoadingModelName[MAX_QPATH];
-
 /*
 ** R_GetModelByHandle
 */
@@ -219,19 +217,6 @@
 	return mod;
 }
 
-void R_GetModelName (qhandle_t index, char *name, int sz) {
-	model_t *mod;
-
-	// out of range gets the defualt model
-	if ( index < 1 || index >= tr.numModels ) {
-		mod = tr.models[0];
-	} else {
-		mod = tr.models[index];
-	}
-
-	Q_strncpyz(name, mod->name, sz);
-}
-
 //===============================================================================
 
 /*
@@ -304,8 +289,6 @@
 		return 0;
 	}
 
-	Q_strncpyz(LoadingModelName, name, sizeof(LoadingModelName));
-
 	// only set the name after the model has been successfully loaded
 	Q_strncpyz( mod->name, name, sizeof( mod->name ) );
 
@@ -371,25 +354,16 @@
 			if( orgNameFailed )
 			{
 				ri.Printf( PRINT_DEVELOPER, "WARNING: %s not present, using %s instead\n",
-						   name, altName );
+						name, altName );
 			}
 
 			break;
 		}
-
-		//FIXME
-		//LoadingModelName[0] = '\0';
 	}
 
-	if (!hModel) {
-		ri.Printf(PRINT_ALL, "^3RE_RegisterModel: failed to load %s\n", name);
-	}
-
-	LoadingModelName[0] = '\0';
 	return hModel;
 }
 
-
 /*
 =================
 R_LoadMD3
@@ -476,17 +450,17 @@
         LL(surf->ofsSt);
         LL(surf->ofsXyzNormals);
         LL(surf->ofsEnd);
-
+		
 		if ( surf->numVerts >= SHADER_MAX_VERTEXES ) {
 			ri.Printf(PRINT_WARNING, "R_LoadMD3: %s has more than %i verts on %s (%i).\n",
-					  mod_name, SHADER_MAX_VERTEXES - 1, surf->name[0] ? surf->name : "a surface",
-					  surf->numVerts );
+				mod_name, SHADER_MAX_VERTEXES - 1, surf->name[0] ? surf->name : "a surface",
+				surf->numVerts );
 			return qfalse;
 		}
 		if ( surf->numTriangles*3 >= SHADER_MAX_INDEXES ) {
 			ri.Printf(PRINT_WARNING, "R_LoadMD3: %s has more than %i triangles on %s (%i).\n",
-					  mod_name, ( SHADER_MAX_INDEXES / 3 ) - 1, surf->name[0] ? surf->name : "a surface",
-					  surf->numTriangles );
+				mod_name, ( SHADER_MAX_INDEXES / 3 ) - 1, surf->name[0] ? surf->name : "a surface",
+				surf->numTriangles );
 			return qfalse;
 		}
 	
@@ -508,18 +482,10 @@
         for ( j = 0 ; j < surf->numShaders ; j++, shader++ ) {
             shader_t	*sh;
 
-			//ri.Printf(PRINT_ALL, "^2model '%s' loading shader '%s'\n", mod_name, shader->name);
-			if (!Q_stricmpn(mod_name, "models/gibsq3/", strlen("models/gibsq3/"))) {
-				Q_strncpyz(shader->name, "models/gibsq3/gibs", MAX_QPATH);
-				//ri.Printf(PRINT_ALL, "yes -> %s\n", shader->name);
-			}
-
             sh = R_FindShader( shader->name, LIGHTMAP_NONE, qtrue );
 			if ( sh->defaultShader ) {
-				//ri.Printf(PRINT_ALL, "couldn't find shader for %s\n", shader->name);
 				shader->shaderIndex = 0;
 			} else {
-				//ri.Printf(PRINT_ALL, "loaded shader for %s\n", shader->name);
 				shader->shaderIndex = sh->index;
 			}
         }
@@ -766,15 +732,15 @@
 			if ( surf->numVerts >= SHADER_MAX_VERTEXES ) 
 			{
 				ri.Printf(PRINT_WARNING, "R_LoadMDR: %s has more than %i verts on %s (%i).\n",
-						  mod_name, SHADER_MAX_VERTEXES - 1, surf->name[0] ? surf->name : "a surface",
-						  surf->numVerts );
+					  mod_name, SHADER_MAX_VERTEXES - 1, surf->name[0] ? surf->name : "a surface",
+					  surf->numVerts );
 				return qfalse;
 			}
 			if ( surf->numTriangles*3 >= SHADER_MAX_INDEXES ) 
 			{
 				ri.Printf(PRINT_WARNING, "R_LoadMDR: %s has more than %i triangles on %s (%i).\n",
-						  mod_name, ( SHADER_MAX_INDEXES / 3 ) - 1, surf->name[0] ? surf->name : "a surface",
-						  surf->numTriangles );
+					  mod_name, ( SHADER_MAX_INDEXES / 3 ) - 1, surf->name[0] ? surf->name : "a surface",
+					  surf->numTriangles );
 				return qfalse;
 			}
 			// lowercase the surface name so skin compares are faster
@@ -902,14 +868,8 @@
 
 
 
-
 //=============================================================================
 
-void RE_GetGlConfig (glconfig_t *glconfigOut)
-{
-	*glconfigOut = glConfig;
-}
-
 /*
 ** RE_BeginRegistration
 */
@@ -1006,7 +966,7 @@
 	return NULL;
 }
 
-md3Tag_t *R_GetAnimTag( mdrHeader_t *mod, int framenum, const char *tagName, md3Tag_t * dest)
+md3Tag_t *R_GetAnimTag( mdrHeader_t *mod, int framenum, const char *tagName, md3Tag_t * dest) 
 {
 	int				i, j, k;
 	int				frameSize;
@@ -1070,9 +1030,9 @@
 			end = R_GetAnimTag((mdrHeader_t *) model->modelData, endFrame, tagName, &end_space);
 		}
 		else if( model->type == MOD_IQM ) {
-				return R_IQMLerpTag( tag, model->modelData,
-									 startFrame, endFrame,
-									 frac, tagName );
+			return R_IQMLerpTag( tag, model->modelData,
+					startFrame, endFrame,
+					frac, tagName );
 		} else {
 			start = end = NULL;
 		}
@@ -1118,7 +1078,7 @@
 	if(model->type == MOD_BRUSH) {
 		VectorCopy( model->bmodel->bounds[0], mins );
 		VectorCopy( model->bmodel->bounds[1], maxs );
-
+		
 		return;
 	} else if (model->type == MOD_MESH) {
 		md3Header_t	*header;
@@ -1129,7 +1089,7 @@
 
 		VectorCopy( frame->bounds[0], mins );
 		VectorCopy( frame->bounds[1], maxs );
-
+		
 		return;
 	} else if (model->type == MOD_MDR) {
 		mdrHeader_t	*header;
@@ -1140,11 +1100,11 @@
 
 		VectorCopy( frame->bounds[0], mins );
 		VectorCopy( frame->bounds[1], maxs );
-
+		
 		return;
 	} else if(model->type == MOD_IQM) {
 		iqmData_t *iqmData;
-
+		
 		iqmData = model->modelData;
 
 		if(iqmData->bounds)

```
