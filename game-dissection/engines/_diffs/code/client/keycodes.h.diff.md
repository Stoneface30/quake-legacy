# Diff: `code/client/keycodes.h`
**Canonical:** `wolfcamql-src` (sha256 `bd4b0925b272...`, 5431 bytes)
Also identical in: ioquake3

## Variants

### `quake3e`  — sha256 `80299384f174...`, 4890 bytes

_Diff stat: +44 / -97 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\keycodes.h	2026-04-16 20:02:25.174724100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3e\code\client\keycodes.h	2026-04-16 20:02:26.914504200 +0100
@@ -35,6 +35,47 @@
 	K_ESCAPE = 27,
 	K_SPACE = 32,
 
+	K_QUOTE = '\'',
+	K_PLUS = '+',
+	K_COMMA = ',',
+	K_MINUS = '-',
+	K_DOT = '.',
+	K_SLASH = '/',
+	K_SEMICOLON = ';',
+	K_EQUAL = '=',
+	K_BACKSLASH = '\\',
+	K_UNDERSCORE = '_',
+	K_BRACKET_OPEN = '[',
+	K_BRACKET_CLOSE = ']',
+
+	K_A = 'a',
+	K_B = 'b',
+	K_C = 'c',
+	K_D = 'd',
+	K_E = 'e',
+	K_F = 'f',
+	K_G = 'g',
+	K_H = 'h',
+	K_I = 'i',
+	K_J = 'j',
+	K_K = 'k',
+	K_L = 'l',
+	K_M = 'm',
+	K_N = 'n',
+	K_O = 'o',
+	K_P = 'p',
+	K_Q = 'q',
+	K_R = 'r',
+	K_S = 's',
+	K_T = 't',
+	K_U = 'u',
+	K_V = 'v',
+	K_W = 'w',
+	K_X = 'x',
+	K_Y = 'y',
+	K_Z = 'z',
+
+	// following definitions must not be changed
 	K_BACKSPACE = 127,
 
 	K_COMMAND = 128,
@@ -150,103 +191,7 @@
 	K_AUX14,
 	K_AUX15,
 	K_AUX16,
-
-	K_WORLD_0,
-	K_WORLD_1,
-	K_WORLD_2,
-	K_WORLD_3,
-	K_WORLD_4,
-	K_WORLD_5,
-	K_WORLD_6,
-	K_WORLD_7,
-	K_WORLD_8,
-	K_WORLD_9,
-	K_WORLD_10,
-	K_WORLD_11,
-	K_WORLD_12,
-	K_WORLD_13,
-	K_WORLD_14,
-	K_WORLD_15,
-	K_WORLD_16,
-	K_WORLD_17,
-	K_WORLD_18,
-	K_WORLD_19,
-	K_WORLD_20,
-	K_WORLD_21,
-	K_WORLD_22,
-	K_WORLD_23,
-	K_WORLD_24,
-	K_WORLD_25,
-	K_WORLD_26,
-	K_WORLD_27,
-	K_WORLD_28,
-	K_WORLD_29,
-	K_WORLD_30,
-	K_WORLD_31,
-	K_WORLD_32,
-	K_WORLD_33,
-	K_WORLD_34,
-	K_WORLD_35,
-	K_WORLD_36,
-	K_WORLD_37,
-	K_WORLD_38,
-	K_WORLD_39,
-	K_WORLD_40,
-	K_WORLD_41,
-	K_WORLD_42,
-	K_WORLD_43,
-	K_WORLD_44,
-	K_WORLD_45,
-	K_WORLD_46,
-	K_WORLD_47,
-	K_WORLD_48,
-	K_WORLD_49,
-	K_WORLD_50,
-	K_WORLD_51,
-	K_WORLD_52,
-	K_WORLD_53,
-	K_WORLD_54,
-	K_WORLD_55,
-	K_WORLD_56,
-	K_WORLD_57,
-	K_WORLD_58,
-	K_WORLD_59,
-	K_WORLD_60,
-	K_WORLD_61,
-	K_WORLD_62,
-	K_WORLD_63,
-	K_WORLD_64,
-	K_WORLD_65,
-	K_WORLD_66,
-	K_WORLD_67,
-	K_WORLD_68,
-	K_WORLD_69,
-	K_WORLD_70,
-	K_WORLD_71,
-	K_WORLD_72,
-	K_WORLD_73,
-	K_WORLD_74,
-	K_WORLD_75,
-	K_WORLD_76,
-	K_WORLD_77,
-	K_WORLD_78,
-	K_WORLD_79,
-	K_WORLD_80,
-	K_WORLD_81,
-	K_WORLD_82,
-	K_WORLD_83,
-	K_WORLD_84,
-	K_WORLD_85,
-	K_WORLD_86,
-	K_WORLD_87,
-	K_WORLD_88,
-	K_WORLD_89,
-	K_WORLD_90,
-	K_WORLD_91,
-	K_WORLD_92,
-	K_WORLD_93,
-	K_WORLD_94,
-	K_WORLD_95,
+	// end of compatibility list
 
 	K_SUPER,
 	K_COMPOSE,
@@ -261,6 +206,8 @@
 	K_UNDO,
 
 	// Gamepad controls
+	// Ordered to match SDL2 game controller buttons and axes
+	// Do not change this order without also changing IN_GamepadMove() in SDL_input.c
 	K_PAD0_A,
 	K_PAD0_B,
 	K_PAD0_X,

