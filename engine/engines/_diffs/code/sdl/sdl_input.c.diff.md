# Diff: `code/sdl/sdl_input.c`
**Canonical:** `wolfcamql-src` (sha256 `84cbc5cd1cf1...`, 39644 bytes)

## Variants

### `ioquake3`  — sha256 `ba9ebeecc38f...`, 38479 bytes

_Diff stat: +44 / -74 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\sdl\sdl_input.c	2026-04-16 20:02:25.266779000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\sdl\sdl_input.c	2026-04-16 20:02:21.617760000 +0100
@@ -31,7 +31,6 @@
 #include <stdlib.h>
 
 #include "../client/client.h"
-#include "../client/keys.h"
 #include "../sys/sys_local.h"
 
 #if !SDL_VERSION_ATLEAST(2, 0, 17)
@@ -48,7 +47,6 @@
 
 static cvar_t *in_mouse             = NULL;
 static cvar_t *in_nograb;
-static cvar_t *in_checkForStolenMouseFocus = NULL;
 
 static cvar_t *in_joystick          = NULL;
 static cvar_t *in_joystickThreshold = NULL;
@@ -76,8 +74,8 @@
 		Com_Printf( "  " );
 
 	Com_Printf( "Scancode: 0x%02x(%s) Sym: 0x%02x(%s)",
-				keysym->scancode, SDL_GetScancodeName( keysym->scancode ),
-				keysym->sym, SDL_GetKeyName( keysym->sym ) );
+			keysym->scancode, SDL_GetScancodeName( keysym->scancode ),
+			keysym->sym, SDL_GetKeyName( keysym->sym ) );
 
 	if( keysym->mod & KMOD_LSHIFT )   Com_Printf( " KMOD_LSHIFT" );
 	if( keysym->mod & KMOD_RSHIFT )   Com_Printf( " KMOD_RSHIFT" );
@@ -141,7 +139,6 @@
 			int charCode = 0;
 
 			token = COM_Parse( &text_p );
-			//Com_Printf("consolekey: %s\n", token);
 			if( !token[ 0 ] )
 				break;
 
