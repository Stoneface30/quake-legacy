# Diff: `code/qcommon/vm.c`
**Canonical:** `wolfcamql-src` (sha256 `733f10a043fa...`, 24162 bytes)

## Variants

### `quake3-source`  — sha256 `8642def24635...`, 19629 bytes

_Diff stat: +171 / -386 lines_

_(full diff is 21871 bytes — see files directly)_

### `ioquake3`  — sha256 `170c8eb72f5f...`, 23288 bytes

_Diff stat: +18 / -58 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm.c	2026-04-16 20:02:25.228264200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\vm.c	2026-04-16 20:02:21.572103800 +0100
@@ -70,9 +70,9 @@
 ==============
 */
 void VM_Init( void ) {
-	Cvar_Get( "vm_cgame", "0", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
-	Cvar_Get( "vm_game", "0", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
-	Cvar_Get( "vm_ui", "0", CVAR_ARCHIVE );		// !@# SHIP WITH SET TO 2
+	Cvar_Get( "vm_cgame", "2", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
+	Cvar_Get( "vm_game", "2", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
+	Cvar_Get( "vm_ui", "2", CVAR_ARCHIVE );		// !@# SHIP WITH SET TO 2
 
 	Cmd_AddCommand ("vmprofile", VM_VmProfile_f );
 	Cmd_AddCommand ("vminfo", VM_VmInfo_f );
@@ -408,7 +408,7 @@
 		{
 			VM_Free(vm);
 			FS_FreeFile(header.v);
-
+			
 			Com_Printf(S_COLOR_YELLOW "Warning: %s has bad header\n", filename);
 			return NULL;
 		}
@@ -436,7 +436,7 @@
 		FS_FreeFile(header.v);
 
 		Com_Printf(S_COLOR_YELLOW "Warning: %s does not have a recognisable "
-				   "magic number in its header\n", filename);
+				"magic number in its header\n", filename);
 		return NULL;
 	}
 
@@ -465,10 +465,10 @@
 			FS_FreeFile(header.v);
 
 			Com_Printf(S_COLOR_YELLOW "Warning: Data region size of %s not matching after "
-					   "VM_Restart()\n", filename);
+					"VM_Restart()\n", filename);
 			return NULL;
 		}
-
+		
 		Com_Memset(vm->dataBase, 0, vm->dataAlloc);
 	}
 
@@ -502,7 +502,7 @@
 				FS_FreeFile(header.v);
 
 				Com_Printf(S_COLOR_YELLOW "Warning: Jump table size of %s not matching after "
-						   "VM_Restart()\n", filename);
+						"VM_Restart()\n", filename);
 				return NULL;
 			}
 
@@ -510,7 +510,7 @@
 		}
 
 		Com_Memcpy(vm->jumpTableTargets, (byte *) header.h + header.h->dataOffset +
-				   header.h->dataLength + header.h->litLength, header.h->jtrgLength);
+				header.h->dataLength + header.h->litLength, header.h->jtrgLength);
 
 		// byte swap the longs
 		for ( i = 0 ; i < header.h->jtrgLength ; i += 4 ) {
@@ -578,8 +578,8 @@
 	vm_t		*vm;
 	vmHeader_t	*header = NULL;
 	int			i, remaining, retval;
-	char		filename[MAX_OSPATH];
-	void		*startSearch = NULL;
+	char filename[MAX_OSPATH];
+	void *startSearch = NULL;
 
 	if ( !module || !module[0] || !systemCalls ) {
 		Com_Error( ERR_FATAL, "VM_Create: bad parms" );
@@ -613,19 +613,19 @@
 	do
 	{
 		retval = FS_FindVM(&startSearch, filename, sizeof(filename), module, (interpret == VMI_NATIVE));
-
+		
 		if(retval == VMI_NATIVE)
 		{
 			Com_Printf("Try loading dll file %s\n", filename);
 
 			vm->dllHandle = Sys_LoadGameDll(filename, &vm->entryPoint, VM_DllSyscall);
-
+			
 			if(vm->dllHandle)
 			{
 				vm->systemCall = systemCalls;
 				return vm;
 			}
-
+			
 			Com_Printf("Failed loading dll, trying next\n");
 		}
 		else if(retval == VMI_COMPILED)
@@ -638,7 +638,7 @@
 			Q_strncpyz(vm->name, module, sizeof(vm->name));
 		}
 	} while(retval >= 0);
-
+	
 	if(retval < 0)
 		return NULL;
 
@@ -697,12 +697,6 @@
 		return;
 	}
 
