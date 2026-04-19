# Diff: `code/renderergl2/tr_bsp.c`
**Canonical:** `wolfcamql-src` (sha256 `e66027943a69...`, 90228 bytes)

## Variants

### `ioquake3`  — sha256 `33a44ce206ba...`, 84572 bytes

_Diff stat: +27 / -241 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\renderergl2\tr_bsp.c	2026-04-16 20:02:25.256259700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\renderergl2\tr_bsp.c	2026-04-16 20:02:21.608255800 +0100
@@ -103,37 +103,24 @@
 */
 static	void R_ColorShiftLightingBytes( byte in[4], byte out[4] ) {
 	int		shift, r, g, b;
-	float mul;
-	int cap;
-
-	cap = r_mapOverBrightBitsCap->integer;
-	if (cap > 255) {
-		cap = 255;
-	} else if (cap < 0) {
-		cap = 0;
-	}
 
 	// shift the color data based on overbright range
 	shift = r_mapOverBrightBits->integer - tr.overbrightBits;
-	mul = r_mapOverBrightBitsValue->value;
-	if (mul < 0.0) {
-		mul = 0.0;
-	}
 
 	// shift the data based on overbright range
-	r = (in[0] << shift) * mul;
-	g = (in[1] << shift) * mul;
-	b = (in[2] << shift) * mul;
-
+	r = in[0] << shift;
+	g = in[1] << shift;
+	b = in[2] << shift;
+	
 	// normalize by color instead of saturating to white
 	if ( ( r | g | b ) > 255 ) {
 		int		max;
 
 		max = r > g ? r : g;
 		max = max > b ? max : b;
-		r = r * cap / max;
-		g = g * cap / max;
-		b = b * cap / max;
+		r = r * 255 / max;
+		g = g * 255 / max;
+		b = b * 255 / max;
 	}
 
 	out[0] = r;
@@ -398,7 +385,6 @@
 #endif
 					color[3] = 1.0f;
 
-					//FIXME r_darknessThreshold
 					R_ColorShiftLightingFloats(color, color);
 
 					ColorToRGB16(color, (uint16_t *)(&image[j * 8]));
@@ -424,7 +410,6 @@
 					}
 					color[3] = 1.0f;
 
-					//FIXME r_darknessThreshold
 					R_ColorShiftLightingFloats(color, color);
 
 					ColorToRGB16(color, (uint16_t *)(&image[j * 8]));
@@ -459,66 +444,8 @@
 					}
 					else
 					{
-						int threshold;
-						int r, g, b;
-
 						R_ColorShiftLightingBytes( &buf_p[j*3], &image[j*4] );
 						image[j*4+3] = 255;
-
-						if (r_darknessThreshold->integer > 0) {
-							r = image[j*4 + 0];
-							g = image[j*4 + 1];
-							b = image[j*4 + 2];
-
-							threshold = r_darknessThreshold->integer;
-
-							if (r < threshold  ||  g < threshold  ||  b < threshold) {
-								int min, max;
-								float wantScale;
-								float useScale;
-
-								min = r;
-								if (g < min) {
-									min = g;
-								}
-								if (b < min) {
-									min = b;
-								}
-
-								max = r;
-								if (g > max) {
-									max = g;
-								}
-								if (b > max) {
-									max = b;
-								}
-
-								// preserve color
-								wantScale = (float)threshold / (float)min;
-								if (wantScale * (float)max <= 255.0) {
-									useScale = wantScale;
-								} else {
-									useScale = 255.0 / (float)max;
-								}
-
-								r = (int)((float)r * useScale);
-								g = (int)((float)g * useScale);
-								b = (int)((float)b * useScale);
-
-								if (r > 255) {
-									r = 255;
-								}
-								if (g > 255) {
-									g = 255;
-								}
-								if (b > 255) {
-									b = 255;
-								}
-								image[j*4 + 0] = r;
-								image[j*4 + 1] = g;
-								image[j*4 + 2] = b;
-							}
-						}
 					}
 				}
 			}
@@ -566,6 +493,7 @@
 	ri.Free(image);
 }
 