@@ -221,20 +218,20 @@
 		switch( keysym->sym )
 		{
 			case SDLK_PAGEUP:       key = K_PGUP;          break;
-			case SDLK_KP_9:          key = K_KP_PGUP;       break;
+			case SDLK_KP_9:         key = K_KP_PGUP;       break;
 			case SDLK_PAGEDOWN:     key = K_PGDN;          break;
-			case SDLK_KP_3:          key = K_KP_PGDN;       break;
-			case SDLK_KP_7:          key = K_KP_HOME;       break;
+			case SDLK_KP_3:         key = K_KP_PGDN;       break;
+			case SDLK_KP_7:         key = K_KP_HOME;       break;
 			case SDLK_HOME:         key = K_HOME;          break;
-			case SDLK_KP_1:          key = K_KP_END;        break;
+			case SDLK_KP_1:         key = K_KP_END;        break;
 			case SDLK_END:          key = K_END;           break;
-			case SDLK_KP_4:          key = K_KP_LEFTARROW;  break;
+			case SDLK_KP_4:         key = K_KP_LEFTARROW;  break;
 			case SDLK_LEFT:         key = K_LEFTARROW;     break;
-			case SDLK_KP_6:          key = K_KP_RIGHTARROW; break;
+			case SDLK_KP_6:         key = K_KP_RIGHTARROW; break;
 			case SDLK_RIGHT:        key = K_RIGHTARROW;    break;
-			case SDLK_KP_2:          key = K_KP_DOWNARROW;  break;
+			case SDLK_KP_2:         key = K_KP_DOWNARROW;  break;
 			case SDLK_DOWN:         key = K_DOWNARROW;     break;
-			case SDLK_KP_8:          key = K_KP_UPARROW;    break;
+			case SDLK_KP_8:         key = K_KP_UPARROW;    break;
 			case SDLK_UP:           key = K_UPARROW;       break;
 			case SDLK_ESCAPE:       key = K_ESCAPE;        break;
 			case SDLK_KP_ENTER:     key = K_KP_ENTER;      break;
@@ -278,12 +275,8 @@
 			case SDLK_RALT:
 			case SDLK_LALT:         key = K_ALT;           break;
 
-			// 2017-07-30 wc not in sdl2 ?
-			//case SDLK_LSUPER:
-			//case SDLK_RSUPER:       *key = K_SUPER;         break;
-
-			case SDLK_KP_5:      	key = K_KP_5;          break;
-		    case SDLK_INSERT:    	key = K_INS;           break;
+			case SDLK_KP_5:         key = K_KP_5;          break;
+			case SDLK_INSERT:       key = K_INS;           break;
 			case SDLK_KP_0:         key = K_KP_INS;        break;
 			case SDLK_KP_MULTIPLY:  key = K_KP_STAR;       break;
 			case SDLK_KP_PLUS:      key = K_KP_PLUS;       break;
@@ -291,19 +284,15 @@
 			case SDLK_KP_DIVIDE:    key = K_KP_SLASH;      break;
 
 			case SDLK_MODE:         key = K_MODE;          break;
-			//case SDLK_COMPOSE:      key = K_COMPOSE;       break;
 			case SDLK_HELP:         key = K_HELP;          break;
-			case SDLK_PRINTSCREEN:	key = K_PRINT;         break;
+			case SDLK_PRINTSCREEN:  key = K_PRINT;         break;
 			case SDLK_SYSREQ:       key = K_SYSREQ;        break;
-			//case SDLK_BREAK:        *key = K_BREAK;         break;
 			case SDLK_MENU:         key = K_MENU;          break;
-		    case SDLK_APPLICATION:  key = K_MENU;          break;
+			case SDLK_APPLICATION:	key = K_MENU;          break;
 			case SDLK_POWER:        key = K_POWER;         break;
-			//case SDLK_EURO:         *key = K_EURO;          break;
 			case SDLK_UNDO:         key = K_UNDO;          break;
-			case SDLK_SCROLLLOCK:    key = K_SCROLLOCK;     break;
-			//case SDLK_NUMLOCK:      *key = K_KP_NUMLOCK;    break;
-		    case SDLK_NUMLOCKCLEAR:	key = K_KP_NUMLOCK;    break;
+			case SDLK_SCROLLLOCK:   key = K_SCROLLOCK;     break;
+			case SDLK_NUMLOCKCLEAR: key = K_KP_NUMLOCK;    break;
 			case SDLK_CAPSLOCK:     key = K_CAPSLOCK;      break;
 
 			default:
@@ -321,7 +310,7 @@
 	}
 
 	if( in_keyboardDebug->integer )
-		IN_PrintKey( keysym, key,  down );
+		IN_PrintKey( keysym, key, down );
 
 	if( IN_IsConsoleKey( key, 0 ) )
 	{
@@ -345,7 +334,7 @@
 	// Gobble any mouse motion events
 	SDL_PumpEvents( );
 	while( ( val = SDL_PeepEvents( dummy, 1, SDL_GETEVENT,
-								   SDL_MOUSEMOTION, SDL_MOUSEMOTION ) ) > 0 ) { }
+		SDL_MOUSEMOTION, SDL_MOUSEMOTION ) ) > 0 ) { }
 
 	if ( val < 0 )
 		Com_Printf( "IN_GobbleMotionEvents failed: %s\n", SDL_GetError( ) );
@@ -413,7 +402,6 @@
 
 		SDL_SetWindowGrab( SDL_window, SDL_FALSE );
 		SDL_SetRelativeMouseMode( SDL_FALSE );
-		//Com_Printf("^3deactivate mouse\n");
 
 		// Don't warp the mouse unless the cursor is within the window
 		if( SDL_GetWindowFlags( SDL_window ) & SDL_WINDOW_MOUSE_FOCUS )
@@ -543,11 +531,11 @@
 		gamepad = SDL_GameControllerOpen(in_joystickNo->integer);
 
 	Com_DPrintf( "Joystick %d opened\n", in_joystickNo->integer );
