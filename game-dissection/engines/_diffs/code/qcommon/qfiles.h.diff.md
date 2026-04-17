# Diff: `code/qcommon/qfiles.h`
**Canonical:** `wolfcamql-src` (sha256 `a40c6db80a17...`, 12603 bytes)

## Variants

### `quake3-source`  — sha256 `53f8e6f1cfa8...`, 11807 bytes

_Diff stat: +71 / -76 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\qfiles.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\qcommon\qfiles.h	2026-04-16 20:02:19.962605000 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -28,7 +28,7 @@
 //
 
 // surface geometry should not exceed these limits
-#define	SHADER_MAX_VERTEXES	10000  // 1000
+#define	SHADER_MAX_VERTEXES	1000
 #define	SHADER_MAX_INDEXES	(6*SHADER_MAX_VERTEXES)
 
 
@@ -43,8 +43,7 @@
 ========================================================================
 */
 
-#define	VM_MAGIC			0x12721444
-#define	VM_MAGIC_VER2	0x12721445
+#define	VM_MAGIC	0x12721444
 typedef struct {
 	int		vmMagic;
 
@@ -57,11 +56,52 @@
 	int		dataLength;
 	int		litLength;			// ( dataLength - litLength ) should be byteswapped on load
 	int		bssLength;			// zero filled memory appended to datalength
-
-	//!!! below here is VM_MAGIC_VER2 !!!
-	int		jtrgLength;			// number of jump table targets
 } vmHeader_t;
 
+
+/*
+========================================================================
+
+PCX files are used for 8 bit images
+
+========================================================================
+*/
+
+typedef struct {
+    char	manufacturer;
+    char	version;
+    char	encoding;
+    char	bits_per_pixel;
+    unsigned short	xmin,ymin,xmax,ymax;
+    unsigned short	hres,vres;
+    unsigned char	palette[48];
+    char	reserved;
+    char	color_planes;
+    unsigned short	bytes_per_line;
+    unsigned short	palette_type;
+    char	filler[58];
+    unsigned char	data;			// unbounded
+} pcx_t;
+
+
+/*
+========================================================================
+
+TGA files are used for 24/32 bit images
+
+========================================================================
+*/
+
+typedef struct _TargaHeader {
+	unsigned char 	id_length, colormap_type, image_type;
+	unsigned short	colormap_index, colormap_length;
+	unsigned char	colormap_size;
+	unsigned short	x_origin, y_origin, width, height;
+	unsigned char	pixel_size, attributes;
+} TargaHeader;
+
+
+
 /*
 ========================================================================
 
@@ -171,55 +211,40 @@
 /*
 ==============================================================================
 
-MDR file format
+MD4 file format
 
 ==============================================================================
 */
 
