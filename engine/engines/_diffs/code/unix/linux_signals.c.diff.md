# Diff: `code/unix/linux_signals.c`
**Canonical:** `quake3e` (sha256 `ac97814de96f...`, 2488 bytes)

## Variants

### `quake3-source`  — sha256 `d5973a1570de...`, 2067 bytes

_Diff stat: +24 / -49 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\unix\linux_signals.c	2026-04-16 20:02:27.371644000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\unix\linux_signals.c	2026-04-16 20:02:19.998527400 +0100
@@ -15,72 +15,47 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 #include <signal.h>
 
-#ifdef _DEBUG
-#include <execinfo.h>
-#include <stdio.h>
-#include <stdlib.h>
-#include <unistd.h>
-#endif
-
-#include "../qcommon/q_shared.h"
+#include "../game/q_shared.h"
 #include "../qcommon/qcommon.h"
 #ifndef DEDICATED
 #include "../renderer/tr_local.h"
 #endif
 
-static qboolean signalcaught = qfalse;
+static qboolean signalcaught = qfalse;;
 
-extern void NORETURN Sys_Exit( int code );
+void Sys_Exit(int); // bk010104 - abstraction
 
-static void signal_handler( int sig )
+static void signal_handler(int sig) // bk010104 - replace this... (NOTE TTimo huh?)
 {
-	char msg[32];
+  if (signalcaught)
+  {
+    printf("DOUBLE SIGNAL FAULT: Received signal %d, exiting...\n", sig);
+    Sys_Exit(1); // bk010104 - abstraction
+  }
 
-	if ( signalcaught == qtrue )
-	{
-		printf( "DOUBLE SIGNAL FAULT: Received signal %d, exiting...\n", sig );
-		Sys_Exit( 1 ); // abstraction
-	}
-
-	printf( "Received signal %d, exiting...\n", sig );
-
-#ifdef _DEBUG
-	if ( sig == SIGSEGV || sig == SIGILL || sig == SIGBUS )
-	{
-		void *syms[10];
-		const size_t size = backtrace( syms, ARRAY_LEN( syms ) );
-		backtrace_symbols_fd( syms, size, STDERR_FILENO );
-	}
-#endif
-
-	signalcaught = qtrue;
-	sprintf( msg, "Signal caught (%d)", sig );
-	VM_Forced_Unload_Start();
+  signalcaught = qtrue;
+  printf("Received signal %d, exiting...\n", sig);
 #ifndef DEDICATED
-	CL_Shutdown( msg, qtrue );
+  GLimp_Shutdown(); // bk010104 - shouldn't this be CL_Shutdown
 #endif
-	SV_Shutdown( msg );
-	VM_Forced_Unload_Done();
-	Sys_Exit( 0 ); // send a 0 to avoid DOUBLE SIGNAL FAULT
+  Sys_Exit(0); // bk010104 - abstraction NOTE TTimo send a 0 to avoid DOUBLE SIGNAL FAULT
 }
 
-
-void InitSig( void )
+void InitSig(void)
 {
-	signal( SIGINT, SIG_IGN );
-	signal( SIGHUP, signal_handler );
-	signal( SIGQUIT, signal_handler );
-	signal( SIGILL, signal_handler );
-	signal( SIGTRAP, signal_handler );
-	signal( SIGIOT, signal_handler );
-	signal( SIGBUS, signal_handler );
-	signal( SIGFPE, signal_handler );
-	signal( SIGSEGV, signal_handler );
-	signal( SIGTERM, signal_handler );
+  signal(SIGHUP, signal_handler);
+  signal(SIGQUIT, signal_handler);
+  signal(SIGILL, signal_handler);
+  signal(SIGTRAP, signal_handler);
+  signal(SIGIOT, signal_handler);
+  signal(SIGBUS, signal_handler);
+  signal(SIGFPE, signal_handler);
+  signal(SIGSEGV, signal_handler);
+  signal(SIGTERM, signal_handler);
 }

```