-	Com_DPrintf( "Name:    %s\n", SDL_JoystickNameForIndex(in_joystickNo->integer) );
-	Com_DPrintf( "Axes:    %d\n", SDL_JoystickNumAxes(stick) );
-	Com_DPrintf( "Hats:    %d\n", SDL_JoystickNumHats(stick) );
-	Com_DPrintf( "Buttons: %d\n", SDL_JoystickNumButtons(stick) );
-	Com_DPrintf( "Balls: %d\n", SDL_JoystickNumBalls(stick) );
+	Com_DPrintf( "Name:       %s\n", SDL_JoystickNameForIndex(in_joystickNo->integer) );
+	Com_DPrintf( "Axes:       %d\n", SDL_JoystickNumAxes(stick) );
+	Com_DPrintf( "Hats:       %d\n", SDL_JoystickNumHats(stick) );
+	Com_DPrintf( "Buttons:    %d\n", SDL_JoystickNumButtons(stick) );
+	Com_DPrintf( "Balls:      %d\n", SDL_JoystickNumBalls(stick) );
 	Com_DPrintf( "Use Analog: %s\n", in_joystickUseAnalog->integer ? "Yes" : "No" );
 	Com_DPrintf( "Is gamepad: %s\n", gamepad ? "Yes" : "No" );
 
@@ -584,6 +572,7 @@
 	SDL_QuitSubSystem(SDL_INIT_JOYSTICK);
 }
 
+
 static qboolean KeyToAxisAndSign(int keynum, int *outAxis, int *outSign)
 {
 	char *bind;
@@ -822,6 +811,7 @@
 	}
 }
 
