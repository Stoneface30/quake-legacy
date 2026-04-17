# Diff: `code/q3_ui/ui_video.c`
**Canonical:** `wolfcamql-src` (sha256 `d693ffb9f7d8...`, 39543 bytes)

## Variants

### `quake3-source`  — sha256 `2da63ce023b6...`, 33226 bytes

_Diff stat: +46 / -291 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_video.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_video.c	2026-04-16 20:02:19.956607700 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -238,6 +238,13 @@
 #define GRAPHICSOPTIONS_ACCEPT0	"menu/art/accept_0"
 #define GRAPHICSOPTIONS_ACCEPT1	"menu/art/accept_1"
 
+static const char *s_drivers[] =
+{
+	OPENGL_DRIVER_NAME,
+	_3DFX_DRIVER_NAME,
+	0
+};
+
 #define ID_BACK2		101
 #define ID_FULLSCREEN	102
 #define ID_LIST			103
@@ -247,7 +254,6 @@
 #define ID_DISPLAY		107
 #define ID_SOUND		108
 #define ID_NETWORK		109
-#define ID_RATIO		110
 
 typedef struct {
 	menuframework_s	menu;
@@ -262,7 +268,6 @@
 	menutext_s		network;
 
 	menulist_s		list;
-	menulist_s		ratio;
 	menulist_s		mode;
 	menulist_s		driver;
 	menuslider_s	tq;
@@ -270,7 +275,7 @@
 	menulist_s  	lighting;
 	menulist_s  	allow_extensions;
 	menulist_s  	texturebits;
-	menulist_s      colordepth;
+	menulist_s  	colordepth;
 	menulist_s  	geometry;
 	menulist_s  	filter;
 	menutext_s		driverinfo;
@@ -299,9 +304,6 @@
 static InitialVideoOptions_s s_ivo_templates[] =
 {
 	{
-		6, qtrue, 3, 0, 2, 2, 2, 1, 0, qtrue
-	},
-	{
 		4, qtrue, 2, 0, 2, 2, 1, 1, 0, qtrue	// JDC: this was tq 3
 	},
 	{
@@ -318,149 +320,7 @@
 	}
 };
 
-#define NUM_IVO_TEMPLATES ( ARRAY_LEN( s_ivo_templates ) )
-
-static const char *builtinResolutions[ ] =
-{
-	"320x240",
-	"400x300",
-	"512x384",
-	"640x480",
-	"800x600",
-	"960x720",
-	"1024x768",
-	"1152x864",
-	"1280x1024",
-	"1600x1200",
-	"2048x1536",
-	"856x480",
-	NULL
-};
-
-static const char *knownRatios[ ][2] =
-{
-	{ "1.25:1", "5:4"   },
-	{ "1.33:1", "4:3"   },
-	{ "1.50:1", "3:2"   },
-	{ "1.56:1", "14:9"  },
-	{ "1.60:1", "16:10" },
-	{ "1.67:1", "5:3"   },
-	{ "1.78:1", "16:9"  },
-	{ NULL    , NULL    }
-};
-
-#define MAX_RESOLUTIONS	32
-
-static const char* ratios[ MAX_RESOLUTIONS ];
-static char ratioBuf[ MAX_RESOLUTIONS ][ 8 ];
-static int ratioToRes[ MAX_RESOLUTIONS ];
-static int resToRatio[ MAX_RESOLUTIONS ];
-
-static char resbuf[ MAX_STRING_CHARS ];
-static const char* detectedResolutions[ MAX_RESOLUTIONS ];
-static char currentResolution[ 20 ];
-
-static const char** resolutions = builtinResolutions;
-static qboolean resolutionsDetected = qfalse;
-
-/*
-=================
-GraphicsOptions_FindBuiltinResolution
-=================
-*/
-static int GraphicsOptions_FindBuiltinResolution( int mode )
-{
-	int i;
-
-	if( !resolutionsDetected )
-		return mode;
-
-	if( mode < 0 )
-		return -1;
-
-	for( i = 0; builtinResolutions[ i ]; i++ )
-	{
-		if( !Q_stricmp( builtinResolutions[ i ], detectedResolutions[ mode ] ) )
-			return i;
-	}
-
-	return -1;
-}
-
-/*
-=================
-GraphicsOptions_FindDetectedResolution
-=================
-*/
-static int GraphicsOptions_FindDetectedResolution( int mode )
-{
-	int i;
-
-	if( !resolutionsDetected )
-		return mode;
-
-	if( mode < 0 )
-		return -1;
-
-	for( i = 0; detectedResolutions[ i ]; i++ )
-	{
-		if( !Q_stricmp( builtinResolutions[ mode ], detectedResolutions[ i ] ) )
-			return i;
-	}
-
-	return -1;
-}
-
-/*
-=================
-GraphicsOptions_GetAspectRatios
-=================
-*/
-static void GraphicsOptions_GetAspectRatios( void )
-{
-	int i, r;
-
-	// build ratio list from resolutions
-	for( r = 0; resolutions[r]; r++ )
-	{
-		int w, h;
-		char *x;
-		char str[ sizeof(ratioBuf[0]) ];
-
-		// calculate resolution's aspect ratio
-		x = strchr( resolutions[r], 'x' ) + 1;
-		Q_strncpyz( str, resolutions[r], x-resolutions[r] );
-		w = atoi( str );
-		h = atoi( x );
-		Com_sprintf( str, sizeof(str), "%.2f:1", (float)w / (float)h );
-
-		// rename common ratios ("1.33:1" -> "4:3")
-		for( i = 0; knownRatios[i][0]; i++ ) {
-			if( !Q_stricmp( str, knownRatios[i][0] ) ) {
-				Q_strncpyz( str, knownRatios[i][1], sizeof( str ) );
-				break;
-			}
-		}
-
-		// add ratio to list if it is new
-		// establish res/ratio relationship
-		for( i = 0; ratioBuf[i][0]; i++ )
-		{
-			if( !Q_stricmp( str, ratioBuf[i] ) )
-				break;
-		}
-		if( !ratioBuf[i][0] )
-		{
-			Q_strncpyz( ratioBuf[i], str, sizeof(ratioBuf[i]) );
-			ratioToRes[i] = r;
-		}
-
-		ratios[r] = ratioBuf[r];
-		resToRatio[r] = i;
-	}
-
-	ratios[r] = NULL;
-}
+#define NUM_IVO_TEMPLATES ( sizeof( s_ivo_templates ) / sizeof( s_ivo_templates[0] ) )
 
 /*
 =================
@@ -483,50 +343,6 @@
 
 /*
 =================
-GraphicsOptions_GetResolutions
-=================
-*/
-static void GraphicsOptions_GetResolutions( void )
-{
-	trap_Cvar_VariableStringBuffer("r_availableModes", resbuf, sizeof(resbuf));
-	if(*resbuf)
-	{
-		char* s = resbuf;
-		unsigned int i = 0;
-		while( s && i < ARRAY_LEN(detectedResolutions)-1 )
-		{
-			detectedResolutions[i++] = s;
-			s = strchr(s, ' ');
-			if( s )
-				*s++ = '\0';
-		}
-		detectedResolutions[ i ] = NULL;
-
-		// add custom resolution if not in mode list
-		if ( i < ARRAY_LEN(detectedResolutions)-1 )
-		{
-			Com_sprintf( currentResolution, sizeof ( currentResolution ), "%dx%d", uis.glconfig.vidWidth, uis.glconfig.vidHeight );
-
-			for( i = 0; detectedResolutions[ i ]; i++ )
-			{
-				if ( strcmp( detectedResolutions[ i ], currentResolution ) == 0 )
-					break;
-			}
-
-			if ( detectedResolutions[ i ] == NULL )
-			{
-				detectedResolutions[ i++ ] = currentResolution;
-				detectedResolutions[ i ] = NULL;
-			}
-		}
-
-		resolutions = detectedResolutions;
-		resolutionsDetected = qtrue;
-	}
-}
-
-/*
-=================
 GraphicsOptions_CheckConfig
 =================
 */
@@ -534,13 +350,13 @@
 {
 	int i;
 
-	for ( i = 0; i < NUM_IVO_TEMPLATES-1; i++ )
+	for ( i = 0; i < NUM_IVO_TEMPLATES; i++ )
 	{
 		if ( s_ivo_templates[i].colordepth != s_graphicsoptions.colordepth.curvalue )
 			continue;
 		if ( s_ivo_templates[i].driver != s_graphicsoptions.driver.curvalue )
 			continue;
-		if ( GraphicsOptions_FindDetectedResolution(s_ivo_templates[i].mode) != s_graphicsoptions.mode.curvalue )
+		if ( s_ivo_templates[i].mode != s_graphicsoptions.mode.curvalue )
 			continue;
 		if ( s_ivo_templates[i].fullscreen != s_graphicsoptions.fs.curvalue )
 			continue;
@@ -557,9 +373,7 @@
 		s_graphicsoptions.list.curvalue = i;
 		return;
 	}
-
-	// return 'Custom' ivo template
-	s_graphicsoptions.list.curvalue = NUM_IVO_TEMPLATES - 1;
+	s_graphicsoptions.list.curvalue = 4;
 }
 
 /*
@@ -668,39 +482,15 @@
 	}
 	trap_Cvar_SetValue( "r_picmip", 3 - s_graphicsoptions.tq.curvalue );
 	trap_Cvar_SetValue( "r_allowExtensions", s_graphicsoptions.allow_extensions.curvalue );
-
-	if( resolutionsDetected )
-	{
-		// search for builtin mode that matches the detected mode
-		int mode;
-		if ( s_graphicsoptions.mode.curvalue == -1
-			 || s_graphicsoptions.mode.curvalue >= ARRAY_LEN( detectedResolutions ) )
-			s_graphicsoptions.mode.curvalue = 0;
-
-		mode = GraphicsOptions_FindBuiltinResolution( s_graphicsoptions.mode.curvalue );
-		if( mode == -1 )
-		{
-			char w[ 16 ], h[ 16 ];
-			Q_strncpyz( w, detectedResolutions[ s_graphicsoptions.mode.curvalue ], sizeof( w ) );
-			*strchr( w, 'x' ) = 0;
-			Q_strncpyz( h,
-					strchr( detectedResolutions[ s_graphicsoptions.mode.curvalue ], 'x' ) + 1, sizeof( h ) );
-			trap_Cvar_Set( "r_customwidth", w );
-			trap_Cvar_Set( "r_customheight", h );
-		}
-
-		trap_Cvar_SetValue( "r_mode", mode );
-	}
-	else
-		trap_Cvar_SetValue( "r_mode", s_graphicsoptions.mode.curvalue );
-
+	trap_Cvar_SetValue( "r_mode", s_graphicsoptions.mode.curvalue );
 	trap_Cvar_SetValue( "r_fullscreen", s_graphicsoptions.fs.curvalue );
+	trap_Cvar_Set( "r_glDriver", ( char * ) s_drivers[s_graphicsoptions.driver.curvalue] );
 	switch ( s_graphicsoptions.colordepth.curvalue )
 	{
 	case 0:
 		trap_Cvar_SetValue( "r_colorbits", 0 );
 		trap_Cvar_SetValue( "r_depthbits", 0 );
-		trap_Cvar_Reset( "r_stencilbits" );
+		trap_Cvar_SetValue( "r_stencilbits", 0 );
 		break;
 	case 1:
 		trap_Cvar_SetValue( "r_colorbits", 16 );
@@ -710,7 +500,6 @@
 	case 2:
 		trap_Cvar_SetValue( "r_colorbits", 32 );
 		trap_Cvar_SetValue( "r_depthbits", 24 );
-		trap_Cvar_SetValue( "r_stencilbits", 8 );
 		break;
 	}
 	trap_Cvar_SetValue( "r_vertexLight", s_graphicsoptions.lighting.curvalue );
@@ -756,11 +545,6 @@
 	}
 
 	switch( ((menucommon_s*)ptr)->id ) {
-	case ID_RATIO:
-		s_graphicsoptions.mode.curvalue =
-			ratioToRes[ s_graphicsoptions.ratio.curvalue ];
-		// fall through to apply mode constraints
-		
 	case ID_MODE:
 		// clamp 3dfx video modes
 		if ( s_graphicsoptions.driver.curvalue == 1 )
@@ -770,16 +554,12 @@
 			else if ( s_graphicsoptions.mode.curvalue > 6 )
 				s_graphicsoptions.mode.curvalue = 6;
 		}
-		s_graphicsoptions.ratio.curvalue =
-			resToRatio[ s_graphicsoptions.mode.curvalue ];
 		break;
 
 	case ID_LIST:
 		ivo = &s_ivo_templates[s_graphicsoptions.list.curvalue];
 
-		s_graphicsoptions.mode.curvalue        = GraphicsOptions_FindDetectedResolution(ivo->mode);
-		s_graphicsoptions.ratio.curvalue =
-			resToRatio[ s_graphicsoptions.mode.curvalue ];
+		s_graphicsoptions.mode.curvalue        = ivo->mode;
 		s_graphicsoptions.tq.curvalue          = ivo->tq;
 		s_graphicsoptions.lighting.curvalue    = ivo->lighting;
 		s_graphicsoptions.colordepth.curvalue  = ivo->colordepth;
@@ -851,38 +631,11 @@
 */
 static void GraphicsOptions_SetMenuItems( void )
 {
-	s_graphicsoptions.mode.curvalue =
-		GraphicsOptions_FindDetectedResolution( trap_Cvar_VariableValue( "r_mode" ) );
-
+	s_graphicsoptions.mode.curvalue = trap_Cvar_VariableValue( "r_mode" );
 	if ( s_graphicsoptions.mode.curvalue < 0 )
 	{
-		if( resolutionsDetected )
-		{
-			int i;
-			char buf[MAX_STRING_CHARS];
-			trap_Cvar_VariableStringBuffer("r_customwidth", buf, sizeof(buf)-2);
-			buf[strlen(buf)+1] = 0;
-			buf[strlen(buf)] = 'x';
-			trap_Cvar_VariableStringBuffer("r_customheight", buf+strlen(buf), sizeof(buf)-strlen(buf));
-
-			for(i = 0; detectedResolutions[i]; ++i)
-			{
-				if(!Q_stricmp(buf, detectedResolutions[i]))
-				{
-					s_graphicsoptions.mode.curvalue = i;
-					break;
-				}
-			}
-			if ( s_graphicsoptions.mode.curvalue < 0 )
-				s_graphicsoptions.mode.curvalue = 0;
-		}
-		else
-		{
-			s_graphicsoptions.mode.curvalue = 3;
-		}
+		s_graphicsoptions.mode.curvalue = 3;
 	}
-	s_graphicsoptions.ratio.curvalue =
-		resToRatio[ s_graphicsoptions.mode.curvalue ];
 	s_graphicsoptions.fs.curvalue = trap_Cvar_VariableValue("r_fullscreen");
 	s_graphicsoptions.allow_extensions.curvalue = trap_Cvar_VariableValue("r_allowExtensions");
 	s_graphicsoptions.tq.curvalue = 3-trap_Cvar_VariableValue( "r_picmip");
@@ -970,7 +723,7 @@
 	{
 		"Default",
 		"Voodoo",
-		NULL
+		0
 	};
 
 	static const char *tq_names[] =
@@ -978,25 +731,24 @@
 		"Default",
 		"16 bit",
 		"32 bit",
-		NULL
+		0
 	};
 
 	static const char *s_graphics_options_names[] =
 	{
-		"Very High Quality",
 		"High Quality",
 		"Normal",
 		"Fast",
 		"Fastest",
 		"Custom",
-		NULL
+		0
 	};
 
 	static const char *lighting_names[] =
 	{
 		"Lightmap",
 		"Vertex",
-		NULL
+		0
 	};
 
 	static const char *colordepth_names[] =
@@ -1004,27 +756,43 @@
 		"Default",
 		"16 bit",
 		"32 bit",
-		NULL
+		0
 	};
 
