# Diff: `code/qcommon/net_ip.c`
**Canonical:** `wolfcamql-src` (sha256 `e755099ad8ab...`, 43323 bytes)

## Variants

### `ioquake3`  — sha256 `f17c002cd53c...`, 43307 bytes

_Diff stat: +5 / -5 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\net_ip.c	2026-04-16 20:02:25.225256200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\qcommon\net_ip.c	2026-04-16 20:02:21.570109000 +0100
@@ -48,10 +48,10 @@
 
 // Undefine existing real error codes and replace
 // with our pretend compatibility layer ones
-#      undef EAGAIN
-#      undef EADDRNOTAVAIL
-#      undef EAFNOSUPPORT
-#      undef ECONNRESET
+#	undef EAGAIN
+#	undef EADDRNOTAVAIL
+#	undef EAFNOSUPPORT
+#	undef ECONNRESET
 
 #	define EAGAIN					WSAEWOULDBLOCK
 #	define EADDRNOTAVAIL	WSAEADDRNOTAVAIL
@@ -1053,7 +1053,7 @@
 	}
 }
 
-void NET_LeaveMulticast6()
+void NET_LeaveMulticast6(void)
 {
 	if(multicast6_socket != INVALID_SOCKET)
 	{

```

### `quake3e`  — sha256 `8c531eb4e584...`, 48724 bytes

_Diff stat: +622 / -402 lines_

_(full diff is 52846 bytes — see files directly)_

### `openarena-engine`  — sha256 `70cbb52c8aee...`, 43236 bytes

_Diff stat: +8 / -9 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\qcommon\net_ip.c	2026-04-16 20:02:25.225256200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\qcommon\net_ip.c	2026-04-16 22:48:25.910297500 +0100
@@ -27,6 +27,7 @@
 #	include <winsock2.h>
 #	include <ws2tcpip.h>
 #	if WINVER < 0x501
+
 #		ifdef __MINGW32__
 			// wspiapi.h isn't available on MinGW, so if it's
 			// present it's because the end user has added it
@@ -39,6 +40,11 @@
 #		include <ws2spi.h>
 #	endif
 
+			// leilei - addition to fix win9x
+#	ifdef USE_REACTOS_WINSOCK_HEADER
+#		include "../reactos/wspiapi.h"
+#	endif
+
 typedef int socklen_t;
 #	ifdef ADDRESS_FAMILY
 #		define sa_family_t	ADDRESS_FAMILY
@@ -46,13 +52,6 @@
 typedef unsigned short sa_family_t;
 #	endif
 
-// Undefine existing real error codes and replace
-// with our pretend compatibility layer ones
-#      undef EAGAIN
-#      undef EADDRNOTAVAIL
-#      undef EAFNOSUPPORT
-#      undef ECONNRESET
-
 #	define EAGAIN					WSAEWOULDBLOCK
 #	define EADDRNOTAVAIL	WSAEADDRNOTAVAIL
 #	define EAFNOSUPPORT		WSAEAFNOSUPPORT
@@ -1275,7 +1274,7 @@
 	}
 }
 
-#if defined(__linux__) || defined(__APPLE__) || defined(__BSD__)
+#if defined(__linux__) || defined(MACOSX) || defined(__BSD__)
 static void NET_GetLocalAddress(void)
 {
 	struct ifaddrs *ifap, *search;
@@ -1626,7 +1625,7 @@
 void NET_Event(fd_set *fdr)
 {
 	byte bufData[MAX_MSGLEN + 1];
-	netadr_t from = {0};
+	netadr_t from;
 	msg_t netmsg;
 	
 	while(1)

```
