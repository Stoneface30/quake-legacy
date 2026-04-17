# Diff: `code/q3_ui/ui_controls2.c`
**Canonical:** `wolfcamql-src` (sha256 `b108d064ae80...`, 54379 bytes)

## Variants

### `quake3-source`  — sha256 `2c7115ec845b...`, 53979 bytes

_Diff stat: +30 / -31 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_controls2.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_controls2.c	2026-04-16 20:02:19.944820100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -111,17 +111,16 @@
 #define ID_CHAT2		31
 #define ID_CHAT3		32
 #define ID_CHAT4		33
-#define ID_TOGGLEMENU	34
 
 // all others
-#define ID_FREELOOK		35
-#define ID_INVERTMOUSE	36
-#define ID_ALWAYSRUN	37
-#define ID_AUTOSWITCH	38
-#define ID_MOUSESPEED	39
-#define ID_JOYENABLE	40
-#define ID_JOYTHRESHOLD	41
-#define ID_SMOOTHMOUSE	42
+#define ID_FREELOOK		34
+#define ID_INVERTMOUSE	35
+#define ID_ALWAYSRUN	36
+#define ID_AUTOSWITCH	37
+#define ID_MOUSESPEED	38
+#define ID_JOYENABLE	39
+#define ID_JOYTHRESHOLD	40
+#define ID_SMOOTHMOUSE	41
 
 #define ANIM_IDLE		0
 #define ANIM_RUN		1
@@ -206,7 +205,6 @@
 	menuaction_s		chat2;
 	menuaction_s		chat3;
 	menuaction_s		chat4;
-	menuaction_s		togglemenu;
 	menuradiobutton_s	joyenable;
 	menuslider_s		joythreshold;
 	int					section;
@@ -216,7 +214,7 @@
 	vec3_t				playerMoveangles;
 	int					playerLegs;
 	int					playerTorso;
-	weapon_t			playerWeapon;
+	int					playerWeapon;
 	qboolean			playerChat;
 
 	menubitmap_s		back;
@@ -225,7 +223,7 @@
 
 static controls_t s_controls;
 
-static vec4_t controls_binding_color  = {1.00f, 0.43f, 0.00f, 1.00f};
+static vec4_t controls_binding_color  = {1.00f, 0.43f, 0.00f, 1.00f}; // bk: Win32 C4305
 
 static bind_t g_bindings[] = 
 {
@@ -263,7 +261,6 @@
 	{"messagemode2", 	"chat - team",		ID_CHAT2,		ANIM_CHAT,		-1,				-1,		-1, -1},
 	{"messagemode3", 	"chat - target",	ID_CHAT3,		ANIM_CHAT,		-1,				-1,		-1, -1},
 	{"messagemode4", 	"chat - attacker",	ID_CHAT4,		ANIM_CHAT,		-1,				-1,		-1, -1},
-	{"togglemenu", 		"toggle menu",		ID_TOGGLEMENU,	ANIM_IDLE,		K_ESCAPE,				-1,		-1,	-1},
 	{(char*)NULL,		(char*)NULL,		0,				0,				-1,				-1,		-1,	-1},
 };
 
@@ -336,7 +333,6 @@
 	(menucommon_s *)&s_controls.chat2,
 	(menucommon_s *)&s_controls.chat3,
 	(menucommon_s *)&s_controls.chat4,
-	(menucommon_s *)&s_controls.togglemenu,
 	NULL,
 };
 