+	static const char *resolutions[] = 
+	{
+		"320x240",
+		"400x300",
+		"512x384",
+		"640x480",
+		"800x600",
+		"960x720",
+		"1024x768",
+		"1152x864",
+		"1280x1024",
+		"1600x1200",
+		"2048x1536",
+		"856x480 wide screen",
+		0
+	};
 	static const char *filter_names[] =
 	{
 		"Bilinear",
 		"Trilinear",
-		NULL
+		0
 	};
 	static const char *quality_names[] =
 	{
 		"Low",
 		"Medium",
 		"High",
-		NULL
+		0
 	};
 	static const char *enabled_names[] =
 	{
 		"Off",
 		"On",
-		NULL
+		0
 	};
 
 	int y;
@@ -1032,9 +800,6 @@
 	// zero set all our globals
 	memset( &s_graphicsoptions, 0 ,sizeof(graphicsoptions_t) );
 
-	GraphicsOptions_GetResolutions();
-	GraphicsOptions_GetAspectRatios();
-	
 	GraphicsOptions_Cache();
 
 	s_graphicsoptions.menu.wrapAround = qtrue;
@@ -1104,7 +869,7 @@
 	s_graphicsoptions.network.style				= UI_RIGHT;
 	s_graphicsoptions.network.color				= color_red;
 
