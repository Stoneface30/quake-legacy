# Diff: `huffman/pyhuffman.c`
**Canonical:** `demodumper` (sha256 `fb7aa69085be...`, 8720 bytes)

## Variants

### `qldemo-python`  — sha256 `1e5fcf805629...`, 8524 bytes

_Diff stat: +20 / -25 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\demodumper\huffman\pyhuffman.c	2026-04-16 20:02:27.596241700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\qldemo-python\huffman\pyhuffman.c	2026-04-16 20:02:26.530758300 +0100
@@ -132,20 +132,22 @@
     return stringBuf;
 }
 
-static char* readFloat( msg_t* msg ) {
+static double* readFloat( msg_t* msg ) {
   int l;
   int c;
   
   for (l=0; l<4; l++) {    
-    c = readByte( msg );        /* use ReadByte so -1 is out of bounds */
+    c = readByte( msg ); /* use ReadByte so -1 is out of bounds */
+    if (c == -1) {
+      printf("Out of bounds in float");
+    }
     stringBuf[ l ] = c;
   }
-  return stringBuf;
+  return (double*) stringBuf;
 }
 
 static PyObject * py_readfloat( PyObject *self, PyObject *args ) {
-  char* raw_float = readFloat(&msg);
-  return PyFloat_FromDouble(_PyFloat_Unpack4(raw_float, 1));
+  return Py_BuildValue("d", *readFloat(&msg));
 }
 
 static char* readBigString( msg_t* msg ) {
@@ -197,13 +199,14 @@
 static PyObject * py_fill( PyObject *self, PyObject *args )
 {
   int len = 0;
-  int count = 0;
 
   if ( !PyArg_ParseTuple( args, "i", &len ) )
     return NULL;
 
-  count = fread( &data, 1, len, file );
-  //printf( "real read %d %d\n", count, len );
+  int count = fread( &data, 1, len, file );
+  if (count < 1) {
+    printf( "real read %d %d\n", count, len );
+  }
 
   msg.bit = 0;
   msg.data = data;
@@ -252,7 +255,10 @@
 static PyObject * py_readrawlong( PyObject *self, PyObject *args )
 {
   int lng;
-  fread( &lng, sizeof( int ), 1, file );
+  int count = fread( &lng, sizeof( int ), 1, file );
+  if (count != 1) {
+    return PyInt_FromLong(-1L);
+  }
   return PyInt_FromLong( ( long )lng );
 }
 
@@ -274,29 +280,17 @@
   return PyInt_FromLong( ( long )readShort( &msg ) );
 }
 
-static PyObject * py_readlong( PyObject *self, PyObject *args )
-{
+static PyObject * py_readlong( PyObject *self, PyObject *args ) {
   return PyInt_FromLong( ( long )readLong( &msg ) );
 }
 
-static PyObject * py_readstring( PyObject *self, PyObject *args )
-{
-  //#if PY_MAJOR_VERSION >= 3
-  char* bob = readString( &msg );
-  return PyUnicode_DecodeLatin1(bob, strlen(bob), "strict" );
-  //#else
-  //return Py_BuildValue( "y", readString( &msg ));
-  //#endif
+static PyObject * py_readstring( PyObject *self, PyObject *args ) {
+  return Py_BuildValue("s", readString( &msg ));
 }
 
 static PyObject * py_readbigstring( PyObject *self, PyObject *args )
 {
-  //#if PY_MAJOR_VERSION >= 3
-  char* bob = readString( &msg );
-  return PyUnicode_DecodeLatin1(bob, strlen(bob), "strict" );
-  //#else
-  //return Py_BuildValue( "y", readBigString( &msg ));
-  //#endif
+  return Py_BuildValue("s", readBigString( &msg ));
 }
 
 
@@ -344,6 +338,7 @@
   m = PyModule_Create(&moduledef);
   if (m == NULL)
     return NULL;
+  return m;
 }
 #else
 PyMODINIT_FUNC inithuffman( void )

```