-/*
- * Here are the definitions for Ravensoft's model format of md4. Raven stores their
- * playermodels in .mdr files, in some games, which are pretty much like the md4
- * format implemented by ID soft. It seems like ID's original md4 stuff is not used at all.
- * MDR is being used in EliteForce, JediKnight2 and Soldiers of Fortune2 (I think).
- * So this comes in handy for anyone who wants to make it possible to load player
- * models from these games.
- * This format has bone tags, which is similar to the thing you have in md3 I suppose.
- * Raven has released their version of md3view under GPL enabling me to add support
- * to this codebase. Thanks to Steven Howes aka Skinner for helping with example
- * source code.
- *
- * - Thilo Schulz (arny@ats.s.bawue.de)
- */
-
-#define MDR_IDENT	(('5'<<24)+('M'<<16)+('D'<<8)+'R')
-#define MDR_VERSION	2
-#define	MDR_MAX_BONES	128
+#define MD4_IDENT			(('4'<<24)+('P'<<16)+('D'<<8)+'I')
+#define MD4_VERSION			1
+#define	MD4_MAX_BONES		128
 
 typedef struct {
-	int			boneIndex;	// these are indexes into the boneReferences,
+	int			boneIndex;		// these are indexes into the boneReferences,
 	float		   boneWeight;		// not the global per-frame bone list
 	vec3_t		offset;
-} mdrWeight_t;
+} md4Weight_t;
 
 typedef struct {
 	vec3_t		normal;
 	vec2_t		texCoords;
 	int			numWeights;
-	mdrWeight_t	weights[1];		// variable sized
-} mdrVertex_t;
+	md4Weight_t	weights[1];		// variable sized
+} md4Vertex_t;
 
 typedef struct {
 	int			indexes[3];
-} mdrTriangle_t;
+} md4Triangle_t;
 
 typedef struct {
 	int			ident;
 
 	char		name[MAX_QPATH];	// polyset name
 	char		shader[MAX_QPATH];
-	int			shaderIndex;	// for in-game use
+	int			shaderIndex;		// for in-game use
 
-	int			ofsHeader;	// this will be a negative number
+	int			ofsHeader;			// this will be a negative number
 
 	int			numVerts;
 	int			ofsVerts;
@@ -235,42 +260,25 @@
 	int			numBoneReferences;
 	int			ofsBoneReferences;
 
-	int			ofsEnd;		// next surface follows
-} mdrSurface_t;
+	int			ofsEnd;				// next surface follows
+} md4Surface_t;
 
 typedef struct {
 	float		matrix[3][4];
-} mdrBone_t;
+} md4Bone_t;
 
 typedef struct {
-	vec3_t		bounds[2];		// bounds of all surfaces of all LOD's for this frame
+	vec3_t		bounds[2];			// bounds of all surfaces of all LOD's for this frame
 	vec3_t		localOrigin;		// midpoint of bounds, used for sphere cull
-	float		radius;			// dist from localOrigin to corner
-	char		name[16];
-	mdrBone_t	bones[1];		// [numBones]
-} mdrFrame_t;
-
-typedef struct {
-        unsigned char Comp[24]; // MC_COMP_BYTES is in MatComp.h, but don't want to couple
-} mdrCompBone_t;
-
-typedef struct {
-        vec3_t          bounds[2];		// bounds of all surfaces of all LOD's for this frame
-        vec3_t          localOrigin;		// midpoint of bounds, used for sphere cull
-        float           radius;			// dist from localOrigin to corner
-        mdrCompBone_t   bones[1];		// [numBones]
-} mdrCompFrame_t;
+	float		radius;				// dist from localOrigin to corner
+	md4Bone_t	bones[1];			// [numBones]
+} md4Frame_t;
 
 typedef struct {
 	int			numSurfaces;
 	int			ofsSurfaces;		// first surface, others follow
 	int			ofsEnd;				// next lod follows
-} mdrLOD_t;
-
-typedef struct {
-        int                     boneIndex;
-        char            name[32];
-} mdrTag_t;
+} md4LOD_t;
 
 typedef struct {
 	int			ident;
@@ -281,17 +289,15 @@
 	// frames and bones are shared by all levels of detail
 	int			numFrames;
 	int			numBones;
-	int			ofsFrames;			// mdrFrame_t[numFrames]
+	int			ofsBoneNames;		// char	name[ MAX_QPATH ]
+	int			ofsFrames;			// md4Frame_t[numFrames]
 
 	// each level of detail has completely separate sets of surfaces
 	int			numLODs;
 	int			ofsLODs;
 
-        int                     numTags;
-        int                     ofsTags;
-
 	int			ofsEnd;				// end of file
-} mdrHeader_t;
+} md4Header_t;
 
 
 /*
@@ -306,7 +312,7 @@
 #define BSP_IDENT	(('P'<<24)+('S'<<16)+('B'<<8)+'I')
 		// little-endian "IBSP"
 
-#define BSP_VERSION			47
+#define BSP_VERSION			46
 
 
 // there shouldn't be any problem with increasing these values at the
@@ -334,7 +340,6 @@
 #define	MAX_MAP_DRAW_VERTS	0x80000
 #define	MAX_MAP_DRAW_INDEXES	0x80000
 
-#define MAX_MAP_ADVERTISEMENTS  30
 
 // key / value pair sizes in the entities lump
 #define	MAX_KEY				32
@@ -375,8 +380,7 @@
 #define	LUMP_LIGHTMAPS		14
 #define	LUMP_LIGHTGRID		15
 #define	LUMP_VISIBILITY		16
-#define LUMP_ADVERTISEMENTS 17
-#define	HEADER_LUMPS		18
+#define	HEADER_LUMPS		17
 
 typedef struct {
 	int			ident;
@@ -450,8 +454,6 @@
 	byte		color[4];
 } drawVert_t;
 
-#define drawVert_t_cleared(x) drawVert_t (x) = {{0, 0, 0}, {0, 0}, {0, 0}, {0, 0, 0}, {0, 0, 0, 0}}
-
 typedef enum {
 	MST_BAD,
 	MST_PLANAR,
@@ -482,12 +484,5 @@
 	int			patchHeight;
 } dsurface_t;
 
-typedef struct {
-	int			cellId;
-	vec3_t		normal;
-	vec3_t		rect[4];
-	char		model[ MAX_QPATH ];
-	//char shader[MAX_QPATH];
-} dadvertisement_t;
 
 #endif

```

### `ioquake3`  — sha256 `b18525f1a332...`, 12377 bytes

_Diff stat: +3 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\qfiles.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\qfiles.h	2026-04-16 20:02:21.571105600 +0100
@@ -28,7 +28,7 @@
 //
 
 // surface geometry should not exceed these limits
-#define	SHADER_MAX_VERTEXES	10000  // 1000
+#define	SHADER_MAX_VERTEXES	1000
 #define	SHADER_MAX_INDEXES	(6*SHADER_MAX_VERTEXES)
 
 
@@ -306,7 +306,7 @@
 #define BSP_IDENT	(('P'<<24)+('S'<<16)+('B'<<8)+'I')
 		// little-endian "IBSP"
 
-#define BSP_VERSION			47
+#define BSP_VERSION			46
 
 
 // there shouldn't be any problem with increasing these values at the
@@ -334,7 +334,6 @@
 #define	MAX_MAP_DRAW_VERTS	0x80000
 #define	MAX_MAP_DRAW_INDEXES	0x80000
 
-#define MAX_MAP_ADVERTISEMENTS  30
 
 // key / value pair sizes in the entities lump
 #define	MAX_KEY				32
@@ -375,8 +374,7 @@
 #define	LUMP_LIGHTMAPS		14
 #define	LUMP_LIGHTGRID		15
 #define	LUMP_VISIBILITY		16
-#define LUMP_ADVERTISEMENTS 17
-#define	HEADER_LUMPS		18
+#define	HEADER_LUMPS		17
 
 typedef struct {
 	int			ident;
@@ -482,12 +480,5 @@
 	int			patchHeight;
 } dsurface_t;
 
-typedef struct {
-	int			cellId;
-	vec3_t		normal;
-	vec3_t		rect[4];
-	char		model[ MAX_QPATH ];
-	//char shader[MAX_QPATH];
-} dadvertisement_t;
 
 #endif

```

### `quake3e`  — sha256 `2fc6798943cd...`, 12422 bytes

_Diff stat: +41 / -49 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\qfiles.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\qcommon\qfiles.h	2026-04-16 20:02:27.307463300 +0100
@@ -28,7 +28,7 @@
 //
 
 // surface geometry should not exceed these limits
-#define	SHADER_MAX_VERTEXES	10000  // 1000
+#define	SHADER_MAX_VERTEXES	1000
 #define	SHADER_MAX_INDEXES	(6*SHADER_MAX_VERTEXES)
 
 
@@ -46,20 +46,20 @@
 #define	VM_MAGIC			0x12721444
 #define	VM_MAGIC_VER2	0x12721445
 typedef struct {
-	int		vmMagic;
+	uint32_t vmMagic;
 
-	int		instructionCount;
+	uint32_t instructionCount;
 
-	int		codeOffset;
-	int		codeLength;
+	uint32_t codeOffset;
+	uint32_t codeLength;
 
-	int		dataOffset;
-	int		dataLength;
-	int		litLength;			// ( dataLength - litLength ) should be byteswapped on load
-	int		bssLength;			// zero filled memory appended to datalength
+	uint32_t dataOffset;
+	uint32_t dataLength;
+	uint32_t litLength;			// ( dataLength - litLength ) should be byteswapped on load
+	uint32_t bssLength;			// zero filled memory appended to datalength
 
 	//!!! below here is VM_MAGIC_VER2 !!!
-	int		jtrgLength;			// number of jump table targets
+	uint32_t jtrgLength;			// number of jump table targets
 } vmHeader_t;
 
 /*
@@ -109,24 +109,24 @@
 ** XyzNormals		sizeof( md3XyzNormal_t ) * numVerts * numFrames
 */
 typedef struct {
-	int		ident;				// 
+	int32_t ident;				//
 
 	char	name[MAX_QPATH];	// polyset name
 
-	int		flags;
-	int		numFrames;			// all surfaces in a model should have the same
+	int32_t flags;
+	int32_t numFrames;			// all surfaces in a model should have the same
 
-	int		numShaders;			// all surfaces in a model should have the same
-	int		numVerts;
+	int32_t numShaders;			// all surfaces in a model should have the same
+	int32_t numVerts;
 
-	int		numTriangles;
-	int		ofsTriangles;
+	int32_t numTriangles;
+	uint32_t ofsTriangles;
 
-	int		ofsShaders;			// offset from start of md3Surface_t
-	int		ofsSt;				// texture coords are common for all frames
-	int		ofsXyzNormals;		// numVerts * numFrames
+	uint32_t ofsShaders;			// offset from start of md3Surface_t
+	uint32_t ofsSt;				// texture coords are common for all frames
+	uint32_t ofsXyzNormals;		// numVerts * numFrames
 
-	int		ofsEnd;				// next surface follows
+	uint32_t ofsEnd;				// next surface follows
 } md3Surface_t;
 
 typedef struct {
@@ -135,7 +135,7 @@
 } md3Shader_t;
 
 typedef struct {
-	int			indexes[3];
+	uint32_t	indexes[3];
 } md3Triangle_t;
 
 typedef struct {
@@ -148,24 +148,24 @@
 } md3XyzNormal_t;
 
 typedef struct {
-	int			ident;
-	int			version;
+	int32_t		ident;
+	int32_t		version;
 
 	char		name[MAX_QPATH];	// model name
 
-	int			flags;
+	uint32_t	flags;
 
-	int			numFrames;
-	int			numTags;			
-	int			numSurfaces;
+	int32_t		numFrames;
+	int32_t		numTags;
+	int32_t		numSurfaces;
 
-	int			numSkins;
+	int32_t		numSkins;
 
-	int			ofsFrames;			// offset for first frame
-	int			ofsTags;			// numFrames * numTags
-	int			ofsSurfaces;		// first surface, others follow
+	uint32_t	ofsFrames;			// offset for first frame
+	uint32_t	ofsTags;			// numFrames * numTags
+	uint32_t	ofsSurfaces;		// first surface, others follow
 
-	int			ofsEnd;				// end of file
+	uint32_t	ofsEnd;				// end of file
 } md3Header_t;
 
 /*
@@ -306,7 +306,7 @@
 #define BSP_IDENT	(('P'<<24)+('S'<<16)+('B'<<8)+'I')
 		// little-endian "IBSP"
 
-#define BSP_VERSION			47
+#define BSP_VERSION			46
 
 
 // there shouldn't be any problem with increasing these values at the
@@ -334,7 +334,6 @@
 #define	MAX_MAP_DRAW_VERTS	0x80000
 #define	MAX_MAP_DRAW_INDEXES	0x80000
 
-#define MAX_MAP_ADVERTISEMENTS  30
 
 // key / value pair sizes in the entities lump
 #define	MAX_KEY				32
@@ -351,11 +350,14 @@
 #define MIN_WORLD_COORD		( -128*1024 )
 #define WORLD_SIZE			( MAX_WORLD_COORD - MIN_WORLD_COORD )
 
+#define VIS_HEADER			8
+
 //=============================================================================
 
 
 typedef struct {
-	int		fileofs, filelen;
+	uint32_t fileofs;
+	uint32_t filelen;
 } lump_t;
 
 #define	LUMP_ENTITIES		0
@@ -375,8 +377,7 @@
 #define	LUMP_LIGHTMAPS		14
 #define	LUMP_LIGHTGRID		15
 #define	LUMP_VISIBILITY		16
-#define LUMP_ADVERTISEMENTS 17
-#define	HEADER_LUMPS		18
+#define	HEADER_LUMPS		17
 
 typedef struct {
 	int			ident;
@@ -397,7 +398,7 @@
 	int			contentFlags;
 } dshader_t;
 
-// planes x^1 is allways the opposite of plane x
+// planes x^1 is always the opposite of plane x
 
 typedef struct {
 	float		normal[3];
@@ -447,11 +448,9 @@
 	float		st[2];
 	float		lightmap[2];
 	vec3_t		normal;
-	byte		color[4];
+	color4ub_t	color;
 } drawVert_t;
 
-#define drawVert_t_cleared(x) drawVert_t (x) = {{0, 0, 0}, {0, 0}, {0, 0}, {0, 0, 0}, {0, 0, 0, 0}}
-
 typedef enum {
 	MST_BAD,
 	MST_PLANAR,
@@ -482,12 +481,5 @@
 	int			patchHeight;
 } dsurface_t;
 
-typedef struct {
-	int			cellId;
-	vec3_t		normal;
-	vec3_t		rect[4];
-	char		model[ MAX_QPATH ];
-	//char shader[MAX_QPATH];
-} dadvertisement_t;
 
 #endif

```

### `openarena-engine`  — sha256 `552dd464d1d5...`, 12965 bytes

_Diff stat: +26 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\qfiles.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\qfiles.h	2026-04-16 22:48:25.913366000 +0100
@@ -27,8 +27,15 @@
 // This file must be identical in the quake and utils directories
 //
 
+//Ignore __attribute__ on non-gcc platforms
+#ifndef __GNUC__
+#ifndef __attribute__
+#define __attribute__(x)
+#endif
+#endif
+
 // surface geometry should not exceed these limits
-#define	SHADER_MAX_VERTEXES	10000  // 1000
+#define	SHADER_MAX_VERTEXES	1000
 #define	SHADER_MAX_INDEXES	(6*SHADER_MAX_VERTEXES)
 
 
@@ -293,6 +300,22 @@
 	int			ofsEnd;				// end of file
 } mdrHeader_t;
 
+#ifdef BROKEN_MDRPHYS
+// leilei - bone deformery
+// 		MDR loading also checks for a text file that can set these properties so the "MDP" code can get to work with them.
+//		and working from the cliententity.
+typedef struct {
+
+		vec3_t ofs[MDR_MAX_BONES];
+		vec3_t wgt[MDR_MAX_BONES];
+		float jiggle[MDR_MAX_BONES];
+	
+} mdrClBoneDeformSet_t;
+
+typedef struct {
+		mdrClBoneDeformSet_t def[4];	// up to 4 can alter bones
+} mdrDeformity_t;
+#endif
 
 /*
 ==============================================================================
@@ -306,7 +329,7 @@
 #define BSP_IDENT	(('P'<<24)+('S'<<16)+('B'<<8)+'I')
 		// little-endian "IBSP"
 
-#define BSP_VERSION			47
+#define BSP_VERSION			46
 
 
 // there shouldn't be any problem with increasing these values at the
@@ -334,7 +357,6 @@
 #define	MAX_MAP_DRAW_VERTS	0x80000
 #define	MAX_MAP_DRAW_INDEXES	0x80000
 
-#define MAX_MAP_ADVERTISEMENTS  30
 
 // key / value pair sizes in the entities lump
 #define	MAX_KEY				32
@@ -375,8 +397,7 @@
 #define	LUMP_LIGHTMAPS		14
 #define	LUMP_LIGHTGRID		15
 #define	LUMP_VISIBILITY		16
-#define LUMP_ADVERTISEMENTS 17
-#define	HEADER_LUMPS		18
+#define	HEADER_LUMPS		17
 
 typedef struct {
 	int			ident;
@@ -482,12 +503,5 @@
 	int			patchHeight;
 } dsurface_t;
 
-typedef struct {
-	int			cellId;
-	vec3_t		normal;
-	vec3_t		rect[4];
-	char		model[ MAX_QPATH ];
-	//char shader[MAX_QPATH];
-} dadvertisement_t;
 
 #endif

```

### `openarena-gamecode`  — sha256 `be96186e8c6d...`, 14770 bytes

_Diff stat: +101 / -13 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\qfiles.h	2026-04-16 20:02:25.227263300 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\qcommon\qfiles.h	2026-04-16 22:48:24.195007000 +0100
@@ -27,8 +27,15 @@
 // This file must be identical in the quake and utils directories
 //
 
+//Ignore __attribute__ on non-gcc platforms
+#ifndef __GNUC__
+#ifndef __attribute__
+#define __attribute__(x)
+#endif
+#endif
+
 // surface geometry should not exceed these limits
-#define	SHADER_MAX_VERTEXES	10000  // 1000
+#define	SHADER_MAX_VERTEXES	1000
 #define	SHADER_MAX_INDEXES	(6*SHADER_MAX_VERTEXES)
 
 
@@ -171,11 +178,94 @@
 /*
 ==============================================================================
 
-MDR file format
+MD4 file format
 
 ==============================================================================
 */
 