-	y = 240 - 7 * (BIGCHAR_HEIGHT + 2);
+	y = 240 - 6 * (BIGCHAR_HEIGHT + 2);
 	s_graphicsoptions.list.generic.type     = MTYPE_SPINCONTROL;
 	s_graphicsoptions.list.generic.name     = "Graphics Settings:";
 	s_graphicsoptions.list.generic.flags    = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
@@ -1133,19 +898,9 @@
 	s_graphicsoptions.allow_extensions.itemnames        = enabled_names;
 	y += BIGCHAR_HEIGHT+2;
 
-	s_graphicsoptions.ratio.generic.type     = MTYPE_SPINCONTROL;
-	s_graphicsoptions.ratio.generic.name     = "Aspect Ratio:";
-	s_graphicsoptions.ratio.generic.flags    = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	s_graphicsoptions.ratio.generic.x        = 400;
-	s_graphicsoptions.ratio.generic.y        = y;
-	s_graphicsoptions.ratio.itemnames        = ratios;
-	s_graphicsoptions.ratio.generic.callback = GraphicsOptions_Event;
-	s_graphicsoptions.ratio.generic.id       = ID_RATIO;
-	y += BIGCHAR_HEIGHT+2;
-
 	// references/modifies "r_mode"
 	s_graphicsoptions.mode.generic.type     = MTYPE_SPINCONTROL;
