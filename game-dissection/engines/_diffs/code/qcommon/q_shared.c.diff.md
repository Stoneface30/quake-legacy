# Diff: `code/qcommon/q_shared.c`
**Canonical:** `wolfcamql-src` (sha256 `c0783a0adf5f...`, 33968 bytes)

## Variants

### `ioquake3`  — sha256 `1566c39b1de1...`, 26584 bytes

_Diff stat: +47 / -377 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\q_shared.c	2026-04-16 20:02:25.226257200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\q_shared.c	2026-04-16 20:02:21.570109000 +0100
@@ -23,9 +23,6 @@
 // q_shared.c -- stateless support routines that are included in each code dll
 #include "q_shared.h"
 
-const char *MonthAbbrev[12] = { "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" };
-const char *DayAbbrev[7] = { "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" };
-
 // ^[0-9a-zA-Z]
 qboolean Q_IsColorString(const char *p) {
 	if (!p)
@@ -48,28 +45,6 @@
 	return qtrue;
 }
 
-// ^[0-9a-zA-Z]
-qboolean Q_IsColorStringPicString(const floatint_t *p) {
-	if (!p)
-		return qfalse;
-
-	if (p[0].i != Q_COLOR_ESCAPE)
-		return qfalse;
-
-	if (p[1].i == 0)
-		return qfalse;
-
-	// isalnum expects a signed integer in the range -1 (EOF) to 255, or it might assert on undefined behaviour
-	// a dereferenced char pointer has the range -128 to 127, so we just need to rangecheck the negative part
-	if (p[1].i < 0)
-		return qfalse;
-
-	if (isalnum(p[1].i) == 0)
-		return qfalse;
-
-	return qtrue;
-}
-
 float Com_Clamp( float min, float max, float value ) {
 	if ( value < min ) {
 		return min;
@@ -89,7 +64,7 @@
 char *COM_SkipPath (char *pathname)
 {
 	char	*last;
-
+	
 	last = pathname;
 	while (*pathname)
 	{
@@ -120,39 +95,17 @@
 COM_StripExtension
 ============
 */
-// allow overlapping array ranges
 void COM_StripExtension( const char *in, char *out, int destsize )
 {
-	const char *dot;
-	const char *slash;
-	int n;
-	int i;
-
-	dot = strrchr(in, '.');
-	slash = strrchr(in, '/');
+	const char *dot = strrchr(in, '.'), *slash;
 
-	if (dot  &&  (!slash  ||  slash < dot)) {
-		if (destsize < (dot - in + 1)) {
-			n = destsize;
-		} else {
-			n = dot - in + 1;
-		}
-	} else {
-		n = destsize;
-	}
+	if (dot && (!(slash = strrchr(in, '/')) || slash < dot))
+		destsize = (destsize < dot-in+1 ? destsize : dot-in+1);
 
-	for (i = 0;  i < n  &&  in[i] != '\0';  i++) {
-		char c;
-
-		c = in[i];
-		out[i] = c;
-	}
-
-	if (i < n) {
-		out[i] = '\0';
-	}
-
-	out[n - 1] = '\0';
+	if ( in == out && destsize > 1 )
+		out[destsize-1] = '\0';
+	else
+		Q_strncpyz(out, in, destsize);
 }
 
 /*
@@ -165,18 +118,18 @@
 qboolean COM_CompareExtension(const char *in, const char *ext)
 {
 	int inlen, extlen;
-
+	
 	inlen = strlen(in);
 	extlen = strlen(ext);
-
+	
 	if(extlen <= inlen)
-        {
-			in += inlen - extlen;
-
-			if(!Q_stricmp(in, ext))
-				return qtrue;
-        }
-
+	{
+		in += inlen - extlen;
+		
+		if(!Q_stricmp(in, ext))
+			return qtrue;
+	}
+	
 	return qfalse;
 }
 
@@ -359,7 +312,7 @@
 static	char	com_token[MAX_TOKEN_CHARS];
 static	char	com_parsename[MAX_TOKEN_CHARS];
 static	int		com_lines;
-static int 		com_tokenline;
+static	int		com_tokenline;
 
 void COM_BeginParseSession( const char *name )
 {
@@ -516,12 +469,9 @@
 	com_token[0] = 0;
 	com_tokenline = 0;
 
-	//Com_Printf("xxx '%s'\n", *data_p);
-
 	// make sure incoming data is valid
 	if ( !data )
 	{
-		//Com_Printf("COM_ParseExt() data invalid\n");
 		*data_p = NULL;
 		return com_token;
 	}
@@ -639,7 +589,7 @@
 =================
 SkipBracedSection
 
-The next token should be an open brace  or set depth to 1 if already parsed it.
+The next token should be an open brace or set depth to 1 if already parsed it.
 Skips until a matching close brace is found.
 Internal brace depths are properly skipped.
 =================
@@ -673,10 +623,8 @@
 
 	p = *data;
 
-	if ( !*p ) {
-		Com_Printf("^3WARNING SkipRestOfLine *p == null\n");
+	if ( !*p )
 		return;
-	}
 
 	while ( (c = *p++) != 0 ) {
 		if ( c == '\n' ) {
@@ -802,15 +750,6 @@
 	return ( 0 );
 }
 
-qboolean Q_isdigit (char c)
-{
-	if (c < '0'  ||  c > '9') {
-		return qfalse;
-	}
-
-	return qtrue;
-}
-
 qboolean Q_isanumber( const char *s )
 {
 	char *p;
@@ -824,25 +763,6 @@
 	return *p == '\0';
 }
 
-qboolean Q_isAnInteger (const char *s)
-{
-	if (!s  ||  !*s) {
-		return qfalse;
-	}
-
-	while (1) {
-		if (!*s) {
-			break;
-		}
-		if (s[0] < '0'  ||  s[0] > '9') {
-			return qfalse;
-		}
-		s++;
-	}
-
-	return qtrue;
-}
-
 qboolean Q_isintegral( float f )
 {
 	return (int)f == f;
@@ -862,7 +782,7 @@
 int Q_vsnprintf(char *str, size_t size, const char *format, va_list ap)
 {
 	int retval;
-
+	
 	retval = _vsnprintf(str, size, format, ap);
 
 	if(retval < 0 || retval == size)
@@ -873,11 +793,11 @@
 		//
 		// Obviously we cannot determine that value from Microsoft's
 		// implementation, so we have no choice but to return size.
-
+		
 		str[size - 1] = '\0';
 		return size;
 	}
-
+	
 	return retval;
 }
 #endif
@@ -885,71 +805,25 @@
 /*
 =============
 Q_strncpyz
-
+ 
 Safe strncpy that ensures a trailing zero
 =============
 */
 void Q_strncpyz( char *dest, const char *src, int destsize ) {
-	qboolean overlap = qfalse;
-	size_t srcLen;
-
   if ( !dest ) {
     Com_Error( ERR_FATAL, "Q_strncpyz: NULL dest" );
   }
 	if ( !src ) {
-		//* ( int * ) 0 = 0x12345678;
 		Com_Error( ERR_FATAL, "Q_strncpyz: NULL src" );
 	}
 	if ( destsize < 1 ) {
-		Com_Error(ERR_FATAL,"Q_strncpyz: destsize < 1" );
-	}
-
-	srcLen = strlen(src) + 1;
-	// check for overlap
-	if (dest >= src  &&  dest <= (src + srcLen)) {
-		// dest starts in src range
-		Com_Printf("starts..\n");
-		overlap = qtrue;
-	} else if (dest <= src  &&  (dest + destsize) > src) {
-		// dest goes into src range
-		Com_Printf("goes into...\n");
-		overlap = qtrue;
-	}
-
-	if (overlap) {
-		Com_Printf("^1Q_strncpyz() destination and source overlap %p, %p  len %d\n", dest, src, destsize);
-		Com_Printf("src: '%s'\n", src);
-		//*(int *)0x0 = 6;
+		Com_Error(ERR_FATAL,"Q_strncpyz: destsize < 1" ); 
 	}
 
-	if (1) {  //(overlap) {
-		int i;
-
-
-		for (i = 0;  i < destsize  &&  src[i] != '\0';  i++) {
-			char c;
-
-			c = src[i];
-			dest[i] = c;
-		}
-
-		if (i < destsize) {
-			dest[i] = '\0';
-		}
-
-#if 0
-		for (  ;  i < destsize;  i++) {
-			dest[i] = '\0';
-		}
-#endif
-		dest[destsize - 1] = 0;
-		return;
-	} else {
-		strncpy( dest, src, destsize-1 );
-		dest[destsize-1] = 0;
-	}
+	strncpy( dest, src, destsize-1 );
+  dest[destsize-1] = 0;
 }
-
+                 
 int Q_stricmpn (const char *s1, const char *s2, int n) {
 	int		c1, c2;
 
@@ -959,11 +833,11 @@
            else
              return -1;
         }
-        else if ( s2==NULL ) {
+        else if ( s2==NULL )
           return 1;
-		}
 
 
+	
 	do {
 		c1 = *s1++;
 		c2 = *s2++;
@@ -971,7 +845,7 @@
 		if (!n--) {
 			return 0;		// strings are equal until end point
 		}
-
+		
 		if (c1 != c2) {
 			if (c1 >= 'a' && c1 <= 'z') {
 				c1 -= ('a' - 'A');
@@ -984,13 +858,13 @@
 			}
 		}
 	} while (c1);
-
+	
 	return 0;		// strings are equal
 }
 
 int Q_strncmp (const char *s1, const char *s2, int n) {
 	int		c1, c2;
-
+	
 	do {
 		c1 = *s1++;
 		c2 = *s2++;
@@ -998,21 +872,17 @@
 		if (!n--) {
 			return 0;		// strings are equal until end point
 		}
-
+		
 		if (c1 != c2) {
 			return c1 < c2 ? -1 : 1;
 		}
 	} while (c1);
-
+	
 	return 0;		// strings are equal
 }
 
 int Q_stricmp (const char *s1, const char *s2) {
-	int r;
-
-	r = (s1 && s2) ? Q_stricmpn (s1, s2, 99999) : -1;
-
-	return r;
+	return (s1 && s2) ? Q_stricmpn (s1, s2, 99999) : -1;
 }
 
 
@@ -1116,7 +986,7 @@
 	while ((c = *s) != 0 ) {
 		if ( Q_IsColorString( s ) ) {
 			s++;
-		}
+		}		
 		else if ( c >= 0x20 && c <= 0x7E ) {
 			*d++ = c;
 		}
@@ -1130,78 +1000,17 @@
 int Q_CountChar(const char *string, char tocount)
 {
 	int count;
-
+	
 	for(count = 0; *string; string++)
 	{
 		if(*string == tocount)
 			count++;
 	}
-
+	
 	return count;
 }
 
-double Q_ParseClockTime (const char *timeString)
-{
-	int slen;
-	int colonCount;
-	int i;
-	double clockTime;
-	char buf[MAX_STRING_CHARS];
-	int minutes;
-	int seconds;
-	int hours;
-	int j;
-
-	slen = strlen(timeString);
-	colonCount = 0;
-	for (i = 0;  i < slen;  i++) {
-		if (timeString[i] == ':') {
-			colonCount++;
-		}
-	}
-
-	if (colonCount == 1) {
-		// minutes and seconds
-		for (i = 0;  i < slen;  i++) {
-			if (timeString[i] == ':') {
-				break;
-			}
-			buf[i] = timeString[i];
-		}
-		buf[i] = '\0';
-		hours = 0;
-		minutes = atoi(buf);
-		seconds = atof(timeString + i + 1);
-	} else if (colonCount == 2) {
-		for (i = 0;  i < slen;  i++) {
-			if (timeString[i] == ':') {
-				break;
-			}
-			buf[i] = timeString[i];
-		}
-		buf[i] = '\0';
-		hours = atoi(buf);
-		i++;
-		for (j = 0;  i < slen;  i++, j++) {
-			if (timeString[i] == ':') {
-				break;
-			}
-			buf[j] = timeString[i];
-		}
-		buf[j] = '\0';
-		minutes = atoi(buf);
-		seconds = atof(timeString + i + 1);
-	} else {
-		Com_Printf("Q_ParseClockTime() bad string '%s', needs to be in clock format:   1:38, 15:01, 0:15, etc... \n", timeString);
-		return -1;
-	}
-
-	clockTime = ((double)hours * 60.0 * 60.0 + (double)minutes * 60.0 + seconds) * 1000.0;
-
-	return clockTime;
-}
-
-int QDECL Com_sprintf( char *dest, int size, const char *fmt, ...)
+int QDECL Com_sprintf(char *dest, int size, const char *fmt, ...)
 {
 	int		len;
 	va_list		argptr;
@@ -1210,12 +1019,9 @@
 	len = Q_vsnprintf(dest, size, fmt, argptr);
 	va_end (argptr);
 
-	if (len >= size) {
-		//Com_Printf("^5  vsnprintf: '%s'\n", dest);
+	if(len >= size)
 		Com_Printf("Com_sprintf: Output length %d too short, require %d bytes.\n", size, len + 1);
-		//Crash();
-	}
-
+	
 	return len;
 }
 
@@ -1227,7 +1033,7 @@
 varargs versions of all text functions.
 ============
 */
-char	* QDECL va( const char *format, ... ) {
+char	* QDECL va( char *format, ... ) {
 	va_list		argptr;
 	static char string[2][32000]; // in case va is called by nested functions
 	static int	index = 0;
@@ -1281,15 +1087,13 @@
 FIXME: overflow check?
 ===============
 */
-char *Info_ValueForKeyExt( const char *s, const char *key, qboolean *hasKey ) {
+char *Info_ValueForKey( const char *s, const char *key ) {
 	char	pkey[BIG_INFO_KEY];
 	static	char value[2][BIG_INFO_VALUE];	// use two buffers so compares
 											// work without stomping on each other
 	static	int	valueindex = 0;
 	char	*o;
-
-	*hasKey = qfalse;
-
+	
 	if ( !s || !key ) {
 		return "";
 	}
@@ -1321,12 +1125,8 @@
 		}
 		*o = 0;
 
-		if (!Q_stricmp (key, pkey)) {
-			if (*value[valueindex]) {
-				*hasKey = qtrue;
-			}
+		if (!Q_stricmp (key, pkey) )
 			return value[valueindex];
-		}
 
 		if (!*s)
 			break;
@@ -1336,12 +1136,6 @@
 	return "";
 }
 
-char *Info_ValueForKey (const char *s, const char *key)
-{
-	qboolean b;
-
-	return Info_ValueForKeyExt(s, key, &b);
-}
 
 /*
 ===================
@@ -1549,13 +1343,11 @@
 			return;
 		}
 	}
-
+	
 	Info_RemoveKey (s, key);
 	if (!value || !strlen(value))
 		return;
 
-	//Com_Printf("^2set value for key: '%s' '%s'\n", key, value);
-
 	Com_sprintf (newi, sizeof(newi), "\\%s\\%s", key, value);
 
 	if (strlen(newi) + strlen(s) >= MAX_INFO_STRING)
@@ -1678,125 +1470,3 @@
 	else
 		return s;
 }
-
-void Crash (void)
-{
-	*(volatile int *) 0 = 0x555;
-}
-
-void Q_PrintSubString (const char *start, const char *end)
-{
-	const char *p;
-
-	p = start;
-
-	while (p < end  &&  p[0] != '\0') {
-		Com_Printf("%c", p[0]);
-		p++;
-	}
-}
-
-//FIXME check for invalid unicode code points, invalid UTF-8 strings
-//FIXME invalid unicode sequences should parse whatever is available?
-// assumes null terminated input string
-
-int Q_GetCpFromUtf8 (const char *s, int *bytes, qboolean *error)
-{
-	unsigned char c;
-	int b0, b1, b2, b3;
-
-	*error = qfalse;
-
-	c = s[0];
-	if (c <= 0x7f) {  // 1 byte 0xxxxxxx
-		*bytes = 1;
-		return c;
-	} else if ((c & 0xe0) == 0xc0) {  // 2 bytes 110xxxxx 10xxxxxx
-		if (qfalse) {  //(s[1] == '\0') {  // not enough bytes to read
-			Com_Printf("^3Q_GetCpFromUtf8 two byte UTF-8 sequence terminated, %d\n", c);
-			*bytes = 1;
-			//FIXME return a standard invalid char
-			*error = qtrue;
-			return c;
-		}
-		*bytes = 2;
-		b0 = c;
-		b1 = s[1];
-		return ( ((b0 & 0x1f) << 6) | (b1 & 0x3f) );
-	} else if ((c & 0xf0) == 0xe0) {  // 3 bytes 1110xxxx 10xxxxxx 10xxxxxx
-		if (qfalse) {  //(s[1] == '\0'  ||  s[2] == '\0') {
-			Com_Printf("^3Q_GetCpFromUtf8  three byte UTF-8 sequence terminated, %d\n", c);
-			//Com_Printf("%s\n", s);
-			*bytes = 1;
-			//FIXME return a standard invalid char
-			*error = qtrue;
-			return c;
-		}
-		*bytes = 3;
-		b0 = c;
-		b1 = s[1];
-		b2 = s[2];
-		return ( ((b0 & 0xf) << 12) | ((b1 & 0x3f) << 6) | (b2 & 0x3f));
-	} else if ((c & 0xf8) == 0xf0) {  // 4 bytes 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
-		if (qfalse) {  //(s[1] == '\0'  ||  s[2] == '\0'  ||  s[3] == '\0') {
-			Com_Printf("^3Q_GetCpFromUtf8  four byte UTF-8 sequence terminated, %d\n", c);
-			*bytes = 1;
-			//FIXME return a standard invalid char
-			*error = qtrue;
-			return c;
-		}
-		*bytes = 4;
-		b0 = c;
-		b1 = s[1];
-		b2 = s[2];
-		b3 = s[3];
-		return ( ((b0 & 0x7) << 18) | ((b1 & 0x3f) << 12) | ((b2 & 0x3f) << 6) | (b3 & 0x3f));
-	}
-
-	// invalid number of bytes
-	Com_Printf("^3Q_GetCpFromUtf8  invalid number of bytes specified in UTF-8 character %d\n", c);
-	*error = qtrue;
-	*bytes = 1;
-	return c;
-}
-
-//FIXME implement
-void Q_GetUtf8FromCp (int codePoint, char *buffer, int *numBytes, qboolean *error)
-{
-	*error = qfalse;
-
-	//FIXME bad encodings
-
-	if (codePoint < 0) {
-		Com_Printf("^3Q_GetUtf8FromCp:  codePoint less than zero  %d\n", codePoint);
-		goto err;
-	} else if (codePoint <= 0x7f) {  // 7bits: 0xxxxxxx
-		buffer[0] = codePoint;
-		*numBytes = 1;
-		return;
-	} else if (codePoint <= 0x7ff) {  // 11bits: 110xxxxx 10xxxxxx
-		buffer[0] = ((codePoint >> 6) & 0x1f) | 0xc0;
-		buffer[1] = (codePoint & 0x3f) | 0x80;
-		*numBytes = 2;
-		return;
-	} else if (codePoint <= 0xffff) {  // 16bits: 1110xxxx 10xxxxxx 10xxxxxx
-		buffer[0] = ((codePoint >> 12) & 0xf) | 0xe0;
-		buffer[1] = ((codePoint >> 6) & 0x3f) | 0x80;
-		buffer[2] = (codePoint & 0x3f) | 0x80;
-		*numBytes = 3;
-		return;
-	} else if (codePoint <= 0x1fffff) {  // 21bits: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
-		//FIXME Unicode max is U+10FFFF
-		buffer[0] = ((codePoint >> 18) & 0x7) | 0xf0;
-		buffer[1] = ((codePoint >> 12) & 0x3f) | 0x80;
-		buffer[2] = ((codePoint >> 6) & 0x3f) | 0x80;
-		buffer[3] = (codePoint & 0x3f) | 0x80;
-		*numBytes = 4;
-		return;
-	}
-
- err:
-	buffer[0] = codePoint & 127;
-	*numBytes = 1;
-	*error = qtrue;
-}

```

### `quake3e`  — sha256 `54f3936e5cb5...`, 41995 bytes

_Diff stat: +1166 / -732 lines_

_(full diff is 53114 bytes — see files directly)_

### `openarena-engine`  — sha256 `aae62c8b70c7...`, 26691 bytes

_Diff stat: +97 / -428 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\q_shared.c	2026-04-16 20:02:25.226257200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\q_shared.c	2026-04-16 22:48:25.912364200 +0100
@@ -23,53 +23,6 @@
 // q_shared.c -- stateless support routines that are included in each code dll
 #include "q_shared.h"
 
-const char *MonthAbbrev[12] = { "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" };
-const char *DayAbbrev[7] = { "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" };
-
-// ^[0-9a-zA-Z]
-qboolean Q_IsColorString(const char *p) {
-	if (!p)
-		return qfalse;
-
-	if (p[0] != Q_COLOR_ESCAPE)
-		return qfalse;
-
-	if (p[1] == 0)
-		return qfalse;
-
-	// isalnum expects a signed integer in the range -1 (EOF) to 255, or it might assert on undefined behaviour
-	// a dereferenced char pointer has the range -128 to 127, so we just need to rangecheck the negative part
-	if (p[1] < 0)
-		return qfalse;
-
-	if (isalnum(p[1]) == 0)
-		return qfalse;
-
-	return qtrue;
-}
-
-// ^[0-9a-zA-Z]
-qboolean Q_IsColorStringPicString(const floatint_t *p) {
-	if (!p)
-		return qfalse;
-
-	if (p[0].i != Q_COLOR_ESCAPE)
-		return qfalse;
-
-	if (p[1].i == 0)
-		return qfalse;
-
-	// isalnum expects a signed integer in the range -1 (EOF) to 255, or it might assert on undefined behaviour
-	// a dereferenced char pointer has the range -128 to 127, so we just need to rangecheck the negative part
-	if (p[1].i < 0)
-		return qfalse;
-
-	if (isalnum(p[1].i) == 0)
-		return qfalse;
-
-	return qtrue;
-}
-
 float Com_Clamp( float min, float max, float value ) {
 	if ( value < min ) {
 		return min;
@@ -89,7 +42,7 @@
 char *COM_SkipPath (char *pathname)
 {
 	char	*last;
-
+	
 	last = pathname;
 	while (*pathname)
 	{
@@ -120,39 +73,17 @@
 COM_StripExtension
 ============
 */
-// allow overlapping array ranges
 void COM_StripExtension( const char *in, char *out, int destsize )
 {
-	const char *dot;
-	const char *slash;
-	int n;
-	int i;
-
-	dot = strrchr(in, '.');
-	slash = strrchr(in, '/');
-
-	if (dot  &&  (!slash  ||  slash < dot)) {
-		if (destsize < (dot - in + 1)) {
-			n = destsize;
-		} else {
-			n = dot - in + 1;
-		}
-	} else {
-		n = destsize;
-	}
+	const char *dot = strrchr(in, '.'), *slash;
 
-	for (i = 0;  i < n  &&  in[i] != '\0';  i++) {
-		char c;
+	if (dot && (!(slash = strrchr(in, '/')) || slash < dot))
+		destsize = (destsize < dot-in+1 ? destsize : dot-in+1);
 
-		c = in[i];
-		out[i] = c;
-	}
-
-	if (i < n) {
-		out[i] = '\0';
-	}
-
-	out[n - 1] = '\0';
+	if ( in == out && destsize > 1 )
+		out[destsize-1] = '\0';
+	else
+		Q_strncpyz(out, in, destsize);
 }
 
 /*
@@ -165,18 +96,18 @@
 qboolean COM_CompareExtension(const char *in, const char *ext)
 {
 	int inlen, extlen;
-
+	
 	inlen = strlen(in);
 	extlen = strlen(ext);
-
+	
 	if(extlen <= inlen)
-        {
-			in += inlen - extlen;
-
-			if(!Q_stricmp(in, ext))
-				return qtrue;
-        }
-
+	{
+		in += inlen - extlen;
+		
+		if(!Q_stricmp(in, ext))
+			return qtrue;
+	}
+	
 	return qfalse;
 }
 
@@ -359,7 +290,7 @@
 static	char	com_token[MAX_TOKEN_CHARS];
 static	char	com_parsename[MAX_TOKEN_CHARS];
 static	int		com_lines;
-static int 		com_tokenline;
+static	int		com_tokenline;
 
 void COM_BeginParseSession( const char *name )
 {
@@ -444,6 +375,13 @@
 	in = out = data_p;
 	if (in) {
 		while ((c = *in) != 0) {
+
+			// try for glsl escape sequence
+			if ( c == '/' && in[1] == '/' && in[2]=='G' && in[3]=='L' && in[4]=='S' && in[5]=='L') {
+				in+=6;
+				c = *in; if (c==0 || *in == '\n') break;
+			}
+
 			// skip double slash comments
 			if ( c == '/' && in[1] == '/' ) {
 				while (*in && *in != '\n') {
@@ -516,12 +454,9 @@
 	com_token[0] = 0;
 	com_tokenline = 0;
 
-	//Com_Printf("xxx '%s'\n", *data_p);
-
 	// make sure incoming data is valid
 	if ( !data )
 	{
-		//Com_Printf("COM_ParseExt() data invalid\n");
 		*data_p = NULL;
 		return com_token;
 	}
@@ -543,6 +478,13 @@
 
 		c = *data;
 
+		// try for glsl program sequence
+		if ( c == '/' && data[1] == '/' && data[2]=='G' && data[3]=='L' && data[4]=='S' && data[5]=='L' )
+		{
+			data += 6;
+			c = *data; if (c==0 || *data == '\n') break;
+		}
+
 		// skip double slash comments
 		if ( c == '/' && data[1] == '/' )
 		{
@@ -639,7 +581,7 @@
 =================
 SkipBracedSection
 
-The next token should be an open brace  or set depth to 1 if already parsed it.
+The next token should be an open brace or set depth to 1 if already parsed it.
 Skips until a matching close brace is found.
 Internal brace depths are properly skipped.
 =================
@@ -672,12 +614,6 @@
 	int		c;
 
 	p = *data;
-
-	if ( !*p ) {
-		Com_Printf("^3WARNING SkipRestOfLine *p == null\n");
-		return;
-	}
-
 	while ( (c = *p++) != 0 ) {
 		if ( c == '\n' ) {
 			com_lines++;
@@ -734,15 +670,15 @@
 */
 int Com_HexStrToInt( const char *str )
 {
-	if ( !str )
+	if ( !str || !str[ 0 ] )
 		return -1;
 
 	// check for hex code
-	if( str[ 0 ] == '0' && str[ 1 ] == 'x' && str[ 2 ] != '\0' )
+	if( str[ 0 ] == '0' && str[ 1 ] == 'x' )
 	{
-		int i, n = 0, len = strlen( str );
+		int i, n = 0;
 
-		for( i = 2; i < len; i++ )
+		for( i = 2; i < strlen( str ); i++ )
 		{
 			char digit;
 
@@ -802,19 +738,10 @@
 	return ( 0 );
 }
 
-qboolean Q_isdigit (char c)
-{
-	if (c < '0'  ||  c > '9') {
-		return qfalse;
-	}
-
-	return qtrue;
-}
-
 qboolean Q_isanumber( const char *s )
 {
 	char *p;
-	double Q_UNUSED_VAR d;
+	double UNUSED_VAR d;
 
 	if( *s == '\0' )
 		return qfalse;
@@ -824,45 +751,25 @@
 	return *p == '\0';
 }
 
-qboolean Q_isAnInteger (const char *s)
-{
-	if (!s  ||  !*s) {
-		return qfalse;
-	}
-
-	while (1) {
-		if (!*s) {
-			break;
-		}
-		if (s[0] < '0'  ||  s[0] > '9') {
-			return qfalse;
-		}
-		s++;
-	}
-
-	return qtrue;
-}
-
 qboolean Q_isintegral( float f )
 {
 	return (int)f == f;
 }
 
-#ifdef _WIN32
+#ifdef _MSC_VER
 /*
 =============
 Q_vsnprintf
-
+ 
 Special wrapper function for Microsoft's broken _vsnprintf() function.
-MinGW comes with its own vsnprintf() which is not broken. mingw-w64
-however, uses Microsoft's broken _vsnprintf() function.
+MinGW comes with its own snprintf() which is not broken.
 =============
 */
 
 int Q_vsnprintf(char *str, size_t size, const char *format, va_list ap)
 {
 	int retval;
-
+	
 	retval = _vsnprintf(str, size, format, ap);
 
 	if(retval < 0 || retval == size)
@@ -873,83 +780,56 @@
 		//
 		// Obviously we cannot determine that value from Microsoft's
 		// implementation, so we have no choice but to return size.
-
+		
 		str[size - 1] = '\0';
 		return size;
 	}
-
+	
 	return retval;
 }
 #endif
 
 /*
+ Copied from code/game/bg_lib.c
+ It is here to avoid undifined behavior when source and destination overlap.
+ This is used quite a lot in the code.
+ */
+char *Q_strncpy(char *strDest, const char *strSource, size_t count) {
+	char *s;
+
+	s = strDest;
+	while (*strSource && count) {
+		*s++ = *strSource++;
+		count--;
+	}
+	while (count--) {
+		*s++ = 0;
+	}
+	return strDest;
+}
+
+/*
 =============
 Q_strncpyz
-
+ 
 Safe strncpy that ensures a trailing zero
 =============
 */
 void Q_strncpyz( char *dest, const char *src, int destsize ) {
-	qboolean overlap = qfalse;
-	size_t srcLen;
-
   if ( !dest ) {
     Com_Error( ERR_FATAL, "Q_strncpyz: NULL dest" );
   }
 	if ( !src ) {
-		//* ( int * ) 0 = 0x12345678;
 		Com_Error( ERR_FATAL, "Q_strncpyz: NULL src" );
 	}
 	if ( destsize < 1 ) {
-		Com_Error(ERR_FATAL,"Q_strncpyz: destsize < 1" );
-	}
-
-	srcLen = strlen(src) + 1;
-	// check for overlap
-	if (dest >= src  &&  dest <= (src + srcLen)) {
-		// dest starts in src range
-		Com_Printf("starts..\n");
-		overlap = qtrue;
-	} else if (dest <= src  &&  (dest + destsize) > src) {
-		// dest goes into src range
-		Com_Printf("goes into...\n");
-		overlap = qtrue;
-	}
-
-	if (overlap) {
-		Com_Printf("^1Q_strncpyz() destination and source overlap %p, %p  len %d\n", dest, src, destsize);
-		Com_Printf("src: '%s'\n", src);
-		//*(int *)0x0 = 6;
+		Com_Error(ERR_FATAL,"Q_strncpyz: destsize < 1" ); 
 	}
 
-	if (1) {  //(overlap) {
-		int i;
-
-
-		for (i = 0;  i < destsize  &&  src[i] != '\0';  i++) {
-			char c;
-
-			c = src[i];
-			dest[i] = c;
-		}
-
-		if (i < destsize) {
-			dest[i] = '\0';
-		}
-
-#if 0
-		for (  ;  i < destsize;  i++) {
-			dest[i] = '\0';
-		}
-#endif
-		dest[destsize - 1] = 0;
-		return;
-	} else {
-		strncpy( dest, src, destsize-1 );
-		dest[destsize-1] = 0;
-	}
+	Q_strncpy( dest, src, destsize-1 );
+  dest[destsize-1] = 0;
 }
-
+                 
 int Q_stricmpn (const char *s1, const char *s2, int n) {
 	int		c1, c2;
 
@@ -959,11 +839,11 @@
            else
              return -1;
         }
-        else if ( s2==NULL ) {
+        else if ( s2==NULL )
           return 1;
-		}
 
 
+	
 	do {
 		c1 = *s1++;
 		c2 = *s2++;
@@ -971,7 +851,7 @@
 		if (!n--) {
 			return 0;		// strings are equal until end point
 		}
-
+		
 		if (c1 != c2) {
 			if (c1 >= 'a' && c1 <= 'z') {
 				c1 -= ('a' - 'A');
@@ -984,13 +864,13 @@
 			}
 		}
 	} while (c1);
-
+	
 	return 0;		// strings are equal
 }
 
 int Q_strncmp (const char *s1, const char *s2, int n) {
 	int		c1, c2;
-
+	
 	do {
 		c1 = *s1++;
 		c2 = *s2++;
@@ -998,21 +878,17 @@
 		if (!n--) {
 			return 0;		// strings are equal until end point
 		}
-
+		
 		if (c1 != c2) {
 			return c1 < c2 ? -1 : 1;
 		}
 	} while (c1);
-
+	
 	return 0;		// strings are equal
 }
 
 int Q_stricmp (const char *s1, const char *s2) {
-	int r;
-
-	r = (s1 && s2) ? Q_stricmpn (s1, s2, 99999) : -1;
-
-	return r;
+	return (s1 && s2) ? Q_stricmpn (s1, s2, 99999) : -1;
 }
 
 
@@ -1116,7 +992,7 @@
 	while ((c = *s) != 0 ) {
 		if ( Q_IsColorString( s ) ) {
 			s++;
-		}
+		}		
 		else if ( c >= 0x20 && c <= 0x7E ) {
 			*d++ = c;
 		}
@@ -1130,78 +1006,17 @@
 int Q_CountChar(const char *string, char tocount)
 {
 	int count;
-
+	
 	for(count = 0; *string; string++)
 	{
 		if(*string == tocount)
 			count++;
 	}
-
+	
 	return count;
 }
 
-double Q_ParseClockTime (const char *timeString)
-{
-	int slen;
-	int colonCount;
-	int i;
-	double clockTime;
-	char buf[MAX_STRING_CHARS];
-	int minutes;
-	int seconds;
-	int hours;
-	int j;
-
-	slen = strlen(timeString);
-	colonCount = 0;
-	for (i = 0;  i < slen;  i++) {
-		if (timeString[i] == ':') {
-			colonCount++;
-		}
-	}
-
-	if (colonCount == 1) {
-		// minutes and seconds
-		for (i = 0;  i < slen;  i++) {
-			if (timeString[i] == ':') {
-				break;
-			}
-			buf[i] = timeString[i];
-		}
-		buf[i] = '\0';
-		hours = 0;
-		minutes = atoi(buf);
-		seconds = atof(timeString + i + 1);
-	} else if (colonCount == 2) {
-		for (i = 0;  i < slen;  i++) {
-			if (timeString[i] == ':') {
-				break;
-			}
-			buf[i] = timeString[i];
-		}
-		buf[i] = '\0';
-		hours = atoi(buf);
-		i++;
-		for (j = 0;  i < slen;  i++, j++) {
-			if (timeString[i] == ':') {
-				break;
-			}
-			buf[j] = timeString[i];
-		}
-		buf[j] = '\0';
-		minutes = atoi(buf);
-		seconds = atof(timeString + i + 1);
-	} else {
-		Com_Printf("Q_ParseClockTime() bad string '%s', needs to be in clock format:   1:38, 15:01, 0:15, etc... \n", timeString);
-		return -1;
-	}
-
-	clockTime = ((double)hours * 60.0 * 60.0 + (double)minutes * 60.0 + seconds) * 1000.0;
-
-	return clockTime;
-}
-
-int QDECL Com_sprintf( char *dest, int size, const char *fmt, ...)
+int QDECL Com_sprintf(char *dest, int size, const char *fmt, ...)
 {
 	int		len;
 	va_list		argptr;
@@ -1210,12 +1025,9 @@
 	len = Q_vsnprintf(dest, size, fmt, argptr);
 	va_end (argptr);
 
-	if (len >= size) {
-		//Com_Printf("^5  vsnprintf: '%s'\n", dest);
+	if(len >= size)
 		Com_Printf("Com_sprintf: Output length %d too short, require %d bytes.\n", size, len + 1);
-		//Crash();
-	}
-
+	
 	return len;
 }
 
@@ -1227,7 +1039,7 @@
 varargs versions of all text functions.
 ============
 */
-char	* QDECL va( const char *format, ... ) {
+char	* QDECL va( char *format, ... ) {
 	va_list		argptr;
 	static char string[2][32000]; // in case va is called by nested functions
 	static int	index = 0;
@@ -1281,15 +1093,13 @@
 FIXME: overflow check?
 ===============
 */
-char *Info_ValueForKeyExt( const char *s, const char *key, qboolean *hasKey ) {
+char *Info_ValueForKey( const char *s, const char *key ) {
 	char	pkey[BIG_INFO_KEY];
 	static	char value[2][BIG_INFO_VALUE];	// use two buffers so compares
 											// work without stomping on each other
 	static	int	valueindex = 0;
 	char	*o;
-
-	*hasKey = qfalse;
-
+	
 	if ( !s || !key ) {
 		return "";
 	}
@@ -1321,12 +1131,8 @@
 		}
 		*o = 0;
 
-		if (!Q_stricmp (key, pkey)) {
-			if (*value[valueindex]) {
-				*hasKey = qtrue;
-			}
+		if (!Q_stricmp (key, pkey) )
 			return value[valueindex];
-		}
 
 		if (!*s)
 			break;
@@ -1336,12 +1142,6 @@
 	return "";
 }
 
-char *Info_ValueForKey (const char *s, const char *key)
-{
-	qboolean b;
-
-	return Info_ValueForKeyExt(s, key, &b);
-}
 
 /*
 ===================
@@ -1427,7 +1227,7 @@
 		}
 		*o = 0;
 
-		if (!Q_stricmp (key, pkey) )
+		if (!strcmp (key, pkey) )
 		{
 			memmove(start, s, strlen(s) + 1); // remove this part
 			
@@ -1483,9 +1283,9 @@
 		}
 		*o = 0;
 
-		if (!Q_stricmp (key, pkey) )
+		if (!strcmp (key, pkey) )
 		{
-			memmove(start, s, strlen(s) + 1); // remove this part
+			strcpy (start, s);	// remove this part
 			return;
 		}
 
@@ -1507,22 +1307,12 @@
 ==================
 */
 qboolean Info_Validate( const char *s ) {
-	const char* ch = s;
-
-	while ( *ch != '\0' )
-	{
-		if( !Q_isprint( *ch ) )
-			return qfalse;
-
-		if( *ch == '\"' )
-			return qfalse;
-
-		if( *ch == ';' )
-			return qfalse;
-
-		++ch;
+	if ( strchr( s, '\"' ) ) {
+		return qfalse;
+	}
+	if ( strchr( s, ';' ) ) {
+		return qfalse;
 	}
-
 	return qtrue;
 }
 
@@ -1549,13 +1339,11 @@
 			return;
 		}
 	}
-
+	
 	Info_RemoveKey (s, key);
 	if (!value || !strlen(value))
 		return;
 
-	//Com_Printf("^2set value for key: '%s' '%s'\n", key, value);
-
 	Com_sprintf (newi, sizeof(newi), "\\%s\\%s", key, value);
 
 	if (strlen(newi) + strlen(s) >= MAX_INFO_STRING)
@@ -1679,124 +1467,5 @@
 		return s;
 }
 
-void Crash (void)
-{
-	*(volatile int *) 0 = 0x555;
-}
-
-void Q_PrintSubString (const char *start, const char *end)
-{
-	const char *p;
-
-	p = start;
-
-	while (p < end  &&  p[0] != '\0') {
-		Com_Printf("%c", p[0]);
-		p++;
-	}
-}
-
-//FIXME check for invalid unicode code points, invalid UTF-8 strings
-//FIXME invalid unicode sequences should parse whatever is available?
-// assumes null terminated input string
-
-int Q_GetCpFromUtf8 (const char *s, int *bytes, qboolean *error)
-{
-	unsigned char c;
-	int b0, b1, b2, b3;
-
-	*error = qfalse;
-
-	c = s[0];
-	if (c <= 0x7f) {  // 1 byte 0xxxxxxx
-		*bytes = 1;
-		return c;
-	} else if ((c & 0xe0) == 0xc0) {  // 2 bytes 110xxxxx 10xxxxxx
-		if (qfalse) {  //(s[1] == '\0') {  // not enough bytes to read
-			Com_Printf("^3Q_GetCpFromUtf8 two byte UTF-8 sequence terminated, %d\n", c);
-			*bytes = 1;
-			//FIXME return a standard invalid char
-			*error = qtrue;
-			return c;
-		}
-		*bytes = 2;
-		b0 = c;
-		b1 = s[1];
-		return ( ((b0 & 0x1f) << 6) | (b1 & 0x3f) );
-	} else if ((c & 0xf0) == 0xe0) {  // 3 bytes 1110xxxx 10xxxxxx 10xxxxxx
-		if (qfalse) {  //(s[1] == '\0'  ||  s[2] == '\0') {
-			Com_Printf("^3Q_GetCpFromUtf8  three byte UTF-8 sequence terminated, %d\n", c);
-			//Com_Printf("%s\n", s);
-			*bytes = 1;
-			//FIXME return a standard invalid char
-			*error = qtrue;
-			return c;
-		}
-		*bytes = 3;
-		b0 = c;
-		b1 = s[1];
-		b2 = s[2];
-		return ( ((b0 & 0xf) << 12) | ((b1 & 0x3f) << 6) | (b2 & 0x3f));
-	} else if ((c & 0xf8) == 0xf0) {  // 4 bytes 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
-		if (qfalse) {  //(s[1] == '\0'  ||  s[2] == '\0'  ||  s[3] == '\0') {
-			Com_Printf("^3Q_GetCpFromUtf8  four byte UTF-8 sequence terminated, %d\n", c);
-			*bytes = 1;
-			//FIXME return a standard invalid char
-			*error = qtrue;
-			return c;
-		}
-		*bytes = 4;
-		b0 = c;
-		b1 = s[1];
-		b2 = s[2];
-		b3 = s[3];
-		return ( ((b0 & 0x7) << 18) | ((b1 & 0x3f) << 12) | ((b2 & 0x3f) << 6) | (b3 & 0x3f));
-	}
-
-	// invalid number of bytes
-	Com_Printf("^3Q_GetCpFromUtf8  invalid number of bytes specified in UTF-8 character %d\n", c);
-	*error = qtrue;
-	*bytes = 1;
-	return c;
-}
-
-//FIXME implement
-void Q_GetUtf8FromCp (int codePoint, char *buffer, int *numBytes, qboolean *error)
-{
-	*error = qfalse;
-
-	//FIXME bad encodings
-
-	if (codePoint < 0) {
-		Com_Printf("^3Q_GetUtf8FromCp:  codePoint less than zero  %d\n", codePoint);
-		goto err;
-	} else if (codePoint <= 0x7f) {  // 7bits: 0xxxxxxx
-		buffer[0] = codePoint;
-		*numBytes = 1;
-		return;
-	} else if (codePoint <= 0x7ff) {  // 11bits: 110xxxxx 10xxxxxx
-		buffer[0] = ((codePoint >> 6) & 0x1f) | 0xc0;
-		buffer[1] = (codePoint & 0x3f) | 0x80;
-		*numBytes = 2;
-		return;
-	} else if (codePoint <= 0xffff) {  // 16bits: 1110xxxx 10xxxxxx 10xxxxxx
-		buffer[0] = ((codePoint >> 12) & 0xf) | 0xe0;
-		buffer[1] = ((codePoint >> 6) & 0x3f) | 0x80;
-		buffer[2] = (codePoint & 0x3f) | 0x80;
-		*numBytes = 3;
-		return;
-	} else if (codePoint <= 0x1fffff) {  // 21bits: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
-		//FIXME Unicode max is U+10FFFF
-		buffer[0] = ((codePoint >> 18) & 0x7) | 0xf0;
-		buffer[1] = ((codePoint >> 12) & 0x3f) | 0x80;
-		buffer[2] = ((codePoint >> 6) & 0x3f) | 0x80;
-		buffer[3] = (codePoint & 0x3f) | 0x80;
-		*numBytes = 4;
-		return;
-	}
-
- err:
-	buffer[0] = codePoint & 127;
-	*numBytes = 1;
-	*error = qtrue;
-}
+int vresWidth;
+int vresHeight;
\ No newline at end of file

```

### `openarena-gamecode`  — sha256 `1b0db1b25ff2...`, 23257 bytes

_Diff stat: +493 / -1044 lines_

_(full diff is 44132 bytes — see files directly)_