-#ifdef CGAME_HARD_LINKED
-	currentVM = NULL;
-	lastVM = NULL;
-	return;
-#endif
-
 	if(vm->callLevel) {
 		if(!forced_unload) {
 			Com_Error( ERR_FATAL, "VM_Free(%s) on running vm", vm->name );
@@ -759,13 +753,6 @@
 	if ( currentVM==NULL )
 	  return NULL;
 
-#ifdef CGAME_HARD_LINKED
-	if (currentVM == (vm_t *)1) {
-		return (void *)intValue;
-	}
-
-#endif
-
 	if ( currentVM->entryPoint ) {
 		return (void *)(currentVM->dataBase + intValue);
 	}
@@ -817,19 +804,14 @@
 ==============
 */
 
-#ifdef CGAME_HARD_LINKED
-int CgvmMain (int command, int arg0, int arg1, int arg2, int arg3, int arg4, int arg5, int arg6, int arg7, int arg8, int arg9, int arg10, int arg11);
-#endif
-
 intptr_t QDECL VM_Call( vm_t *vm, int callnum, ... )
 {
 	vm_t	*oldVM;
 	intptr_t r;
 	int i;
 
-	if(!vm || !vm->name[0]) {
-		Com_Error( ERR_FATAL, "VM_Call with NULL vm" );
-	}
+	if(!vm || !vm->name[0])
+		Com_Error(ERR_FATAL, "VM_Call with NULL vm");
 
 	oldVM = currentVM;
 	currentVM = vm;
@@ -839,26 +821,6 @@
 	  Com_Printf( "VM_Call( %d )\n", callnum );
 	}
 
-#ifdef CGAME_HARD_LINKED
-	if (vm == (vm_t *)1) {  // hack
-		int args[12];
-		va_list ap;
-		va_start(ap, callnum);
-		for (i = 0; i < ARRAY_LEN(args); i++) {
-			args[i] = va_arg(ap, int);
-		}
-		va_end(ap);
-
-		r = CgvmMain( callnum,  args[0],  args[1],  args[2], args[3],
-                            args[4],  args[5],  args[6], args[7],
-					  args[8],  args[9], args[10], args[11]);
-
-		if ( oldVM != NULL )
-			currentVM = oldVM;
-		return r;
-	}
-#endif
-
 	++vm->callLevel;
 	// if we have a dll loaded, call it directly
 	if ( vm->entryPoint ) {
@@ -871,11 +833,9 @@
 		}
 		va_end(ap);
 
-		//Com_Printf("^6vmCall %d\n", callnum);
-
 		r = vm->entryPoint( callnum,  args[0],  args[1],  args[2], args[3],
                             args[4],  args[5],  args[6], args[7],
-							args[8],  args[9], args[10], args[11]);
+                            args[8],  args[9], args[10], args[11]);
 	} else {
 #if ( id386 || idsparc ) && !defined __clang__ // calling convention doesn't need conversion in some cases
 #ifdef HAVE_VM_COMPILED

```

### `quake3e`  — sha256 `58d815edae6e...`, 54756 bytes

_Diff stat: +1559 / -380 lines_

_(full diff is 59507 bytes — see files directly)_

### `openarena-engine`  — sha256 `478c653d5198...`, 23157 bytes

_Diff stat: +25 / -67 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\vm.c	2026-04-16 20:02:25.228264200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\vm.c	2026-04-16 22:48:25.914363000 +0100
@@ -70,9 +70,9 @@
 ==============
 */
 void VM_Init( void ) {
-	Cvar_Get( "vm_cgame", "0", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
-	Cvar_Get( "vm_game", "0", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
-	Cvar_Get( "vm_ui", "0", CVAR_ARCHIVE );		// !@# SHIP WITH SET TO 2
+	Cvar_Get( "vm_cgame", "2", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
+	Cvar_Get( "vm_game", "2", CVAR_ARCHIVE );	// !@# SHIP WITH SET TO 2
+	Cvar_Get( "vm_ui", "2", CVAR_ARCHIVE );		// !@# SHIP WITH SET TO 2
 
 	Cmd_AddCommand ("vmprofile", VM_VmProfile_f );
 	Cmd_AddCommand ("vminfo", VM_VmInfo_f );
@@ -408,7 +408,7 @@
 		{
 			VM_Free(vm);
 			FS_FreeFile(header.v);
-
+			
 			Com_Printf(S_COLOR_YELLOW "Warning: %s has bad header\n", filename);
 			return NULL;
 		}
@@ -436,7 +436,7 @@
 		FS_FreeFile(header.v);
 
 		Com_Printf(S_COLOR_YELLOW "Warning: %s does not have a recognisable "
-				   "magic number in its header\n", filename);
+				"magic number in its header\n", filename);
 		return NULL;
 	}
 
@@ -451,25 +451,23 @@
 	if(alloc)
 	{
 		// allocate zero filled space for initialized and uninitialized data
-		// leave some space beyond data mask so we can secure all mask operations
-		vm->dataAlloc = dataLength + 4;
-		vm->dataBase = Hunk_Alloc(vm->dataAlloc, h_high);
+		vm->dataBase = Hunk_Alloc(dataLength, h_high);
 		vm->dataMask = dataLength - 1;
 	}
 	else
 	{
 		// clear the data, but make sure we're not clearing more than allocated
-		if(vm->dataAlloc != dataLength + 4)
+		if(vm->dataMask + 1 != dataLength)
 		{
 			VM_Free(vm);
 			FS_FreeFile(header.v);
 
 			Com_Printf(S_COLOR_YELLOW "Warning: Data region size of %s not matching after "
-					   "VM_Restart()\n", filename);
+					"VM_Restart()\n", filename);
 			return NULL;
 		}
-
-		Com_Memset(vm->dataBase, 0, vm->dataAlloc);
+		
+		Com_Memset(vm->dataBase, 0, dataLength);
 	}
 
 	// copy the intialized data
@@ -502,7 +500,7 @@
 				FS_FreeFile(header.v);
 
 				Com_Printf(S_COLOR_YELLOW "Warning: Jump table size of %s not matching after "
-						   "VM_Restart()\n", filename);
+						"VM_Restart()\n", filename);
 				return NULL;
 			}
 
@@ -510,7 +508,7 @@
 		}
 
 		Com_Memcpy(vm->jumpTableTargets, (byte *) header.h + header.h->dataOffset +
-				   header.h->dataLength + header.h->litLength, header.h->jtrgLength);
+				header.h->dataLength + header.h->litLength, header.h->jtrgLength);
 
 		// byte swap the longs
 		for ( i = 0 ; i < header.h->jtrgLength ; i += 4 ) {
@@ -576,10 +574,10 @@
 vm_t *VM_Create( const char *module, intptr_t (*systemCalls)(intptr_t *), 
 				vmInterpret_t interpret ) {
 	vm_t		*vm;
-	vmHeader_t	*header = NULL;
+	vmHeader_t	*header;
 	int			i, remaining, retval;
-	char		filename[MAX_OSPATH];
-	void		*startSearch = NULL;
+	char filename[MAX_OSPATH];
+	void *startSearch = NULL;
 
 	if ( !module || !module[0] || !systemCalls ) {
 		Com_Error( ERR_FATAL, "VM_Create: bad parms" );
@@ -613,19 +611,19 @@
 	do
 	{
 		retval = FS_FindVM(&startSearch, filename, sizeof(filename), module, (interpret == VMI_NATIVE));
-
+		
 		if(retval == VMI_NATIVE)
 		{
 			Com_Printf("Try loading dll file %s\n", filename);
 
 			vm->dllHandle = Sys_LoadGameDll(filename, &vm->entryPoint, VM_DllSyscall);
-
+			
 			if(vm->dllHandle)
 			{
 				vm->systemCall = systemCalls;
 				return vm;
 			}
-
+			
 			Com_Printf("Failed loading dll, trying next\n");
 		}
 		else if(retval == VMI_COMPILED)
@@ -638,7 +636,7 @@
 			Q_strncpyz(vm->name, module, sizeof(vm->name));
 		}
 	} while(retval >= 0);
-
+	
 	if(retval < 0)
 		return NULL;
 
@@ -653,7 +651,7 @@
 
 	vm->compiled = qfalse;
 
-#ifndef HAVE_VM_COMPILED
+#ifdef NO_VM_COMPILED
 	if(interpret >= VMI_COMPILED) {
 		Com_Printf("Architecture doesn't have a bytecode compiler, using interpreter\n");
 		interpret = VMI_BYTECODE;
@@ -697,12 +695,6 @@
 		return;
 	}
 
-#ifdef CGAME_HARD_LINKED
-	currentVM = NULL;
-	lastVM = NULL;
-	return;
-#endif
-
 	if(vm->callLevel) {
 		if(!forced_unload) {
 			Com_Error( ERR_FATAL, "VM_Free(%s) on running vm", vm->name );
@@ -759,13 +751,6 @@
 	if ( currentVM==NULL )
 	  return NULL;
 
-#ifdef CGAME_HARD_LINKED
-	if (currentVM == (vm_t *)1) {
-		return (void *)intValue;
-	}
-
-#endif
-
 	if ( currentVM->entryPoint ) {
 		return (void *)(currentVM->dataBase + intValue);
 	}
@@ -817,19 +802,14 @@
 ==============
 */
 
-#ifdef CGAME_HARD_LINKED
-int CgvmMain (int command, int arg0, int arg1, int arg2, int arg3, int arg4, int arg5, int arg6, int arg7, int arg8, int arg9, int arg10, int arg11);
-#endif
-
 intptr_t QDECL VM_Call( vm_t *vm, int callnum, ... )
 {
 	vm_t	*oldVM;
 	intptr_t r;
 	int i;
 
-	if(!vm || !vm->name[0]) {
-		Com_Error( ERR_FATAL, "VM_Call with NULL vm" );
-	}
+	if(!vm || !vm->name[0])
+		Com_Error(ERR_FATAL, "VM_Call with NULL vm");
 
 	oldVM = currentVM;
 	currentVM = vm;
@@ -839,26 +819,6 @@
 	  Com_Printf( "VM_Call( %d )\n", callnum );
 	}
 
-#ifdef CGAME_HARD_LINKED
-	if (vm == (vm_t *)1) {  // hack
-		int args[12];
-		va_list ap;
-		va_start(ap, callnum);
-		for (i = 0; i < ARRAY_LEN(args); i++) {
-			args[i] = va_arg(ap, int);
-		}
-		va_end(ap);
-
-		r = CgvmMain( callnum,  args[0],  args[1],  args[2], args[3],
-                            args[4],  args[5],  args[6], args[7],
-					  args[8],  args[9], args[10], args[11]);
-
-		if ( oldVM != NULL )
-			currentVM = oldVM;
-		return r;
-	}
-#endif
-
 	++vm->callLevel;
 	// if we have a dll loaded, call it directly
 	if ( vm->entryPoint ) {
@@ -871,14 +831,12 @@
 		}
 		va_end(ap);
 
-		//Com_Printf("^6vmCall %d\n", callnum);
-
 		r = vm->entryPoint( callnum,  args[0],  args[1],  args[2], args[3],
                             args[4],  args[5],  args[6], args[7],
-							args[8],  args[9], args[10], args[11]);
+                            args[8],  args[9], args[10], args[11]);
 	} else {
 #if ( id386 || idsparc ) && !defined __clang__ // calling convention doesn't need conversion in some cases
-#ifdef HAVE_VM_COMPILED
+#ifndef NO_VM_COMPILED
 		if ( vm->compiled )
 			r = VM_CallCompiled( vm, (int*)&callnum );
 		else
@@ -897,7 +855,7 @@
 			a.args[i] = va_arg(ap, int);
 		}
 		va_end(ap);
-#ifdef HAVE_VM_COMPILED
+#ifndef NO_VM_COMPILED
 		if ( vm->compiled )
 			r = VM_CallCompiled( vm, &a.callnum );
 		else

```