-	s_graphicsoptions.mode.generic.name     = "Resolution:";
+	s_graphicsoptions.mode.generic.name     = "Video Mode:";
 	s_graphicsoptions.mode.generic.flags    = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
 	s_graphicsoptions.mode.generic.x        = 400;
 	s_graphicsoptions.mode.generic.y        = y;
@@ -1228,6 +983,7 @@
 	s_graphicsoptions.driverinfo.string           = "Driver Info";
 	s_graphicsoptions.driverinfo.style            = UI_CENTER|UI_SMALLFONT;
 	s_graphicsoptions.driverinfo.color            = color_red;
+	y += BIGCHAR_HEIGHT+2;
 
 	s_graphicsoptions.back.generic.type	    = MTYPE_BITMAP;
 	s_graphicsoptions.back.generic.name     = GRAPHICSOPTIONS_BACK0;
@@ -1262,7 +1018,6 @@
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.list );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.driver );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.allow_extensions );
-	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.ratio );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.mode );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.colordepth );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.fs );

```

### `ioquake3`  — sha256 `5c2e36509b7b...`, 39541 bytes

_Diff stat: +4 / -4 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_video.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_video.c	2026-04-16 20:02:21.562593700 +0100
@@ -270,7 +270,7 @@
 	menulist_s  	lighting;
 	menulist_s  	allow_extensions;
 	menulist_s  	texturebits;
-	menulist_s      colordepth;
+	menulist_s  	colordepth;
 	menulist_s  	geometry;
 	menulist_s  	filter;
 	menutext_s		driverinfo;
@@ -455,8 +455,8 @@
 			ratioToRes[i] = r;
 		}
 
-		ratios[r] = ratioBuf[r];
-		resToRatio[r] = i;
+		ratios[r] = ratioBuf[r]; 
+		resToRatio[r] = i; 
 	}
 
 	ratios[r] = NULL;
@@ -674,7 +674,7 @@
 		// search for builtin mode that matches the detected mode
 		int mode;
 		if ( s_graphicsoptions.mode.curvalue == -1
-			 || s_graphicsoptions.mode.curvalue >= ARRAY_LEN( detectedResolutions ) )
+			|| s_graphicsoptions.mode.curvalue >= ARRAY_LEN( detectedResolutions ) )
 			s_graphicsoptions.mode.curvalue = 0;
 
 		mode = GraphicsOptions_FindBuiltinResolution( s_graphicsoptions.mode.curvalue );

```