+#define MD4_IDENT			(('4'<<24)+('P'<<16)+('D'<<8)+'I')
+#define MD4_VERSION			1
+#define	MD4_MAX_BONES		128
+
+typedef struct {
+	int			boneIndex;		// these are indexes into the boneReferences,
+	float		   boneWeight;		// not the global per-frame bone list
+	vec3_t		offset;
+} md4Weight_t;
+
+typedef struct {
+	vec3_t		normal;
+	vec2_t		texCoords;
+	int			numWeights;
+	md4Weight_t	weights[1];		// variable sized
+} md4Vertex_t;
+
+typedef struct {
+	int			indexes[3];
+} md4Triangle_t;
+
+typedef struct {
+	int			ident;
+
+	char		name[MAX_QPATH];	// polyset name
+	char		shader[MAX_QPATH];
+	int			shaderIndex;		// for in-game use
+
+	int			ofsHeader;			// this will be a negative number
+
+	int			numVerts;
+	int			ofsVerts;
+
+	int			numTriangles;
+	int			ofsTriangles;
+
+	// Bone references are a set of ints representing all the bones
+	// present in any vertex weights for this surface.  This is
+	// needed because a model may have surfaces that need to be
+	// drawn at different sort times, and we don't want to have
+	// to re-interpolate all the bones for each surface.
+	int			numBoneReferences;
+	int			ofsBoneReferences;
+
+	int			ofsEnd;				// next surface follows
+} md4Surface_t;
+
+typedef struct {
+	float		matrix[3][4];
+} md4Bone_t;
+
+typedef struct {
+	vec3_t		bounds[2];			// bounds of all surfaces of all LOD's for this frame
+	vec3_t		localOrigin;		// midpoint of bounds, used for sphere cull
+	float		radius;				// dist from localOrigin to corner
+	md4Bone_t	bones[1];			// [numBones]
+} md4Frame_t;
+
+typedef struct {
+	int			numSurfaces;
+	int			ofsSurfaces;		// first surface, others follow
+	int			ofsEnd;				// next lod follows
+} md4LOD_t;
+
+typedef struct {
+	int			ident;
+	int			version;
+
+	char		name[MAX_QPATH];	// model name
+
+	// frames and bones are shared by all levels of detail
+	int			numFrames;
+	int			numBones;
+	int			ofsBoneNames;		// char	name[ MAX_QPATH ]
+	int			ofsFrames;			// md4Frame_t[numFrames]
+
+	// each level of detail has completely separate sets of surfaces
+	int			numLODs;
+	int			ofsLODs;
+
+	int			ofsEnd;				// end of file
+} md4Header_t;
+
 /*
  * Here are the definitions for Ravensoft's model format of md4. Raven stores their
  * playermodels in .mdr files, in some games, which are pretty much like the md4
@@ -191,6 +281,12 @@
  * - Thilo Schulz (arny@ats.s.bawue.de)
  */
 
