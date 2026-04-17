# Diff: `code/game/bg_lib.c`
**Canonical:** `wolfcamql-src` (sha256 `08cd9ecd07e9...`, 60990 bytes)

## Variants

### `quake3-source`  — sha256 `6dd9c84dc018...`, 40501 bytes

_Diff stat: +288 / -1083 lines_

_(full diff is 36195 bytes — see files directly)_

### `ioquake3`  — sha256 `c0d26b6a9618...`, 61000 bytes

_Diff stat: +11 / -11 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_lib.c	2026-04-16 20:02:25.186107600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\game\bg_lib.c	2026-04-16 20:02:21.538886200 +0100
@@ -53,10 +53,10 @@
  */
 #define swapcode(TYPE, parmi, parmj, n) { 		\
 	long i = (n) / sizeof (TYPE); 			\
-	TYPE *pi = (TYPE *) (parmi); 		\
-	TYPE *pj = (TYPE *) (parmj); 		\
+	TYPE *pi = (TYPE *) (parmi); 			\
+	TYPE *pj = (TYPE *) (parmj); 			\
 	do { 						\
-		TYPE	t = *pi;		\
+		TYPE	t = *pi;			\
 		*pi++ = *pj;				\
 		*pj++ = t;				\
         } while (--i > 0);				\
@@ -233,7 +233,7 @@
 		}
 		string++;
 	}
-
+	
 	if(c)
 		return NULL;
 	else
@@ -243,7 +243,7 @@
 char *strrchr(const char *string, int c)
 {
 	const char *found = NULL;
-
+	
 	while(*string)
 	{
 		if(*string == c)
@@ -251,7 +251,7 @@
 
 		string++;
 	}
-
+	
 	if(c)
 		return (char *) found;
 	else
@@ -299,7 +299,7 @@
 		if(dest > src)
 		{
 			i = count;
-
+			
 			do
 			{
 				i--;
@@ -308,11 +308,11 @@
 		}
 		else
 		{
-			for(i = 0;  i < count; i++)
+			for(i = 0; i < count; i++)
 				((char *) dest)[i] = ((char *) src)[i];
 		}
 	}
-
+	
 	return dest;
 }
 
@@ -1750,7 +1750,7 @@
     }
   }
   if (maxlen > 0)
-      buffer[currlen] = '\0';
+    buffer[currlen] = '\0';
   return total;
 }
 
@@ -1967,7 +1967,7 @@
   if (fracpart >= powN (10, max))
   {
     intpart++;
-	fracpart -= powN (10, max);
+    fracpart -= powN (10, max);
   }
 
 #ifdef DEBUG_SNPRINTF

```

### `openarena-engine`  — sha256 `f948204d1a55...`, 61023 bytes

_Diff stat: +12 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\game\bg_lib.c	2026-04-16 20:02:25.186107600 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\game\bg_lib.c	2026-04-16 22:48:25.743535300 +0100
@@ -53,10 +53,10 @@
  */
 #define swapcode(TYPE, parmi, parmj, n) { 		\
 	long i = (n) / sizeof (TYPE); 			\
-	TYPE *pi = (TYPE *) (parmi); 		\
-	TYPE *pj = (TYPE *) (parmj); 		\
+	register TYPE *pi = (TYPE *) (parmi); 		\
+	register TYPE *pj = (TYPE *) (parmj); 		\
 	do { 						\
-		TYPE	t = *pi;		\
+		register TYPE	t = *pi;		\
 		*pi++ = *pj;				\
 		*pj++ = t;				\
         } while (--i > 0);				\
@@ -233,7 +233,7 @@
 		}
 		string++;
 	}
-
+	
 	if(c)
 		return NULL;
 	else
@@ -243,7 +243,7 @@
 char *strrchr(const char *string, int c)
 {
 	const char *found = NULL;
-
+	
 	while(*string)
 	{
 		if(*string == c)
@@ -251,7 +251,7 @@
 
 		string++;
 	}
-
+	
 	if(c)
 		return (char *) found;
 	else
@@ -299,7 +299,7 @@
 		if(dest > src)
 		{
 			i = count;
-
+			
 			do
 			{
 				i--;
@@ -308,11 +308,11 @@
 		}
 		else
 		{
-			for(i = 0;  i < count; i++)
+			for(i = 0; i < count; i++)
 				((char *) dest)[i] = ((char *) src)[i];
 		}
 	}
-
+	
 	return dest;
 }
 
@@ -1376,7 +1376,7 @@
  *    probably requires libm on most operating systems.  Don't yet
  *    support the exponent (e,E) and sigfig (g,G).  Also, fmtint()
  *    was pretty badly broken, it just wasn't being exercised in ways
- *    which showed it, so that's been fixed.  Also, formatted the code
+ *    which showed it, so that's been fixed.  Also, formated the code
  *    to mutt conventions, and removed dead code left over from the
  *    original.  Also, there is now a builtin-test, just compile with:
  *           gcc -DTEST_SNPRINTF -o snprintf snprintf.c -lm
@@ -1750,7 +1750,7 @@
     }
   }
   if (maxlen > 0)
-      buffer[currlen] = '\0';
+    buffer[currlen] = '\0';
   return total;
 }
 
@@ -1967,7 +1967,7 @@
   if (fracpart >= powN (10, max))
   {
     intpart++;
-	fracpart -= powN (10, max);
+    fracpart -= powN (10, max);
   }
 
 #ifdef DEBUG_SNPRINTF

```

### `openarena-gamecode`  — sha256 `752065312b5d...`, 62967 bytes

_Diff stat: +1191 / -1258 lines_

_(full diff is 102181 bytes — see files directly)_