### `openarena-engine`  — sha256 `43878d45a8a3...`, 36757 bytes

_Diff stat: +19 / -109 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_video.c	2026-04-16 20:02:25.215651600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_video.c	2026-04-16 22:48:25.903298800 +0100
@@ -270,7 +270,6 @@
 	menulist_s  	lighting;
 	menulist_s  	allow_extensions;
 	menulist_s  	texturebits;
-	menulist_s      colordepth;
 	menulist_s  	geometry;
 	menulist_s  	filter;
 	menutext_s		driverinfo;
@@ -285,7 +284,6 @@
 	qboolean fullscreen;
 	int tq;
 	int lighting;
-	int colordepth;
 	int texturebits;
 	int geometry;
 	int filter;
@@ -299,22 +297,22 @@
 static InitialVideoOptions_s s_ivo_templates[] =
 {
 	{
-		6, qtrue, 3, 0, 2, 2, 2, 1, 0, qtrue
+		6, qtrue, 3, 0, 2, 2, 1, 0, qtrue
 	},
 	{
-		4, qtrue, 2, 0, 2, 2, 1, 1, 0, qtrue	// JDC: this was tq 3
+		4, qtrue, 2, 0, 2, 1, 1, 0, qtrue	// JDC: this was tq 3
 	},
 	{
-		3, qtrue, 2, 0, 0, 0, 1, 0, 0, qtrue
+		3, qtrue, 2, 0, 0, 1, 0, 0, qtrue
 	},
 	{
-		2, qtrue, 1, 0, 1, 0, 0, 0, 0, qtrue
+		2, qtrue, 1, 0, 0, 0, 0, 0, qtrue
 	},
 	{
-		2, qtrue, 1, 1, 1, 0, 0, 0, 0, qtrue
+		2, qtrue, 1, 1, 0, 0, 0, 0, qtrue
 	},
 	{
-		3, qtrue, 1, 0, 0, 0, 1, 0, 0, qtrue
+		3, qtrue, 1, 0, 0, 1, 0, 0, qtrue
 	}
 };
 