+// If you want to enable support for Raven's .mdr / md4 format, uncomment the next
+// line.
+//#define RAVENMD4
+
+#ifdef RAVENMD4
+
 #define MDR_IDENT	(('5'<<24)+('M'<<16)+('D'<<8)+'R')
 #define MDR_VERSION	2
 #define	MDR_MAX_BONES	128
@@ -293,6 +389,7 @@
 	int			ofsEnd;				// end of file
 } mdrHeader_t;
 
+#endif
 
 /*
 ==============================================================================
@@ -306,7 +403,7 @@
 #define BSP_IDENT	(('P'<<24)+('S'<<16)+('B'<<8)+'I')
 		// little-endian "IBSP"
 
-#define BSP_VERSION			47
+#define BSP_VERSION			46
 
 
 // there shouldn't be any problem with increasing these values at the
@@ -334,7 +431,6 @@
 #define	MAX_MAP_DRAW_VERTS	0x80000
 #define	MAX_MAP_DRAW_INDEXES	0x80000
 
-#define MAX_MAP_ADVERTISEMENTS  30
 
 // key / value pair sizes in the entities lump
 #define	MAX_KEY				32
@@ -375,8 +471,7 @@
 #define	LUMP_LIGHTMAPS		14
 #define	LUMP_LIGHTGRID		15
 #define	LUMP_VISIBILITY		16
-#define LUMP_ADVERTISEMENTS 17
-#define	HEADER_LUMPS		18
+#define	HEADER_LUMPS		17
 
 typedef struct {
 	int			ident;
@@ -482,12 +577,5 @@
 	int			patchHeight;
 } dsurface_t;
 
-typedef struct {
-	int			cellId;
-	vec3_t		normal;
-	vec3_t		rect[4];
-	char		model[ MAX_QPATH ];
-	//char shader[MAX_QPATH];
-} dadvertisement_t;
 
 #endif

```
