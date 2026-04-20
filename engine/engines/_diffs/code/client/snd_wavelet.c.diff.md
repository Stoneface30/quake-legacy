# Diff: `code/client/snd_wavelet.c`
**Canonical:** `wolfcamql-src` (sha256 `bd6df8a4f33e...`, 6305 bytes)

## Variants

### `quake3-source`  — sha256 `49b78f6c6940...`, 6183 bytes

_Diff stat: +23 / -23 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_wavelet.c	2026-04-16 20:02:25.180303500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\snd_wavelet.c	2026-04-16 20:02:19.895607000 +0100
@@ -15,22 +15,24 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 
 #include "snd_local.h"
 
+long myftol( float f );
+
 #define C0 0.4829629131445341
 #define C1 0.8365163037378079
 #define C2 0.2241438680420134
 #define C3 -0.1294095225512604
 
-static void daub4(float b[], unsigned long n, int isign)
+void daub4(float b[], unsigned long n, int isign)
 {
-	float wksp[4097] = { 0.0f };
-#define a(x) b[(x)-1]					// numerical recipies so a[1] = b[0]
+	float wksp[4097];
+	float	*a=b-1;						// numerical recipies so a[1] = b[0]
 
 	unsigned long nh,nh1,i,j;
 
@@ -39,25 +41,25 @@
 	nh1=(nh=n >> 1)+1;
 	if (isign >= 0) {
 		for (i=1,j=1;j<=n-3;j+=2,i++) {
-			wksp[i]	   = C0*a(j)+C1*a(j+1)+C2*a(j+2)+C3*a(j+3);
-			wksp[i+nh] = C3*a(j)-C2*a(j+1)+C1*a(j+2)-C0*a(j+3);
+			wksp[i]	   = C0*a[j]+C1*a[j+1]+C2*a[j+2]+C3*a[j+3];
+			wksp[i+nh] = C3*a[j]-C2*a[j+1]+C1*a[j+2]-C0*a[j+3];
 		}
-		wksp[i   ] = C0*a(n-1)+C1*a(n)+C2*a(1)+C3*a(2);
-		wksp[i+nh] = C3*a(n-1)-C2*a(n)+C1*a(1)-C0*a(2);
+		wksp[i   ] = C0*a[n-1]+C1*a[n]+C2*a[1]+C3*a[2];
+		wksp[i+nh] = C3*a[n-1]-C2*a[n]+C1*a[1]-C0*a[2];
 	} else {
-		wksp[1] = C2*a(nh)+C1*a(n)+C0*a(1)+C3*a(nh1);
-		wksp[2] = C3*a(nh)-C0*a(n)+C1*a(1)-C2*a(nh1);
+		wksp[1] = C2*a[nh]+C1*a[n]+C0*a[1]+C3*a[nh1];
+		wksp[2] = C3*a[nh]-C0*a[n]+C1*a[1]-C2*a[nh1];
 		for (i=1,j=3;i<nh;i++) {
-			wksp[j++] = C2*a(i)+C1*a(i+nh)+C0*a(i+1)+C3*a(i+nh1);
-			wksp[j++] = C3*a(i)-C0*a(i+nh)+C1*a(i+1)-C2*a(i+nh1);
+			wksp[j++] = C2*a[i]+C1*a[i+nh]+C0*a[i+1]+C3*a[i+nh1];
+			wksp[j++] = C3*a[i]-C0*a[i+nh]+C1*a[i+1]-C2*a[i+nh1];
 		}
 	}
 	for (i=1;i<=n;i++) {
-		a(i)=wksp[i];
+		a[i]=wksp[i];
 	}
 }
 
-static void wt1(float a[], unsigned long n, int isign)
+void wt1(float a[], unsigned long n, int isign)
 {
 	unsigned long nn;
 	int inverseStartLength = n/4;
@@ -81,7 +83,7 @@
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
 };
 