@@ -358,7 +356,6 @@
 
 static char resbuf[ MAX_STRING_CHARS ];
 static const char* detectedResolutions[ MAX_RESOLUTIONS ];
-static char currentResolution[ 20 ];
 
 static const char** resolutions = builtinResolutions;
 static qboolean resolutionsDetected = qfalse;
@@ -455,8 +452,8 @@
 			ratioToRes[i] = r;
 		}
 
-		ratios[r] = ratioBuf[r];
-		resToRatio[r] = i;
+		ratios[r] = ratioBuf[r]; 
+		resToRatio[r] = i; 
 	}
 
 	ratios[r] = NULL;
@@ -469,7 +466,6 @@
 */
 static void GraphicsOptions_GetInitialVideo( void )
 {
-	s_ivo.colordepth  = s_graphicsoptions.colordepth.curvalue;
 	s_ivo.driver      = s_graphicsoptions.driver.curvalue;
 	s_ivo.mode        = s_graphicsoptions.mode.curvalue;
 	s_ivo.fullscreen  = s_graphicsoptions.fs.curvalue;
@@ -488,7 +484,7 @@
 */
 static void GraphicsOptions_GetResolutions( void )
 {
-	trap_Cvar_VariableStringBuffer("r_availableModes", resbuf, sizeof(resbuf));
+	Q_strncpyz(resbuf, UI_Cvar_VariableString("r_availableModes"), sizeof(resbuf));
 	if(*resbuf)
 	{
 		char* s = resbuf;
@@ -502,26 +498,11 @@
 		}
 		detectedResolutions[ i ] = NULL;
 
-		// add custom resolution if not in mode list
-		if ( i < ARRAY_LEN(detectedResolutions)-1 )
+		if( i > 0 )
 		{
-			Com_sprintf( currentResolution, sizeof ( currentResolution ), "%dx%d", uis.glconfig.vidWidth, uis.glconfig.vidHeight );
-
-			for( i = 0; detectedResolutions[ i ]; i++ )
-			{
-				if ( strcmp( detectedResolutions[ i ], currentResolution ) == 0 )
-					break;
-			}
-
-			if ( detectedResolutions[ i ] == NULL )
-			{
-				detectedResolutions[ i++ ] = currentResolution;
-				detectedResolutions[ i ] = NULL;
-			}
+			resolutions = detectedResolutions;
+			resolutionsDetected = qtrue;
 		}
-
-		resolutions = detectedResolutions;
-		resolutionsDetected = qtrue;
 	}
 }
 