```

### `openarena-engine`  — sha256 `4a04f885a2e1...`, 4507 bytes

_Diff stat: +0 / -35 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\keycodes.h	2026-04-16 20:02:25.174724100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\keycodes.h	2026-04-16 22:48:25.733378900 +0100
@@ -260,41 +260,6 @@
 	K_EURO,
 	K_UNDO,
 
-	// Gamepad controls
-	K_PAD0_A,
-	K_PAD0_B,
-	K_PAD0_X,
-	K_PAD0_Y,
-	K_PAD0_BACK,
-	K_PAD0_GUIDE,
-	K_PAD0_START,
-	K_PAD0_LEFTSTICK_CLICK,
-	K_PAD0_RIGHTSTICK_CLICK,
-	K_PAD0_LEFTSHOULDER,
-	K_PAD0_RIGHTSHOULDER,
-	K_PAD0_DPAD_UP,
-	K_PAD0_DPAD_DOWN,
-	K_PAD0_DPAD_LEFT,
-	K_PAD0_DPAD_RIGHT,
-
-	K_PAD0_LEFTSTICK_LEFT,
-	K_PAD0_LEFTSTICK_RIGHT,
-	K_PAD0_LEFTSTICK_UP,
-	K_PAD0_LEFTSTICK_DOWN,
-	K_PAD0_RIGHTSTICK_LEFT,
-	K_PAD0_RIGHTSTICK_RIGHT,
-	K_PAD0_RIGHTSTICK_UP,
-	K_PAD0_RIGHTSTICK_DOWN,
-	K_PAD0_LEFTTRIGGER,
-	K_PAD0_RIGHTTRIGGER,
-
-	K_PAD0_MISC1,    /* Xbox Series X share button, PS5 microphone button, Nintendo Switch Pro capture button, Amazon Luna microphone button */
-	K_PAD0_PADDLE1,  /* Xbox Elite paddle P1 */
-	K_PAD0_PADDLE2,  /* Xbox Elite paddle P3 */
-	K_PAD0_PADDLE3,  /* Xbox Elite paddle P2 */
-	K_PAD0_PADDLE4,  /* Xbox Elite paddle P4 */
-	K_PAD0_TOUCHPAD, /* PS4/PS5 touchpad button */
-
 	// Pseudo-key that brings the console down
 	K_CONSOLE,
 

```

### `openarena-gamecode`  — sha256 `66953ecd011a...`, 4562 bytes

_Diff stat: +8 / -46 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\keycodes.h	2026-04-16 20:02:25.174724100 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-gamecode\code\client\keycodes.h	2026-04-16 22:48:24.156330900 +0100
@@ -101,10 +101,10 @@
 	K_MWHEELDOWN,
 	K_MWHEELUP,
 
-	K_JOY1,
-	K_JOY2,
-	K_JOY3,
-	K_JOY4,
+	K_JOY1,		// BUTTON X
+	K_JOY2,		// BUTTON O
+	K_JOY3,		// BUTTON SQUARE
+	K_JOY4,		// BUTTON TRIANGLE
 	K_JOY5,
 	K_JOY6,
 	K_JOY7,
@@ -129,10 +129,10 @@
 	K_JOY26,
 	K_JOY27,
 	K_JOY28,
-	K_JOY29,
-	K_JOY30,
-	K_JOY31,
-	K_JOY32,
+	K_JOY29,	// DPAD UP
+	K_JOY30,	// DPAD RIGHT
+	K_JOY31,	// DPAD DOWN
+	K_JOY32,	// DPAD LEFT
 
 	K_AUX1,
 	K_AUX2,
@@ -260,44 +260,6 @@
 	K_EURO,
 	K_UNDO,
 
-	// Gamepad controls
-	K_PAD0_A,
-	K_PAD0_B,
-	K_PAD0_X,
-	K_PAD0_Y,
-	K_PAD0_BACK,
-	K_PAD0_GUIDE,
-	K_PAD0_START,
-	K_PAD0_LEFTSTICK_CLICK,
-	K_PAD0_RIGHTSTICK_CLICK,
-	K_PAD0_LEFTSHOULDER,
-	K_PAD0_RIGHTSHOULDER,
-	K_PAD0_DPAD_UP,
-	K_PAD0_DPAD_DOWN,
-	K_PAD0_DPAD_LEFT,
-	K_PAD0_DPAD_RIGHT,
-
-	K_PAD0_LEFTSTICK_LEFT,
-	K_PAD0_LEFTSTICK_RIGHT,
-	K_PAD0_LEFTSTICK_UP,
-	K_PAD0_LEFTSTICK_DOWN,
-	K_PAD0_RIGHTSTICK_LEFT,
-	K_PAD0_RIGHTSTICK_RIGHT,
-	K_PAD0_RIGHTSTICK_UP,
-	K_PAD0_RIGHTSTICK_DOWN,
-	K_PAD0_LEFTTRIGGER,
-	K_PAD0_RIGHTTRIGGER,
-
-	K_PAD0_MISC1,    /* Xbox Series X share button, PS5 microphone button, Nintendo Switch Pro capture button, Amazon Luna microphone button */
-	K_PAD0_PADDLE1,  /* Xbox Elite paddle P1 */
-	K_PAD0_PADDLE2,  /* Xbox Elite paddle P3 */
-	K_PAD0_PADDLE3,  /* Xbox Elite paddle P2 */
-	K_PAD0_PADDLE4,  /* Xbox Elite paddle P4 */
-	K_PAD0_TOUCHPAD, /* PS4/PS5 touchpad button */
-
-	// Pseudo-key that brings the console down
-	K_CONSOLE,
-
 	MAX_KEYS
 } keyNum_t;
 

```