+
 // If FatPackU() or FatPackV() changes, update FixFatLightmapTexCoords()
 static float FatPackU(float input, int lightmapnum)
 {
@@ -696,43 +624,6 @@
 	return shader;
 }
 
-static void MarkAsMapShader (shader_t *shader)
-{
-	static int ignoreCount = -1;
-	int i;
-
-	if (ignoreCount == -1) {
-		ignoreCount = 0;
-
-		while (1) {
-			if (!ri.Cvar_FindVar(va("r_singleShaderIgnore%d", ignoreCount + 1))) {
-				break;
-			}
-
-			ignoreCount++;
-		}
-	}
-
-	//FIXME tr.defaultShader
-
-	// ignore weather shaders and weather shaders replaced with wc/empty (r_weather)
-	if (strcmp(shader->name, "textures/sfx/rain") == 0  ||  strcmp(shader->name, "textures/proto2/snow01") == 0  ||  strcmp(shader->name, "gfx/misc/snow") == 0  ||  strcmp(shader->name, "wc/empty") == 0) {
-		shader->mapShader = qfalse;
-	} else {
-		shader->mapShader = qtrue;
-	}
-
-	for (i = 0;  i < ignoreCount;  i++) {
-		cvar_t *cv;
-
-		cv = ri.Cvar_Get(va("r_singleShaderIgnore%d", i + 1), "", 0);
-
-		if (strcmp(shader->name, cv->string) == 0) {
-			shader->mapShader = qfalse;
-		}
-	}
-}
-
 void LoadDrawVertToSrfVert(srfVert_t *s, drawVert_t *d, int realLightmapNum, float hdrVertColors[3], vec3_t *bounds)
 {
 	vec4_t v;
@@ -813,7 +704,9 @@
 
 	// get shader value
 	surf->shader = ShaderForShaderNum( ds->shaderNum, realLightmapNum );
-	MarkAsMapShader(surf->shader);
+	if ( r_singleShader->integer && !surf->shader->isSky ) {
+		surf->shader = tr.defaultShader;
+	}
 
 	numVerts = LittleLong(ds->numVerts);
 	if (numVerts > MAX_FACE_POINTS) {
@@ -901,10 +794,9 @@
 ParseMesh
 ===============
 */
-static void ParseMesh ( dsurface_t *ds, drawVert_t *verts, float *hdrVertColors, msurface_t *surf, int num ) {
+static void ParseMesh ( dsurface_t *ds, drawVert_t *verts, float *hdrVertColors, msurface_t *surf ) {
 	srfBspSurface_t	*grid = (srfBspSurface_t *)surf->data;
-	int				i, j;
-	int k;
+	int				i;
 	int				width, height, numPoints;
 	srfVert_t points[MAX_PATCH_SIZE*MAX_PATCH_SIZE];
 	vec3_t			bounds[2];
@@ -919,7 +811,9 @@
 
 	// get shader value
 	surf->shader = ShaderForShaderNum( ds->shaderNum, realLightmapNum );
-	MarkAsMapShader(surf->shader);
+	if ( r_singleShader->integer && !surf->shader->isSky ) {
+		surf->shader = tr.defaultShader;
+	}
 
 	// we may have a nodraw surface, because they might still need to
 	// be around for movement clipping
@@ -939,66 +833,6 @@
 	for(i = 0; i < numPoints; i++)
 		LoadDrawVertToSrfVert(&points[i], &verts[i], realLightmapNum, hdrVertColors ? hdrVertColors + (ds->firstVert + i) * 3 : NULL, NULL);
 
-		// ad hack
-#if 0
-	if (num >= (s_worldData.numsurfaces - s_worldData.numAds)) {
-		int index;
-
-		index = (num - s_worldData.numsurfaces) + s_worldData.numAds;
-		ri.Printf(PRINT_ALL, "advert %d '%s' %d\n", index, surf->shader->name, LittleLong(ds->shaderNum));
-
-        Q_strncpyz(s_worldData.ads[index].model, surf->shader->name, sizeof(s_worldData.ads[index].model));
-		s_worldData.ads[index].cellId = RE_RegisterShader(surf->shader->name);  //LittleLong(ds->shaderNum);
-	}
-#endif
-
-	if (!Q_stricmpn(surf->shader->name, "textures/ad_content/", strlen("textures/ad_content/"))  ||  !Q_stricmpn(surf->shader->name, "textures/ad_trim/", strlen("textures/ad_trim/"))) {
-		qboolean found = qfalse;
-
-		//ri.Printf(PRINT_ALL, "advert '%s'\n", surf->shader->name);
-
-		for (i = 0;  i < numPoints;  i++) {
-			//ri.Printf(PRINT_ALL, "%d: %f %f %f\n", i, verts[i].xyz[0], verts[i].xyz[1], verts[i].xyz[2]);
-		}
-
-		for (i = 0;  i < s_worldData.numAds;  i++) {
-			found = qfalse;
-
-			for (j = 0;  j < 3;  j++) {
-				found = qfalse;
-				for (k = 0;  k < numPoints;  k++) {
-					if (*s_worldData.adShaders[i]) {
-						continue;
-					}
-					if (s_worldData.ads[i].rect[j][0] == verts[k].xyz[0]  &&
-						s_worldData.ads[i].rect[j][1] == verts[k].xyz[1]  &&
-						s_worldData.ads[i].rect[j][2] == verts[k].xyz[2]) {
-						found = qtrue;
-						break;
-					}
-				}
-
-				if (!found) {
-					break;
-				}
-			}
-
-			if (found) {
-				//FIXME fuck wait, what about transparent ads :(
-				//ri.Printf(PRINT_ALL, "found ad %d  lightmap:%d\n", i + 1, lightmapNum);
-				//s_worldData.ads[i].cellId = RE_RegisterShader(surf->shader->name);
-				//FIXME always 0 :[
-				s_worldData.adsLightmap[i] = realLightmapNum;  //1;  //lightmapNum;
-				Q_strncpyz(s_worldData.adShaders[i], surf->shader->name, MAX_QPATH);
-				break;
-			}
-		}
-
-		if (!found) {
-			ri.Printf(PRINT_ALL, "couldn't find add for mesh %d\n", num);
-		}
-	}
-
 	// pre-tesseleate
 	R_SubdividePatchToGrid( grid, width, height, points );
 
@@ -1037,7 +871,9 @@
 
 	// get shader
 	surf->shader = ShaderForShaderNum( ds->shaderNum, LIGHTMAP_BY_VERTEX );
-	MarkAsMapShader(surf->shader);
+	if ( r_singleShader->integer && !surf->shader->isSky ) {
+		surf->shader = tr.defaultShader;
+	}
 
 	numVerts = LittleLong(ds->numVerts);
 	numIndexes = LittleLong(ds->numIndexes);
@@ -1118,7 +954,9 @@
 
 	// get shader
 	surf->shader = ShaderForShaderNum( ds->shaderNum, LIGHTMAP_BY_VERTEX );
-	MarkAsMapShader(surf->shader);
+	if ( r_singleShader->integer && !surf->shader->isSky ) {
+		surf->shader = tr.defaultShader;
+	}
 
 	//flare = ri.Hunk_Alloc( sizeof( *flare ), h_low );
 	flare = (void *)surf->data;
@@ -1929,7 +1767,7 @@
 	for ( i = 0 ; i < count ; i++, in++, out++ ) {
 		switch ( LittleLong( in->surfaceType ) ) {
 		case MST_PATCH:
-			ParseMesh ( in, dv, hdrVertColors, out, i );
+			ParseMesh ( in, dv, hdrVertColors, out );
 			numMeshes++;
 			break;
 		case MST_TRIANGLE_SOUP:
@@ -2136,11 +1974,6 @@
 	for ( i=0 ; i<count ; i++ ) {
 		out[i].surfaceFlags = LittleLong( out[i].surfaceFlags );
 		out[i].contentFlags = LittleLong( out[i].contentFlags );
-		//ri.Printf(PRINT_ALL, "^6 %03d '%s'  surf: 0x%x  cont: 0x%x\n", i, out[i].shader, out[i].surfaceFlags, out[i].contentFlags);
-		if (out[i].surfaceFlags & SURF_SKY  &&  *r_forceSky->string) {
-			ri.Printf(PRINT_ALL, "changing sky '%s' to '%s'\n", out[i].shader, r_forceSky->string);
-			Q_strncpyz(out[i].shader, r_forceSky->string, sizeof(out[i].shader));
-		}
 	}
 }
 
@@ -2488,7 +2321,7 @@
 			}
 			*s++ = 0;
 			if (r_vertexLight->integer) {
-				R_RemapShader(value, s, "0", qfalse, qfalse);
+				R_RemapShader(value, s, "0");
 			}
 			continue;
 		}
@@ -2501,7 +2334,7 @@
 				break;
 			}
 			*s++ = 0;
-			R_RemapShader(value, s, "0", qfalse, qfalse);
+			R_RemapShader(value, s, "0");
 			continue;
 		}
 		// check for a different grid size
@@ -2518,9 +2351,6 @@
 	}
 }
 