@@ -536,8 +517,6 @@
 
 	for ( i = 0; i < NUM_IVO_TEMPLATES-1; i++ )
 	{
-		if ( s_ivo_templates[i].colordepth != s_graphicsoptions.colordepth.curvalue )
-			continue;
 		if ( s_ivo_templates[i].driver != s_graphicsoptions.driver.curvalue )
 			continue;
 		if ( GraphicsOptions_FindDetectedResolution(s_ivo_templates[i].mode) != s_graphicsoptions.mode.curvalue )
@@ -573,23 +552,12 @@
 	{
 		s_graphicsoptions.fs.curvalue = 1;
 		s_graphicsoptions.fs.generic.flags |= QMF_GRAYED;
-		s_graphicsoptions.colordepth.curvalue = 1;
 	}
 	else
 	{
 		s_graphicsoptions.fs.generic.flags &= ~QMF_GRAYED;
 	}
 
-	if ( s_graphicsoptions.fs.curvalue == 0 || s_graphicsoptions.driver.curvalue == 1 )
-	{
-		s_graphicsoptions.colordepth.curvalue = 0;
-		s_graphicsoptions.colordepth.generic.flags |= QMF_GRAYED;
-	}
-	else
-	{
-		s_graphicsoptions.colordepth.generic.flags &= ~QMF_GRAYED;
-	}
-
 	if ( s_graphicsoptions.allow_extensions.curvalue == 0 )
 	{
 		if ( s_graphicsoptions.texturebits.curvalue == 0 )
@@ -620,10 +588,6 @@
 	{
 		s_graphicsoptions.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
 	}
-	if ( s_ivo.colordepth != s_graphicsoptions.colordepth.curvalue )
-	{
-		s_graphicsoptions.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
-	}
 	if ( s_ivo.driver != s_graphicsoptions.driver.curvalue )
 	{
 		s_graphicsoptions.apply.generic.flags &= ~(QMF_HIDDEN|QMF_INACTIVE);
@@ -674,7 +638,7 @@
 		// search for builtin mode that matches the detected mode
 		int mode;
 		if ( s_graphicsoptions.mode.curvalue == -1
-			 || s_graphicsoptions.mode.curvalue >= ARRAY_LEN( detectedResolutions ) )
+			|| s_graphicsoptions.mode.curvalue >= ARRAY_LEN( detectedResolutions ) )
 			s_graphicsoptions.mode.curvalue = 0;
 
 		mode = GraphicsOptions_FindBuiltinResolution( s_graphicsoptions.mode.curvalue );
@@ -695,24 +659,11 @@
 		trap_Cvar_SetValue( "r_mode", s_graphicsoptions.mode.curvalue );
 
 	trap_Cvar_SetValue( "r_fullscreen", s_graphicsoptions.fs.curvalue );
-	switch ( s_graphicsoptions.colordepth.curvalue )
-	{
-	case 0:
-		trap_Cvar_SetValue( "r_colorbits", 0 );
-		trap_Cvar_SetValue( "r_depthbits", 0 );
-		trap_Cvar_Reset( "r_stencilbits" );
-		break;
-	case 1:
-		trap_Cvar_SetValue( "r_colorbits", 16 );
-		trap_Cvar_SetValue( "r_depthbits", 16 );
-		trap_Cvar_SetValue( "r_stencilbits", 0 );
-		break;
-	case 2:
-		trap_Cvar_SetValue( "r_colorbits", 32 );
-		trap_Cvar_SetValue( "r_depthbits", 24 );
-		trap_Cvar_SetValue( "r_stencilbits", 8 );
-		break;
-	}
+
+	trap_Cvar_Reset("r_colorbits");
+	trap_Cvar_Reset("r_depthbits");
+	trap_Cvar_Reset("r_stencilbits");
+
 	trap_Cvar_SetValue( "r_vertexLight", s_graphicsoptions.lighting.curvalue );
 
 	if ( s_graphicsoptions.geometry.curvalue == 2 )
@@ -782,7 +733,6 @@
 			resToRatio[ s_graphicsoptions.mode.curvalue ];
 		s_graphicsoptions.tq.curvalue          = ivo->tq;
 		s_graphicsoptions.lighting.curvalue    = ivo->lighting;
-		s_graphicsoptions.colordepth.curvalue  = ivo->colordepth;
 		s_graphicsoptions.texturebits.curvalue = ivo->texturebits;
 		s_graphicsoptions.geometry.curvalue    = ivo->geometry;
 		s_graphicsoptions.filter.curvalue      = ivo->filter;
@@ -934,29 +884,6 @@
 	{
 		s_graphicsoptions.geometry.curvalue = 2;
 	}
-
-	switch ( ( int ) trap_Cvar_VariableValue( "r_colorbits" ) )
-	{
-	default:
-	case 0:
-		s_graphicsoptions.colordepth.curvalue = 0;
-		break;
-	case 16:
-		s_graphicsoptions.colordepth.curvalue = 1;
-		break;
-	case 32:
-		s_graphicsoptions.colordepth.curvalue = 2;
-		break;
-	}
-
-	if ( s_graphicsoptions.fs.curvalue == 0 )
-	{
-		s_graphicsoptions.colordepth.curvalue = 0;
-	}
-	if ( s_graphicsoptions.driver.curvalue == 1 )
-	{
-		s_graphicsoptions.colordepth.curvalue = 1;
-	}
 }
 
 /*
@@ -999,14 +926,6 @@
 		NULL
 	};
 
-	static const char *colordepth_names[] =
-	{
-		"Default",
-		"16 bit",
-		"32 bit",
-		NULL
-	};
-
 	static const char *filter_names[] =
 	{
 		"Bilinear",
@@ -1154,15 +1073,6 @@
 	s_graphicsoptions.mode.generic.id       = ID_MODE;
 	y += BIGCHAR_HEIGHT+2;
 
-	// references "r_colorbits"
-	s_graphicsoptions.colordepth.generic.type     = MTYPE_SPINCONTROL;
-	s_graphicsoptions.colordepth.generic.name     = "Color Depth:";
-	s_graphicsoptions.colordepth.generic.flags    = QMF_PULSEIFFOCUS|QMF_SMALLFONT;
-	s_graphicsoptions.colordepth.generic.x        = 400;
-	s_graphicsoptions.colordepth.generic.y        = y;
-	s_graphicsoptions.colordepth.itemnames        = colordepth_names;
-	y += BIGCHAR_HEIGHT+2;
-
 	// references/modifies "r_fullscreen"
 	s_graphicsoptions.fs.generic.type     = MTYPE_SPINCONTROL;
 	s_graphicsoptions.fs.generic.name	  = "Fullscreen:";
@@ -1228,6 +1138,7 @@
 	s_graphicsoptions.driverinfo.string           = "Driver Info";
 	s_graphicsoptions.driverinfo.style            = UI_CENTER|UI_SMALLFONT;
 	s_graphicsoptions.driverinfo.color            = color_red;
+	y += BIGCHAR_HEIGHT+2;
 
 	s_graphicsoptions.back.generic.type	    = MTYPE_BITMAP;
 	s_graphicsoptions.back.generic.name     = GRAPHICSOPTIONS_BACK0;
@@ -1264,7 +1175,6 @@
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.allow_extensions );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.ratio );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.mode );
-	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.colordepth );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.fs );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.lighting );
 	Menu_AddItem( &s_graphicsoptions.menu, ( void * ) &s_graphicsoptions.geometry );

```

### `openarena-gamecode`  — sha256 `83f503af45d1...`, 43030 bytes

_Diff stat: +224 / -196 lines_

_(full diff is 25373 bytes — see files directly)_