+
 /*
 ===============
 IN_JoyMove
@@ -1072,7 +1062,7 @@
 				lastKeyDown = 0;
 				break;
 
- 		    case SDL_TEXTINPUT:
+			case SDL_TEXTINPUT:
 				if( lastKeyDown != K_CONSOLE )
 				{
 					char *c = e.text.text;
@@ -1129,10 +1119,6 @@
 						break;
 					Com_QueueEvent( in_eventTime, SE_MOUSE, e.motion.xrel, e.motion.yrel, 0, NULL );
 				}
-				else
-				{
-					Com_QueueEvent( in_eventTime, SE_MOUSE_INACTIVE, e.motion.x, e.motion.y, 0, NULL );
-				}
 				break;
 
 			case SDL_MOUSEBUTTONDOWN:
@@ -1141,19 +1127,19 @@
 					int b;
 					switch( e.button.button )
 					{
-					case SDL_BUTTON_LEFT:    b = K_MOUSE1;     break;
-					case SDL_BUTTON_MIDDLE:    b = K_MOUSE3;     break;
-					case SDL_BUTTON_RIGHT:    b = K_MOUSE2;     break;
-					case SDL_BUTTON_X1:      b = K_MOUSE4;     break;
-					case SDL_BUTTON_X2:      b = K_MOUSE5;     break;
-					default:  b = K_AUX1 + ( e.button.button - SDL_BUTTON_X2 + 1 ) % 16; break;
+						case SDL_BUTTON_LEFT:   b = K_MOUSE1;     break;
+						case SDL_BUTTON_MIDDLE: b = K_MOUSE3;     break;
+						case SDL_BUTTON_RIGHT:  b = K_MOUSE2;     break;
+						case SDL_BUTTON_X1:     b = K_MOUSE4;     break;
+						case SDL_BUTTON_X2:     b = K_MOUSE5;     break;
+						default:                b = K_AUX1 + ( e.button.button - SDL_BUTTON_X2 + 1 ) % 16; break;
 					}
 					Com_QueueEvent( in_eventTime, SE_KEY, b,
 						( e.type == SDL_MOUSEBUTTONDOWN ? qtrue : qfalse ), 0, NULL );
 				}
 				break;
 
-		    case SDL_MOUSEWHEEL:
+			case SDL_MOUSEWHEEL:
 				if( e.wheel.y > 0 )
 				{
 					Com_QueueEvent( in_eventTime, SE_KEY, K_MWHEELUP, qtrue, 0, NULL );
@@ -1176,10 +1162,10 @@
 				Cbuf_ExecuteText(EXEC_NOW, "quit Closed window\n");
 				break;
 
-  		    case SDL_WINDOWEVENT:
+			case SDL_WINDOWEVENT:
 				switch( e.window.event )
 				{
-				    case SDL_WINDOWEVENT_RESIZED:
+					case SDL_WINDOWEVENT_RESIZED:
 						{
 							int width, height;
 
@@ -1209,13 +1195,13 @@
 						}
 						break;
 
-				    case SDL_WINDOWEVENT_MINIMIZED:    Cvar_SetValue( "com_minimized", 1 ); break;
-				    case SDL_WINDOWEVENT_RESTORED:
-				    case SDL_WINDOWEVENT_MAXIMIZED:    Cvar_SetValue( "com_minimized", 0 ); break;
-				    case SDL_WINDOWEVENT_FOCUS_LOST:   Cvar_SetValue( "com_unfocused", 1 ); break;
-				    case SDL_WINDOWEVENT_FOCUS_GAINED: Cvar_SetValue( "com_unfocused", 0 ); break;
+					case SDL_WINDOWEVENT_MINIMIZED:    Cvar_SetValue( "com_minimized", 1 ); break;
+					case SDL_WINDOWEVENT_RESTORED:
+					case SDL_WINDOWEVENT_MAXIMIZED:    Cvar_SetValue( "com_minimized", 0 ); break;
+					case SDL_WINDOWEVENT_FOCUS_LOST:   Cvar_SetValue( "com_unfocused", 1 ); break;
+					case SDL_WINDOWEVENT_FOCUS_GAINED: Cvar_SetValue( "com_unfocused", 0 ); break;
 				}
-			break;
+				break;
 
 #if defined(PROTOCOL_HANDLER) && defined(__APPLE__)
 			case SDL_DROPFILE:
@@ -1254,13 +1240,6 @@
 {
 	qboolean loading;
 
-	//FIXME test, checking mouse grab
-#if 0
-	if (in_checkForStolenMouseFocus->integer  &&  mouseActive  &&  !(SDL_GetAppState() & SDL_APPMOUSEFOCUS)) {
-		Com_Printf("^3external application stole mouse focus\n");
-	}
-#endif
-
 	IN_JoyMove( );
 
 	// If not DISCONNECTED (main menu) or ACTIVE (in game), we're loading
@@ -1282,16 +1261,10 @@
 	else if( !( SDL_GetWindowFlags( SDL_window ) & SDL_WINDOW_INPUT_FOCUS ) )
 	{
 		// Window not got focus
-		//Com_Printf("^3window lost focus\n");
 		IN_DeactivateMouse( cls.glconfig.isFullscreen );
 	}
-	else {
-		if (in_nograb->integer) {
-			IN_DeactivateMouse( cls.glconfig.isFullscreen );
-		} else {
-			IN_ActivateMouse( cls.glconfig.isFullscreen );
-		}
-	}
+	else
+		IN_ActivateMouse( cls.glconfig.isFullscreen );
 
 	IN_ProcessEvents( );
 
@@ -1330,13 +1303,10 @@
 	// mouse variables
 	in_mouse = Cvar_Get( "in_mouse", "1", CVAR_ARCHIVE );
 	in_nograb = Cvar_Get( "in_nograb", "0", CVAR_ARCHIVE );
-	in_checkForStolenMouseFocus = Cvar_Get("in_checkForStolenMouseFocus", "0", CVAR_ARCHIVE);
 
 	in_joystick = Cvar_Get( "in_joystick", "0", CVAR_ARCHIVE|CVAR_LATCH );
 	in_joystickThreshold = Cvar_Get( "joy_threshold", "0.15", CVAR_ARCHIVE );
 
-	//SDL_EnableUNICODE( 1 );
-
 #if defined(PROTOCOL_HANDLER) && defined(__APPLE__)
 	SDL_EventState( SDL_DROPFILE, SDL_ENABLE );
 #endif
@@ -1347,7 +1317,7 @@
 	IN_DeactivateMouse( Cvar_VariableIntegerValue( "r_fullscreen" ) != 0 );
 
 	appState = SDL_GetWindowFlags( SDL_window );
-	Cvar_SetValue( "com_unfocused", !( appState & SDL_WINDOW_INPUT_FOCUS ) );
+	Cvar_SetValue( "com_unfocused",	!( appState & SDL_WINDOW_INPUT_FOCUS ) );
 	Cvar_SetValue( "com_minimized", appState & SDL_WINDOW_MINIMIZED );
 
 	IN_InitJoystick( );

```

### `quake3e`  — sha256 `ba8049ac7f4f...`, 42696 bytes

_Diff stat: +415 / -311 lines_

_(full diff is 36367 bytes — see files directly)_

### `openarena-engine`  — sha256 `8e8a25d47ba0...`, 40303 bytes

_Diff stat: +584 / -548 lines_

_(full diff is 54861 bytes — see files directly)_