-// R_LoadAdvertisements()
-#include "../renderercommon/inc_tr_bsp.c"
-
 /*
 =================
 R_GetEntityToken
@@ -2861,7 +2691,6 @@
 	}
 }
 
-qboolean LoadingWorld = qfalse;
 
 /*
 =================
@@ -2878,15 +2707,11 @@
 		void *v;
 	} buffer;
 	byte		*startMarker;
-	int bsp_version;
 
-	ri.Printf(PRINT_ALL, "RE_LoadWorldMap(%s)\n", name);
 	if ( tr.worldMapLoaded ) {
 		ri.Error( ERR_DROP, "ERROR: attempted to redundantly load world map" );
 	}
 
-	LoadingWorld = qtrue;
-
 	// set default map light scale
 	tr.sunShadowScale = 0.5f;
 
@@ -2915,41 +2740,7 @@
 	// load it
     ri.FS_ReadFile( name, &buffer.v );
 	if ( !buffer.b ) {
-		//ri.Error (ERR_DROP, "RE_LoadWorldMap: %s not found", name);
-		//LoadingWorld = qfalse;
-
-		i = 0;
-		while (1) {
-			if (ri.MapNames[i].oldName == NULL) {
-				break;
-			}
-			if (!Q_stricmp(name, ri.MapNames[i].oldName)) {
-				ri.FS_ReadFile(ri.MapNames[i].newName, &buffer.v);
-				if (!buffer.b) {
-					ri.Error (ERR_DROP, "RE_LoadWorldMap: %s not found", name);
-					LoadingWorld = qfalse;
-					break;
-				}
-				break;
-			}
-
-			if (!Q_stricmp(name, ri.MapNames[i].newName)) {
-				ri.FS_ReadFile(ri.MapNames[i].oldName, &buffer.v);
-				if (!buffer.b) {
-					ri.Error (ERR_DROP, "RE_LoadWorldMap: %s not found", name);
-					LoadingWorld = qfalse;
-					break;
-				}
-				break;
-			}
-
-			i++;
-		}
-
-		if (!buffer.b) {
-			ri.Error (ERR_DROP, "RE_LoadWorldMap: %s not found", name);
-			LoadingWorld = qfalse;
-		}
+		ri.Error (ERR_DROP, "RE_LoadWorldMap: %s not found", name);
 	}
 
 	// clear tr.world so if the level fails to load, the next
@@ -2969,11 +2760,10 @@
 	fileBase = (byte *)header;
 
 	i = LittleLong (header->version);
-	if ( i > BSP_VERSION ) {
+	if ( i != BSP_VERSION ) {
 		ri.Error (ERR_DROP, "RE_LoadWorldMap: %s has wrong version number (%i should be %i)", 
 			name, i, BSP_VERSION);
 	}
-	bsp_version = i;
 
 	// swap all the lumps
 	for (i=0 ; i<sizeof(dheader_t)/4 ; i++) {
@@ -2981,10 +2771,6 @@
 	}
 
 	// load into heap
-	if (bsp_version > 46) {
-		R_LoadAdvertisements(&header->lumps[LUMP_ADVERTISEMENTS]);
-	}
-
 	R_LoadEntities( &header->lumps[LUMP_ENTITIES] );
 	R_LoadShaders( &header->lumps[LUMP_SHADERS] );
 	R_LoadLightmaps( &header->lumps[LUMP_LIGHTMAPS], &header->lumps[LUMP_SURFACES] );

```