-static byte MuLawEncode(short s) {
+byte MuLawEncode(short s) {
 	unsigned long adjusted;
 	byte sign, exponent, mantissa;
 
@@ -96,7 +98,7 @@
 	return ~(sign | (exponent<<4) | mantissa);
 }
 
-static short MuLawDecode(byte uLaw) {
+short MuLawDecode(byte uLaw) {
 	signed long adjusted;
 	byte exponent, mantissa;
 
@@ -111,17 +113,15 @@
 short mulawToShort[256];
 static qboolean madeTable = qfalse;
 
-#if 0  // unused
 static	int	NXStreamCount;
 
-static void NXPutc(NXStream *stream, char out) {
+void NXPutc(NXStream *stream, char out) {
 	stream[NXStreamCount++] = out;
 }
-#endif
 
 
 void encodeWavelet( sfx_t *sfx, short *packets) {
-	float	wksp[4097] = {0}, temp;
+	float	wksp[4097], temp;
 	int		i, samples, size;
 	sndBuffer		*newchunk, *chunk;
 	byte			*out;
@@ -148,7 +148,7 @@
 		newchunk = SND_malloc();
 		if (sfx->soundData == NULL) {
 			sfx->soundData = newchunk;
-		} else if (chunk != NULL) {
+		} else {
 			chunk->next = newchunk;
 		}
 		chunk = newchunk;
@@ -171,7 +171,7 @@
 }
 
 void decodeWavelet(sndBuffer *chunk, short *to) {
-	float			wksp[4097] = {0};
+	float			wksp[4097];
 	int				i;
 	byte			*out;
 
@@ -217,7 +217,7 @@
 		newchunk = SND_malloc();
 		if (sfx->soundData == NULL) {
 			sfx->soundData = newchunk;
-		} else if (chunk != NULL) {
+		} else {
 			chunk->next = newchunk;
 		}
 		chunk = newchunk;

```

### `ioquake3`  — sha256 `9f8fb5d5a886...`, 6254 bytes

_Diff stat: +6 / -7 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_wavelet.c	2026-04-16 20:02:25.180303500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\snd_wavelet.c	2026-04-16 20:02:21.534568900 +0100
@@ -27,7 +27,7 @@
 #define C2 0.2241438680420134
 #define C3 -0.1294095225512604
 
-static void daub4(float b[], unsigned long n, int isign)
+void daub4(float b[], unsigned long n, int isign)
 {
 	float wksp[4097] = { 0.0f };
 #define a(x) b[(x)-1]					// numerical recipies so a[1] = b[0]
@@ -55,9 +55,10 @@
 	for (i=1;i<=n;i++) {
 		a(i)=wksp[i];
 	}
+#undef a
 }
 
-static void wt1(float a[], unsigned long n, int isign)
+void wt1(float a[], unsigned long n, int isign)
 {
 	unsigned long nn;
 	int inverseStartLength = n/4;
@@ -81,7 +82,7 @@
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
 };
 
-static byte MuLawEncode(short s) {
+byte MuLawEncode(short s) {
 	unsigned long adjusted;
 	byte sign, exponent, mantissa;
 
@@ -96,7 +97,7 @@
 	return ~(sign | (exponent<<4) | mantissa);
 }
 
-static short MuLawDecode(byte uLaw) {
+short MuLawDecode(byte uLaw) {
 	signed long adjusted;
 	byte exponent, mantissa;
 
@@ -111,13 +112,11 @@
 short mulawToShort[256];
 static qboolean madeTable = qfalse;
 
-#if 0  // unused
 static	int	NXStreamCount;
 
-static void NXPutc(NXStream *stream, char out) {
+void NXPutc(NXStream *stream, char out) {
 	stream[NXStreamCount++] = out;
 }
-#endif
 
 
 void encodeWavelet( sfx_t *sfx, short *packets) {

```

### `quake3e`  — sha256 `3fef4b3fe6ee...`, 6253 bytes

_Diff stat: +7 / -8 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_wavelet.c	2026-04-16 20:02:25.180303500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\snd_wavelet.c	2026-04-16 20:02:26.917521900 +0100
@@ -27,10 +27,10 @@
 #define C2 0.2241438680420134
 #define C3 -0.1294095225512604
 
-static void daub4(float b[], unsigned long n, int isign)
+void daub4(float b[], unsigned long n, int isign)
 {
 	float wksp[4097] = { 0.0f };
-#define a(x) b[(x)-1]					// numerical recipies so a[1] = b[0]
+#define a(x) b[(x)-1]					// numerical recipes so a[1] = b[0]
 
 	unsigned long nh,nh1,i,j;
 
@@ -55,9 +55,10 @@
 	for (i=1;i<=n;i++) {
 		a(i)=wksp[i];
 	}
+#undef a
 }
 
-static void wt1(float a[], unsigned long n, int isign)
+void wt1(float a[], unsigned long n, int isign)
 {
 	unsigned long nn;
 	int inverseStartLength = n/4;
@@ -81,7 +82,7 @@
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
 };
 
-static byte MuLawEncode(short s) {
+byte MuLawEncode(short s) {
 	unsigned long adjusted;
 	byte sign, exponent, mantissa;
 
@@ -96,7 +97,7 @@
 	return ~(sign | (exponent<<4) | mantissa);
 }
 
-static short MuLawDecode(byte uLaw) {
+short MuLawDecode(byte uLaw) {
 	signed long adjusted;
 	byte exponent, mantissa;
 
@@ -111,13 +112,11 @@
 short mulawToShort[256];
 static qboolean madeTable = qfalse;
 
-#if 0  // unused
 static	int	NXStreamCount;
 
-static void NXPutc(NXStream *stream, char out) {
+void NXPutc(NXStream *stream, char out) {
 	stream[NXStreamCount++] = out;
 }
-#endif
 
 
 void encodeWavelet( sfx_t *sfx, short *packets) {

```

### `openarena-engine`  — sha256 `50a112277374...`, 6222 bytes

_Diff stat: +15 / -17 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\snd_wavelet.c	2026-04-16 20:02:25.180303500 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\snd_wavelet.c	2026-04-16 22:48:25.738377800 +0100
@@ -30,7 +30,7 @@
 static void daub4(float b[], unsigned long n, int isign)
 {
 	float wksp[4097] = { 0.0f };
-#define a(x) b[(x)-1]					// numerical recipies so a[1] = b[0]
+	float *a=b;
 
 	unsigned long nh,nh1,i,j;
 
@@ -39,21 +39,21 @@
 	nh1=(nh=n >> 1)+1;
 	if (isign >= 0) {
 		for (i=1,j=1;j<=n-3;j+=2,i++) {
-			wksp[i]	   = C0*a(j)+C1*a(j+1)+C2*a(j+2)+C3*a(j+3);
-			wksp[i+nh] = C3*a(j)-C2*a(j+1)+C1*a(j+2)-C0*a(j+3);
+			wksp[i]	   = C0*a[j-1]+C1*a[j]+C2*a[j+1]+C3*a[j+2];
+			wksp[i+nh] = C3*a[j-1]-C2*a[j]+C1*a[j+1]-C0*a[j+2];
 		}
-		wksp[i   ] = C0*a(n-1)+C1*a(n)+C2*a(1)+C3*a(2);
-		wksp[i+nh] = C3*a(n-1)-C2*a(n)+C1*a(1)-C0*a(2);
+		wksp[i   ] = C0*a[n-2]+C1*a[n-1]+C2*a[0]+C3*a[1];
+		wksp[i+nh] = C3*a[n-2]-C2*a[n-1]+C1*a[0]-C0*a[1];
 	} else {
-		wksp[1] = C2*a(nh)+C1*a(n)+C0*a(1)+C3*a(nh1);
-		wksp[2] = C3*a(nh)-C0*a(n)+C1*a(1)-C2*a(nh1);
+		wksp[1] = C2*a[nh-1]+C1*a[n-1]+C0*a[0]+C3*a[nh1-1];
+		wksp[2] = C3*a[nh-1]-C0*a[n-1]+C1*a[0]-C2*a[nh1-1];
 		for (i=1,j=3;i<nh;i++) {
-			wksp[j++] = C2*a(i)+C1*a(i+nh)+C0*a(i+1)+C3*a(i+nh1);
-			wksp[j++] = C3*a(i)-C0*a(i+nh)+C1*a(i+1)-C2*a(i+nh1);
+			wksp[j++] = C2*a[i-1]+C1*a[i+nh-1]+C0*a[i]+C3*a[i+nh1-1];
+			wksp[j++] = C3*a[i-1]-C0*a[i+nh-1]+C1*a[i]-C2*a[i+nh1-1];
 		}
 	}
 	for (i=1;i<=n;i++) {
-		a(i)=wksp[i];
+		a[i-1]=wksp[i];
 	}
 }
 
@@ -81,7 +81,7 @@
    8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,
 };
 
-static byte MuLawEncode(short s) {
+byte MuLawEncode(short s) {
 	unsigned long adjusted;
 	byte sign, exponent, mantissa;
 
@@ -96,7 +96,7 @@
 	return ~(sign | (exponent<<4) | mantissa);
 }
 
-static short MuLawDecode(byte uLaw) {
+short MuLawDecode(byte uLaw) {
 	signed long adjusted;
 	byte exponent, mantissa;
 
@@ -111,17 +111,15 @@
 short mulawToShort[256];
 static qboolean madeTable = qfalse;
 
-#if 0  // unused
 static	int	NXStreamCount;
 
-static void NXPutc(NXStream *stream, char out) {
+void NXPutc(NXStream *stream, char out) {
 	stream[NXStreamCount++] = out;
 }
-#endif
 
 
 void encodeWavelet( sfx_t *sfx, short *packets) {
-	float	wksp[4097] = {0}, temp;
+	float	wksp[4097], temp;
 	int		i, samples, size;
 	sndBuffer		*newchunk, *chunk;
 	byte			*out;
@@ -171,7 +169,7 @@
 }
 
 void decodeWavelet(sndBuffer *chunk, short *to) {
-	float			wksp[4097] = {0};
+	float			wksp[4097];
 	int				i;
 	byte			*out;
 

```