@@ -354,10 +350,11 @@
 */
 static void Controls_InitCvars( void )
 {
+	int				i;
 	configcvar_t*	cvarptr;
 
 	cvarptr = g_configcvars;
-	for (;;cvarptr++)
+	for (i=0; ;i++,cvarptr++)
 	{
 		if (!cvarptr->name)
 			break;
@@ -382,9 +379,10 @@
 static float Controls_GetCvarDefault( char* name )
 {
 	configcvar_t*	cvarptr;
+	int				i;
 
 	cvarptr = g_configcvars;
-	for (;;cvarptr++)
+	for (i=0; ;i++,cvarptr++)
 	{
 		if (!cvarptr->name)
 			return (0);
@@ -404,9 +402,10 @@
 static float Controls_GetCvarValue( char* name )
 {
 	configcvar_t*	cvarptr;
+	int				i;
 
 	cvarptr = g_configcvars;
-	for (;;cvarptr++)
+	for (i=0; ;i++,cvarptr++)
 	{
 		if (!cvarptr->name)
 			return (0);
@@ -431,7 +430,7 @@
 	s_controls.playerMoveangles[YAW] = s_controls.playerViewangles[YAW];
 	s_controls.playerLegs		     = LEGS_IDLE;
 	s_controls.playerTorso			 = TORSO_STAND;
-	s_controls.playerWeapon			 = WP_NUM_WEAPONS;
+	s_controls.playerWeapon			 = -1;
 	s_controls.playerChat			 = qfalse;
 
 	switch( anim ) {
@@ -562,6 +561,7 @@
 	// disable all controls in all groups
 	for( i = 0; i < C_MAX; i++ ) {
 		controls = g_controls[i];
+		// bk001204 - parentheses
 		for( j = 0;  (control = controls[j]) ; j++ ) {
 			control->flags |= (QMF_HIDDEN|QMF_INACTIVE);
 		}
@@ -570,12 +570,14 @@
 	controls = g_controls[s_controls.section];
 
 	// enable controls in active group (and count number of items for vertical centering)
+	// bk001204 - parentheses
 	for( j = 0;  (control = controls[j]) ; j++ ) {
 		control->flags &= ~(QMF_GRAYED|QMF_HIDDEN|QMF_INACTIVE);
 	}
 
 	// position controls
 	y = ( SCREEN_HEIGHT - j * SMALLCHAR_HEIGHT ) / 2;
+	// bk001204 - parentheses
 	for( j = 0;	(control = controls[j]) ; j++, y += SMALLCHAR_HEIGHT ) {
 		control->x      = 320;
 		control->y      = y;
@@ -785,6 +787,7 @@
 */
 static void Controls_GetConfig( void )
 {
+	int		i;
 	int		twokeys[2];
 	bind_t*	bindptr;
 
@@ -792,7 +795,7 @@
 	bindptr = g_bindings;
 
 	// iterate each command, get its numeric binding
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)
 			break;
@@ -820,13 +823,14 @@
 */
 static void Controls_SetConfig( void )
 {
+	int		i;
 	bind_t*	bindptr;
 
 	// set the bindings from the local store
 	bindptr = g_bindings;
 
 	// iterate each command, get its numeric binding
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)
 			break;
@@ -862,13 +866,14 @@
 */
 static void Controls_SetDefaults( void )
 {
+	int	i;
 	bind_t*	bindptr;
 
 	// set the bindings from the local store
 	bindptr = g_bindings;
 
 	// iterate each command, set its default binding
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)
 			break;
@@ -895,6 +900,7 @@
 static sfxHandle_t Controls_MenuKey( int key )
 {
 	int			id;
+	int			i;
 	qboolean	found;
 	bind_t*		bindptr;
 	found = qfalse;
@@ -942,7 +948,7 @@
 	{
 		// remove from any other bind
 		bindptr = g_bindings;
-		for (;;bindptr++)
+		for (i=0; ;i++,bindptr++)
 		{
 			if (!bindptr->label)	
 				break;
@@ -961,7 +967,7 @@
 	// assign key to local store
 	id      = ((menucommon_s*)(s_controls.menu.items[s_controls.menu.cursor]))->id;
 	bindptr = g_bindings;
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)	
 			break;
@@ -1529,12 +1535,6 @@
 	s_controls.chat4.generic.ownerdraw = Controls_DrawKeyBinding;
 	s_controls.chat4.generic.id        = ID_CHAT4;
 
-	s_controls.togglemenu.generic.type              = MTYPE_ACTION;
-	s_controls.togglemenu.generic.flags     = QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_GRAYED|QMF_HIDDEN;
-	s_controls.togglemenu.generic.callback  = Controls_ActionEvent;
-	s_controls.togglemenu.generic.ownerdraw = Controls_DrawKeyBinding;
-	s_controls.togglemenu.generic.id        = ID_TOGGLEMENU;
-
 	s_controls.joyenable.generic.type      = MTYPE_RADIOBUTTON;
 	s_controls.joyenable.generic.flags	   = QMF_SMALLFONT;
 	s_controls.joyenable.generic.x	       = SCREEN_WIDTH/2;
@@ -1617,7 +1617,6 @@
 	Menu_AddItem( &s_controls.menu, &s_controls.chat2 );
 	Menu_AddItem( &s_controls.menu, &s_controls.chat3 );
 	Menu_AddItem( &s_controls.menu, &s_controls.chat4 );
-	Menu_AddItem( &s_controls.menu, &s_controls.togglemenu );
 
 	Menu_AddItem( &s_controls.menu, &s_controls.back );
 

```

### `ioquake3`  — sha256 `08ab2b66e7d1...`, 54365 bytes

_Diff stat: +2 / -2 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_controls2.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_controls2.c	2026-04-16 20:02:21.553432500 +0100
@@ -263,7 +263,7 @@
 	{"messagemode2", 	"chat - team",		ID_CHAT2,		ANIM_CHAT,		-1,				-1,		-1, -1},
 	{"messagemode3", 	"chat - target",	ID_CHAT3,		ANIM_CHAT,		-1,				-1,		-1, -1},
 	{"messagemode4", 	"chat - attacker",	ID_CHAT4,		ANIM_CHAT,		-1,				-1,		-1, -1},
-	{"togglemenu", 		"toggle menu",		ID_TOGGLEMENU,	ANIM_IDLE,		K_ESCAPE,				-1,		-1,	-1},
+	{"togglemenu", 		"toggle menu",		ID_TOGGLEMENU,	ANIM_IDLE,		K_ESCAPE,		-1,		-1, -1},
 	{(char*)NULL,		(char*)NULL,		0,				0,				-1,				-1,		-1,	-1},
 };
 
@@ -1529,7 +1529,7 @@
 	s_controls.chat4.generic.ownerdraw = Controls_DrawKeyBinding;
 	s_controls.chat4.generic.id        = ID_CHAT4;
 
-	s_controls.togglemenu.generic.type              = MTYPE_ACTION;
+	s_controls.togglemenu.generic.type		= MTYPE_ACTION;
 	s_controls.togglemenu.generic.flags     = QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_GRAYED|QMF_HIDDEN;
 	s_controls.togglemenu.generic.callback  = Controls_ActionEvent;
 	s_controls.togglemenu.generic.ownerdraw = Controls_DrawKeyBinding;

```

### `openarena-engine`  — sha256 `e79cca48e841...`, 54490 bytes

_Diff stat: +19 / -12 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_controls2.c	2026-04-16 20:02:25.205500000 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_controls2.c	2026-04-16 22:48:25.893195200 +0100
@@ -216,7 +216,7 @@
 	vec3_t				playerMoveangles;
 	int					playerLegs;
 	int					playerTorso;
-	weapon_t			playerWeapon;
+	int					playerWeapon;
 	qboolean			playerChat;
 
 	menubitmap_s		back;
@@ -263,7 +263,7 @@
 	{"messagemode2", 	"chat - team",		ID_CHAT2,		ANIM_CHAT,		-1,				-1,		-1, -1},
 	{"messagemode3", 	"chat - target",	ID_CHAT3,		ANIM_CHAT,		-1,				-1,		-1, -1},
 	{"messagemode4", 	"chat - attacker",	ID_CHAT4,		ANIM_CHAT,		-1,				-1,		-1, -1},
-	{"togglemenu", 		"toggle menu",		ID_TOGGLEMENU,	ANIM_IDLE,		K_ESCAPE,				-1,		-1,	-1},
+	{"togglemenu", 		"toggle menu",		ID_TOGGLEMENU,	ANIM_IDLE,		K_ESCAPE,		-1,		-1, -1},
 	{(char*)NULL,		(char*)NULL,		0,				0,				-1,				-1,		-1,	-1},
 };
 
@@ -354,10 +354,11 @@
 */
 static void Controls_InitCvars( void )
 {
+	int				i;
 	configcvar_t*	cvarptr;
 
 	cvarptr = g_configcvars;
-	for (;;cvarptr++)
+	for (i=0; ;i++,cvarptr++)
 	{
 		if (!cvarptr->name)
 			break;
@@ -382,9 +383,10 @@
 static float Controls_GetCvarDefault( char* name )
 {
 	configcvar_t*	cvarptr;
+	int				i;
 
 	cvarptr = g_configcvars;
-	for (;;cvarptr++)
+	for (i=0; ;i++,cvarptr++)
 	{
 		if (!cvarptr->name)
 			return (0);
@@ -404,9 +406,10 @@
 static float Controls_GetCvarValue( char* name )
 {
 	configcvar_t*	cvarptr;
+	int				i;
 
 	cvarptr = g_configcvars;
-	for (;;cvarptr++)
+	for (i=0; ;i++,cvarptr++)
 	{
 		if (!cvarptr->name)
 			return (0);
@@ -431,7 +434,7 @@
 	s_controls.playerMoveangles[YAW] = s_controls.playerViewangles[YAW];
 	s_controls.playerLegs		     = LEGS_IDLE;
 	s_controls.playerTorso			 = TORSO_STAND;
-	s_controls.playerWeapon			 = WP_NUM_WEAPONS;
+	s_controls.playerWeapon			 = -1;
 	s_controls.playerChat			 = qfalse;
 
 	switch( anim ) {
@@ -785,6 +788,7 @@
 */
 static void Controls_GetConfig( void )
 {
+	int		i;
 	int		twokeys[2];
 	bind_t*	bindptr;
 
@@ -792,7 +796,7 @@
 	bindptr = g_bindings;
 
 	// iterate each command, get its numeric binding
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)
 			break;
@@ -820,13 +824,14 @@
 */
 static void Controls_SetConfig( void )
 {
+	int		i;
 	bind_t*	bindptr;
 
 	// set the bindings from the local store
 	bindptr = g_bindings;
 
 	// iterate each command, get its numeric binding
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)
 			break;
@@ -862,13 +867,14 @@
 */
 static void Controls_SetDefaults( void )
 {
+	int	i;
 	bind_t*	bindptr;
 
 	// set the bindings from the local store
 	bindptr = g_bindings;
 
 	// iterate each command, set its default binding
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)
 			break;
@@ -895,6 +901,7 @@
 static sfxHandle_t Controls_MenuKey( int key )
 {
 	int			id;
+	int			i;
 	qboolean	found;
 	bind_t*		bindptr;
 	found = qfalse;
@@ -942,7 +949,7 @@
 	{
 		// remove from any other bind
 		bindptr = g_bindings;
-		for (;;bindptr++)
+		for (i=0; ;i++,bindptr++)
 		{
 			if (!bindptr->label)	
 				break;
@@ -961,7 +968,7 @@
 	// assign key to local store
 	id      = ((menucommon_s*)(s_controls.menu.items[s_controls.menu.cursor]))->id;
 	bindptr = g_bindings;
-	for (;;bindptr++)
+	for (i=0; ;i++,bindptr++)
 	{
 		if (!bindptr->label)	
 			break;
@@ -1529,7 +1536,7 @@
 	s_controls.chat4.generic.ownerdraw = Controls_DrawKeyBinding;
 	s_controls.chat4.generic.id        = ID_CHAT4;
 
-	s_controls.togglemenu.generic.type              = MTYPE_ACTION;
+	s_controls.togglemenu.generic.type		= MTYPE_ACTION;
 	s_controls.togglemenu.generic.flags     = QMF_LEFT_JUSTIFY|QMF_PULSEIFFOCUS|QMF_GRAYED|QMF_HIDDEN;
 	s_controls.togglemenu.generic.callback  = Controls_ActionEvent;
 	s_controls.togglemenu.generic.ownerdraw = Controls_DrawKeyBinding;

```

### `openarena-gamecode`  — sha256 `5679c5579090...`, 58826 bytes

_Diff stat: +255 / -155 lines_

_(full diff is 30999 bytes — see files directly)_
