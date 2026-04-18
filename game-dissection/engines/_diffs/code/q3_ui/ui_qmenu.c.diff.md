# Diff: `code/q3_ui/ui_qmenu.c`
**Canonical:** `wolfcamql-src` (sha256 `843e21345a00...`, 39758 bytes)

## Variants

### `quake3-source`  — sha256 `7b84e0744d74...`, 37751 bytes

_Diff stat: +81 / -142 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_qmenu.c	2026-04-16 20:02:25.210502700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\q3_ui\ui_qmenu.c	2026-04-16 20:02:19.950618100 +0100
@@ -15,7 +15,7 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
@@ -55,7 +55,7 @@
 vec4_t text_color_normal    = {1.00f, 0.43f, 0.00f, 1.00f};	// light orange
 vec4_t text_color_highlight = {1.00f, 1.00f, 0.00f, 1.00f};	// bright yellow
 vec4_t listbar_color        = {1.00f, 0.43f, 0.00f, 0.30f};	// transluscent orange
-vec4_t text_color_status    = {1.00f, 1.00f, 1.00f, 1.00f};	// bright white
+vec4_t text_color_status    = {1.00f, 1.00f, 1.00f, 1.00f};	// bright white	
 
 // action widget
 static void	Action_Init( menuaction_s *a );
@@ -81,7 +81,7 @@
 static void Text_Draw( menutext_s *b );
 
 // scrolllist widget
-void	ScrollList_Init( menulist_s *l );
+static void	ScrollList_Init( menulist_s *l );
 sfxHandle_t ScrollList_Key( menulist_s *l, int key );
 
 // proportional text widget
@@ -111,7 +111,7 @@
 {
 	int		x;
 	int		y;
-	char	buff[512];
+	char	buff[512];	
 	float*	color;
 
 	x = t->generic.x;
@@ -126,7 +126,7 @@
 	// possible value
 	if (t->string)
 		strcat(buff,t->string);
-
+		
 	if (t->generic.flags & QMF_GRAYED)
 		color = text_color_disabled;
 	else
@@ -327,16 +327,17 @@
 		if (b->shader)
 			UI_DrawHandlePic( x, y, w, h, b->shader );
 
-		if (  ( (b->generic.flags & QMF_PULSE)
+		// bk001204 - parentheses
+		if (  ( (b->generic.flags & QMF_PULSE) 
 			|| (b->generic.flags & QMF_PULSEIFFOCUS) )
 		      && (Menu_ItemAtCursor( b->generic.parent ) == b))
-		{
-			if (b->focuscolor)
+		{	
+			if (b->focuscolor)			
 			{
 				tempcolor[0] = b->focuscolor[0];
 				tempcolor[1] = b->focuscolor[1];
 				tempcolor[2] = b->focuscolor[2];
-				color        = tempcolor;
+				color        = tempcolor;	
 			}
 			else
 				color = pulse_color;
@@ -347,7 +348,7 @@
 			trap_R_SetColor( NULL );
 		}
 		else if ((b->generic.flags & QMF_HIGHLIGHT) || ((b->generic.flags & QMF_HIGHLIGHT_IF_FOCUS) && (Menu_ItemAtCursor( b->generic.parent ) == b)))
-		{
+		{	
 			if (b->focuscolor)
 			{
 				trap_R_SetColor( b->focuscolor );
@@ -376,7 +377,7 @@
 		len = 0;
 
 	// left justify text
-	a->generic.left   = a->generic.x;
+	a->generic.left   = a->generic.x; 
 	a->generic.right  = a->generic.x + len*BIGCHAR_WIDTH;
 	a->generic.top    = a->generic.y;
 	a->generic.bottom = a->generic.y + BIGCHAR_HEIGHT;
@@ -518,7 +519,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( rb->generic.left, rb->generic.top, rb->generic.right-rb->generic.left+1, rb->generic.bottom-rb->generic.top+1, listbar_color );
+		UI_FillRect( rb->generic.left, rb->generic.top, rb->generic.right-rb->generic.left+1, rb->generic.bottom-rb->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -552,7 +553,7 @@
 	else
 		len = 0;
 
-	s->generic.left   = s->generic.x - (len+1)*SMALLCHAR_WIDTH;
+	s->generic.left   = s->generic.x - (len+1)*SMALLCHAR_WIDTH; 
 	s->generic.right  = s->generic.x + (SLIDER_RANGE+2+1)*SMALLCHAR_WIDTH;
 	s->generic.top    = s->generic.y;
 	s->generic.bottom = s->generic.y + SMALLCHAR_HEIGHT;
@@ -595,7 +596,7 @@
 			}
 			else
 				sound = menu_buzz_sound;
-			break;
+			break;			
 
 		case K_KP_RIGHTARROW:
 		case K_RIGHTARROW:
@@ -606,7 +607,7 @@
 			}
 			else
 				sound = menu_buzz_sound;
-			break;
+			break;			
 
 		default:
 			// key not handled
@@ -633,7 +634,7 @@
 	float		*color;
 	int			button;
 	qboolean	focus;
-
+	
 	x =	s->generic.x;
 	y = s->generic.y;
 	focus = (s->generic.parent->cursor == s->generic.menuPosition);
@@ -697,7 +698,7 @@
 	int x;
 	int y;
 	qboolean focus;
-
+	
 	x =	s->generic.x;
 	y = s->generic.y;
 	focus = (s->generic.parent->cursor == s->generic.menuPosition);
@@ -720,7 +721,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color );
+		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -779,7 +780,7 @@
 			len = l;
 
 		s->numitems++;
-	}
+	}		
 
 	s->generic.top	  =	s->generic.y;
 	s->generic.right  =	s->generic.x + (len+1)*SMALLCHAR_WIDTH;
@@ -798,21 +799,33 @@
 	sound = 0;
 	switch (key)
 	{
-	    case K_KP_RIGHTARROW:
-	    case K_RIGHTARROW:
 		case K_MOUSE1:
 			s->curvalue++;
 			if (s->curvalue >= s->numitems)
 				s->curvalue = 0;
 			sound = menu_move_sound;
 			break;
-
+		
 		case K_KP_LEFTARROW:
 		case K_LEFTARROW:
-			s->curvalue--;
-			if (s->curvalue < 0)
-				s->curvalue = s->numitems-1;
-			sound = menu_move_sound;
+			if (s->curvalue > 0)
+			{
+				s->curvalue--;
+				sound = menu_move_sound;
+			}
+			else
+				sound = menu_buzz_sound;
+			break;
+
+		case K_KP_RIGHTARROW:
+		case K_RIGHTARROW:
+			if (s->curvalue < s->numitems-1)
+			{
+				s->curvalue++;
+				sound = menu_move_sound;
+			}
+			else
+				sound = menu_buzz_sound;
 			break;
 	}
 
@@ -858,7 +871,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color );
+		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -871,7 +884,7 @@
 ScrollList_Init
 =================
 */
-void ScrollList_Init( menulist_s *l )
+static void ScrollList_Init( menulist_s *l )
 {
 	int		w;
 
@@ -881,16 +894,16 @@
 
 	if( !l->columns ) {
 		l->columns = 1;
-		l->separation = 0;
+		l->seperation = 0;
 	}
-	else if( !l->separation ) {
-		l->separation = 3;
+	else if( !l->seperation ) {
+		l->seperation = 3;
 	}
 
-	w = ( (l->width + l->separation) * l->columns - l->separation) * SMALLCHAR_WIDTH;
+	w = ( (l->width + l->seperation) * l->columns - l->seperation) * SMALLCHAR_WIDTH;
 
 	l->generic.left   =	l->generic.x;
-	l->generic.top    = l->generic.y;
+	l->generic.top    = l->generic.y;	
 	l->generic.right  =	l->generic.x + w;
 	l->generic.bottom =	l->generic.y + l->height * SMALLCHAR_HEIGHT;
 
@@ -911,38 +924,29 @@
 	int	y;
 	int	w;
 	int	i;
-	int	j;
+	int	j;	
 	int	c;
 	int	cursorx;
 	int	cursory;
 	int	column;
 	int	index;
-	static int clickTime = 0;
-	qboolean doubleClicked;
 
 	switch (key)
 	{
-        case K_MOUSE1:
-			if (trap_Milliseconds() - clickTime < ui_doubleClickTime.integer) {
-				clickTime = 0;
-				doubleClicked = qtrue;
-			} else {
-				clickTime = trap_Milliseconds();
-				doubleClicked = qfalse;
-			}
+		case K_MOUSE1:
 			if (l->generic.flags & QMF_HASMOUSEFOCUS)
 			{
 				// check scroll region
 				x = l->generic.x;
 				y = l->generic.y;
-				w = ( (l->width + l->separation) * l->columns - l->separation) * SMALLCHAR_WIDTH;
+				w = ( (l->width + l->seperation) * l->columns - l->seperation) * SMALLCHAR_WIDTH;
 				if( l->generic.flags & QMF_CENTER_JUSTIFY ) {
 					x -= w / 2;
 				}
 				if (UI_CursorInRect( x, y, w, l->height*SMALLCHAR_HEIGHT ))
 				{
 					cursorx = (uis.cursorx - x)/SMALLCHAR_WIDTH;
-					column = cursorx / (l->width + l->separation);
+					column = cursorx / (l->width + l->seperation);
 					cursory = (uis.cursory - y)/SMALLCHAR_HEIGHT;
 					index = column * l->height + cursory;
 					if (l->top + index < l->numitems)
@@ -955,20 +959,12 @@
 							l->generic.callback( l, QM_GOTFOCUS );
 							return (menu_move_sound);
 						}
-
 					}
-
-
 				}
-
-				if (doubleClicked  &&  l->generic.callback) {
-					l->generic.callback(l, QM_DOUBLECLICKED);
-				}
-
+			
 				// absorbed, silent sound effect
 				return (menu_null_sound);
 			}
-
 			break;
 
 		case K_KP_HOME:
@@ -996,7 +992,7 @@
 				l->top = l->curvalue - (l->height - 1);
 			}
 			if (l->top < 0)
-				l->top = 0;
+				l->top = 0;			
 
 			if (l->oldvalue != l->curvalue && l->generic.callback)
 			{
@@ -1051,7 +1047,6 @@
 			}
 			return (menu_buzz_sound);
 
-	case K_MWHEELUP:
 		case K_KP_UPARROW:
 		case K_UPARROW:
 			if( l->curvalue == 0 ) {
@@ -1076,7 +1071,6 @@
 
 			return (menu_move_sound);
 
-	case K_MWHEELDOWN:
 		case K_KP_DOWNARROW:
 		case K_DOWNARROW:
 			if( l->curvalue == l->numitems - 1 ) {
@@ -1183,14 +1177,14 @@
 				// past end of list box, do page down
 				l->top = (j+1) - l->height;
 			}
-
+			
 			if (l->curvalue != j)
 			{
 				l->oldvalue = l->curvalue;
 				l->curvalue = j;
 				if (l->generic.callback)
 					l->generic.callback( l, QM_GOTFOCUS );
-				return ( menu_move_sound );
+				return ( menu_move_sound );			
 			}
 
 			return (menu_buzz_sound);
@@ -1216,7 +1210,6 @@
 	float*		color;
 	qboolean	hasfocus;
 	int			style;
-	int slen;
 
 	hasfocus = (l->generic.parent->cursor == l->generic.menuPosition);
 
@@ -1235,9 +1228,7 @@
 					u -= (l->width * SMALLCHAR_WIDTH) / 2 + 1;
 				}
 
-				//UI_FillRect(u,y,l->width*SMALLCHAR_WIDTH,SMALLCHAR_HEIGHT+2,listbar_color);
-				slen = strlen(l->itemnames[i]);
-				UI_FillRect(u, y, slen * SMALLCHAR_WIDTH + 4, SMALLCHAR_HEIGHT + 2, listbar_color);
+				UI_FillRect(u,y,l->width*SMALLCHAR_WIDTH,SMALLCHAR_HEIGHT+2,listbar_color);
 				color = text_color_highlight;
 
 				if (hasfocus)
@@ -1263,7 +1254,7 @@
 
 			y += SMALLCHAR_HEIGHT;
 		}
-		x += (l->width + l->separation) * SMALLCHAR_WIDTH;
+		x += (l->width + l->seperation) * SMALLCHAR_WIDTH;
 	}
 }
 
@@ -1346,18 +1337,17 @@
 void Menu_CursorMoved( menuframework_s *m )
 {
 	void (*callback)( void *self, int notification );
-
+	
 	if (m->cursor_prev == m->cursor)
 		return;
 
 	if (m->cursor_prev >= 0 && m->cursor_prev < m->nitems)
 	{
 		callback = ((menucommon_s*)(m->items[m->cursor_prev]))->callback;
-		if (callback) {
+		if (callback)
 			callback(m->items[m->cursor_prev],QM_LOSTFOCUS);
-		}
 	}
-
+	
 	if (m->cursor >= 0 && m->cursor < m->nitems)
 	{
 		callback = ((menucommon_s*)(m->items[m->cursor]))->callback;
@@ -1478,11 +1468,11 @@
 		{
 			// total subclassing, owner draws everything
 			itemptr->ownerdraw( itemptr );
-		}
-		else
+		}	
+		else 
 		{
 			switch (itemptr->type)
-			{
+			{	
 				case MTYPE_RADIOBUTTON:
 					RadioButton_Draw( (menuradiobutton_s*)itemptr );
 					break;
@@ -1490,19 +1480,19 @@
 				case MTYPE_FIELD:
 					MenuField_Draw( (menufield_s*)itemptr );
 					break;
-
+		
 				case MTYPE_SLIDER:
 					Slider_Draw( (menuslider_s*)itemptr );
 					break;
-
+ 
 				case MTYPE_SPINCONTROL:
 					SpinControl_Draw( (menulist_s*)itemptr );
 					break;
-
+		
 				case MTYPE_ACTION:
 					Action_Draw( (menuaction_s*)itemptr );
 					break;
-
+		
 				case MTYPE_BITMAP:
 					Bitmap_Draw( (menubitmap_s*)itemptr );
 					break;
@@ -1514,7 +1504,7 @@
 				case MTYPE_SCROLLLIST:
 					ScrollList_Draw( (menulist_s*)itemptr );
 					break;
-
+				
 				case MTYPE_PTEXT:
 					PText_Draw( (menutext_s*)itemptr );
 					break;
@@ -1527,7 +1517,7 @@
 					trap_Error( va("Menu_Draw: unknown type %d", itemptr->type) );
 			}
 		}
-#ifndef NQDEBUG
+#ifndef NDEBUG
 		if( uis.debug ) {
 			int	x;
 			int	y;
@@ -1564,7 +1554,7 @@
 void *Menu_ItemAtCursor( menuframework_s *m )
 {
 	if ( m->cursor < 0 || m->cursor >= m->nitems )
-		return NULL;
+		return 0;
 
 	return m->items[m->cursor];
 }
@@ -1595,12 +1585,11 @@
 	sfxHandle_t		sound = 0;
 	menucommon_s	*item;
 	int				cursor_prev;
-	char buf[MAX_STRING_CHARS];
 
 	// menu system keys
 	switch ( key )
 	{
-		//case K_MOUSE2:
+		case K_MOUSE2:
 		case K_ESCAPE:
 			UI_PopMenu();
 			return menu_out_sound;
@@ -1638,14 +1627,14 @@
 
 		if (sound) {
 			// key was handled
-			return sound;
+			return sound;		
 		}
 	}
 
 	// default handling
 	switch ( key )
 	{
-#if 0  //ndef NQDEBUG
+#ifndef NDEBUG
 		case K_F11:
 			uis.debug ^= 1;
 			break;
@@ -1654,7 +1643,6 @@
 			trap_Cmd_ExecuteText(EXEC_APPEND, "screenshot\n");
 			break;
 #endif
-	case K_MWHEELUP:
 		case K_KP_UPARROW:
 		case K_UPARROW:
 			cursor_prev    = m->cursor;
@@ -1667,7 +1655,6 @@
 			}
 			break;
 
-	case K_MWHEELDOWN:
 		case K_TAB:
 		case K_KP_DOWNARROW:
 		case K_DOWNARROW:
@@ -1710,20 +1697,9 @@
 		case K_AUX16:
 		case K_KP_ENTER:
 		case K_ENTER:
-			if (item) {
-				if (!(item->flags & (QMF_MOUSEONLY|QMF_GRAYED|QMF_INACTIVE))) {
+			if (item)
+				if (!(item->flags & (QMF_MOUSEONLY|QMF_GRAYED|QMF_INACTIVE)))
 					return (Menu_ActivateItem( m, item ));
-				} else {
-				}
-			}
-			break;
-	    default:
-			buf[0] = '\0';
-			trap_Key_GetBindingBuf(key, buf, sizeof(buf));
-			if (!*buf  ||  buf[0] == '+'  ||  buf[1] == '-'  ||  !Q_stricmpn(buf, "vstr", strlen("vstr") - 1)) {
-				break;
-			}
-			trap_Cmd_ExecuteText(EXEC_NOW, buf);
 			break;
 	}
 
@@ -1738,65 +1714,27 @@
 void Menu_Cache( void )
 {
 	uis.charset			= trap_R_RegisterShaderNoMip( "gfx/2d/bigchars" );
-
-	if (!uis.charset) {
-		uis.charset = trap_R_RegisterShaderNoMip("gfx/wc/openarenachars");
-		uis.charsetProp		= trap_R_RegisterShaderNoMip("gfx/wc/font1_prop.tga");
-		uis.charsetPropGlow	= trap_R_RegisterShaderNoMip("gfx/wc/font1_prop_glo.tga");
-		uis.charsetPropB	= trap_R_RegisterShaderNoMip("gfx/wc/font2_prop.tga");
-		//uis.charsetProp = uis.charset;
-		//uis.charsetPropGlow = uis.charset;
-		//uis.charsetPropB = uis.charset;
-		uis.showErrorMenu = qtrue;
-		//trap_Cvar_Set("com_errorMessage", "quakelive paks not found");
-		uis.cursor = trap_R_RegisterShaderNoMip("gfx/wc/3_cursor2");
-		uis.menuBackShader = uis.menuBackNoLogoShader = trap_R_RegisterShaderNoMip("gfx/wc/black.png");
-		return;
-	}
-
 	uis.charsetProp		= trap_R_RegisterShaderNoMip( "menu/art/font1_prop.tga" );
 	uis.charsetPropGlow	= trap_R_RegisterShaderNoMip( "menu/art/font1_prop_glo.tga" );
 	uis.charsetPropB	= trap_R_RegisterShaderNoMip( "menu/art/font2_prop.tga" );
-	//uis.cursor          = trap_R_RegisterShaderNoMip( "menu/art/3_cursor2" );
-	uis.cursor          = trap_R_RegisterShaderNoMip( "ui/assets/3_cursor3" );
+	uis.cursor          = trap_R_RegisterShaderNoMip( "menu/art/3_cursor2" );
 	uis.rb_on           = trap_R_RegisterShaderNoMip( "menu/art/switch_on" );
 	uis.rb_off          = trap_R_RegisterShaderNoMip( "menu/art/switch_off" );
 
 	uis.whiteShader = trap_R_RegisterShaderNoMip( "white" );
-	if (!uis.whiteShader) {
-		uis.whiteShader = trap_R_RegisterShaderNoMip("wcwhite");
-	}
 	if ( uis.glconfig.hardwareType == GLHW_RAGEPRO ) {
-		// the blend effect turns to shit with the normal
+		// the blend effect turns to shit with the normal 
 		uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menubackRagePro" );
 	} else {
-		//uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menuback" );
-		uis.menuBackShader = trap_R_RegisterShaderNoMip( "menubacknologo" );
+		uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menuback" );
 	}
 	uis.menuBackNoLogoShader = trap_R_RegisterShaderNoMip( "menubacknologo" );
 
-	//FIXME hack.. key handler depends on returning non zero sound if
-	// handled
-	menu_in_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_in_sound) {
-		menu_in_sound = -2;
-	}
+	menu_in_sound	= trap_S_RegisterSound( "sound/misc/menu1.wav", qfalse );
 	menu_move_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_move_sound) {
-		menu_move_sound = -3;
-	}
-	menu_out_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_out_sound) {
-		menu_out_sound = -4;
-	}
-	menu_buzz_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_buzz_sound) {
-		menu_buzz_sound = -5;
-	}
+	menu_out_sound	= trap_S_RegisterSound( "sound/misc/menu3.wav", qfalse );
+	menu_buzz_sound	= trap_S_RegisterSound( "sound/misc/menu4.wav", qfalse );
 	weaponChangeSound	= trap_S_RegisterSound( "sound/weapons/change.wav", qfalse );
-	if (!weaponChangeSound) {
-		weaponChangeSound = -6;
-	}
 
 	// need a nonzero sound, make an empty sound for this
 	menu_null_sound = -1;
@@ -1805,3 +1743,4 @@
 	sliderButton_0 = trap_R_RegisterShaderNoMip( "menu/art/sliderbutt_0" );
 	sliderButton_1 = trap_R_RegisterShaderNoMip( "menu/art/sliderbutt_1" );
 }
+	

```

### `ioquake3`  — sha256 `fac141285687...`, 38650 bytes

_Diff stat: +99 / -129 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_qmenu.c	2026-04-16 20:02:25.210502700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\q3_ui\ui_qmenu.c	2026-04-16 20:02:21.557593600 +0100
@@ -55,7 +55,7 @@
 vec4_t text_color_normal    = {1.00f, 0.43f, 0.00f, 1.00f};	// light orange
 vec4_t text_color_highlight = {1.00f, 1.00f, 0.00f, 1.00f};	// bright yellow
 vec4_t listbar_color        = {1.00f, 0.43f, 0.00f, 0.30f};	// transluscent orange
-vec4_t text_color_status    = {1.00f, 1.00f, 1.00f, 1.00f};	// bright white
+vec4_t text_color_status    = {1.00f, 1.00f, 1.00f, 1.00f};	// bright white	
 
 // action widget
 static void	Action_Init( menuaction_s *a );
@@ -81,7 +81,7 @@
 static void Text_Draw( menutext_s *b );
 
 // scrolllist widget
-void	ScrollList_Init( menulist_s *l );
+static void	ScrollList_Init( menulist_s *l );
 sfxHandle_t ScrollList_Key( menulist_s *l, int key );
 
 // proportional text widget
@@ -111,7 +111,7 @@
 {
 	int		x;
 	int		y;
-	char	buff[512];
+	char	buff[512];	
 	float*	color;
 
 	x = t->generic.x;
@@ -126,7 +126,7 @@
 	// possible value
 	if (t->string)
 		strcat(buff,t->string);
-
+		
 	if (t->generic.flags & QMF_GRAYED)
 		color = text_color_disabled;
 	else
@@ -327,16 +327,16 @@
 		if (b->shader)
 			UI_DrawHandlePic( x, y, w, h, b->shader );
 
-		if (  ( (b->generic.flags & QMF_PULSE)
+		if (  ( (b->generic.flags & QMF_PULSE) 
 			|| (b->generic.flags & QMF_PULSEIFFOCUS) )
 		      && (Menu_ItemAtCursor( b->generic.parent ) == b))
-		{
-			if (b->focuscolor)
+		{	
+			if (b->focuscolor)			
 			{
 				tempcolor[0] = b->focuscolor[0];
 				tempcolor[1] = b->focuscolor[1];
 				tempcolor[2] = b->focuscolor[2];
-				color        = tempcolor;
+				color        = tempcolor;	
 			}
 			else
 				color = pulse_color;
@@ -347,7 +347,7 @@
 			trap_R_SetColor( NULL );
 		}
 		else if ((b->generic.flags & QMF_HIGHLIGHT) || ((b->generic.flags & QMF_HIGHLIGHT_IF_FOCUS) && (Menu_ItemAtCursor( b->generic.parent ) == b)))
-		{
+		{	
 			if (b->focuscolor)
 			{
 				trap_R_SetColor( b->focuscolor );
@@ -376,7 +376,7 @@
 		len = 0;
 
 	// left justify text
-	a->generic.left   = a->generic.x;
+	a->generic.left   = a->generic.x; 
 	a->generic.right  = a->generic.x + len*BIGCHAR_WIDTH;
 	a->generic.top    = a->generic.y;
 	a->generic.bottom = a->generic.y + BIGCHAR_HEIGHT;
@@ -518,7 +518,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( rb->generic.left, rb->generic.top, rb->generic.right-rb->generic.left+1, rb->generic.bottom-rb->generic.top+1, listbar_color );
+		UI_FillRect( rb->generic.left, rb->generic.top, rb->generic.right-rb->generic.left+1, rb->generic.bottom-rb->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -552,7 +552,7 @@
 	else
 		len = 0;
 
-	s->generic.left   = s->generic.x - (len+1)*SMALLCHAR_WIDTH;
+	s->generic.left   = s->generic.x - (len+1)*SMALLCHAR_WIDTH; 
 	s->generic.right  = s->generic.x + (SLIDER_RANGE+2+1)*SMALLCHAR_WIDTH;
 	s->generic.top    = s->generic.y;
 	s->generic.bottom = s->generic.y + SMALLCHAR_HEIGHT;
@@ -595,7 +595,7 @@
 			}
 			else
 				sound = menu_buzz_sound;
-			break;
+			break;			
 
 		case K_KP_RIGHTARROW:
 		case K_RIGHTARROW:
@@ -606,7 +606,7 @@
 			}
 			else
 				sound = menu_buzz_sound;
-			break;
+			break;			
 
 		default:
 			// key not handled
@@ -633,7 +633,7 @@
 	float		*color;
 	int			button;
 	qboolean	focus;
-
+	
 	x =	s->generic.x;
 	y = s->generic.y;
 	focus = (s->generic.parent->cursor == s->generic.menuPosition);
@@ -697,7 +697,7 @@
 	int x;
 	int y;
 	qboolean focus;
-
+	
 	x =	s->generic.x;
 	y = s->generic.y;
 	focus = (s->generic.parent->cursor == s->generic.menuPosition);
@@ -720,7 +720,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color );
+		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -779,7 +779,7 @@
 			len = l;
 
 		s->numitems++;
-	}
+	}		
 
 	s->generic.top	  =	s->generic.y;
 	s->generic.right  =	s->generic.x + (len+1)*SMALLCHAR_WIDTH;
@@ -798,15 +798,15 @@
 	sound = 0;
 	switch (key)
 	{
-	    case K_KP_RIGHTARROW:
-	    case K_RIGHTARROW:
+		case K_KP_RIGHTARROW:
+		case K_RIGHTARROW:
 		case K_MOUSE1:
 			s->curvalue++;
 			if (s->curvalue >= s->numitems)
 				s->curvalue = 0;
 			sound = menu_move_sound;
 			break;
-
+		
 		case K_KP_LEFTARROW:
 		case K_LEFTARROW:
 			s->curvalue--;
@@ -858,7 +858,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color );
+		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -871,7 +871,7 @@
 ScrollList_Init
 =================
 */
-void ScrollList_Init( menulist_s *l )
+static void ScrollList_Init( menulist_s *l )
 {
 	int		w;
 
@@ -890,7 +890,7 @@
 	w = ( (l->width + l->separation) * l->columns - l->separation) * SMALLCHAR_WIDTH;
 
 	l->generic.left   =	l->generic.x;
-	l->generic.top    = l->generic.y;
+	l->generic.top    = l->generic.y;	
 	l->generic.right  =	l->generic.x + w;
 	l->generic.bottom =	l->generic.y + l->height * SMALLCHAR_HEIGHT;
 
@@ -911,25 +911,16 @@
 	int	y;
 	int	w;
 	int	i;
-	int	j;
+	int	j;	
 	int	c;
 	int	cursorx;
 	int	cursory;
 	int	column;
 	int	index;
-	static int clickTime = 0;
-	qboolean doubleClicked;
 
 	switch (key)
 	{
-        case K_MOUSE1:
-			if (trap_Milliseconds() - clickTime < ui_doubleClickTime.integer) {
-				clickTime = 0;
-				doubleClicked = qtrue;
-			} else {
-				clickTime = trap_Milliseconds();
-				doubleClicked = qfalse;
-			}
+		case K_MOUSE1:
 			if (l->generic.flags & QMF_HASMOUSEFOCUS)
 			{
 				// check scroll region
@@ -955,20 +946,12 @@
 							l->generic.callback( l, QM_GOTFOCUS );
 							return (menu_move_sound);
 						}
-
 					}
-
-
-				}
-
-				if (doubleClicked  &&  l->generic.callback) {
-					l->generic.callback(l, QM_DOUBLECLICKED);
 				}
-
+			
 				// absorbed, silent sound effect
 				return (menu_null_sound);
 			}
-
 			break;
 
 		case K_KP_HOME:
@@ -996,7 +979,7 @@
 				l->top = l->curvalue - (l->height - 1);
 			}
 			if (l->top < 0)
-				l->top = 0;
+				l->top = 0;			
 
 			if (l->oldvalue != l->curvalue && l->generic.callback)
 			{
@@ -1051,7 +1034,50 @@
 			}
 			return (menu_buzz_sound);
 
-	case K_MWHEELUP:
+		case K_MWHEELUP:
+			if( l->columns > 1 ) {
+				return menu_null_sound;
+			}
+
+			if (l->top > 0)
+			{
+				// if scrolling 3 lines would replace over half of the
+				// displayed items, only scroll 1 item at a time.
+				int scroll = l->height < 6 ? 1 : 3;
+				l->top -= scroll;
+				if (l->top < 0)
+					l->top = 0;
+
+				if (l->generic.callback)
+					l->generic.callback( l, QM_GOTFOCUS );
+
+				// make scrolling silent
+				return (menu_null_sound);
+			}
+			return (menu_buzz_sound);
+
+		case K_MWHEELDOWN:
+			if( l->columns > 1 ) {
+				return menu_null_sound;
+			}
+
+			if (l->top < l->numitems-l->height)
+			{
+				// if scrolling 3 items would replace over half of the
+				// displayed items, only scroll 1 item at a time.
+				int scroll = l->height < 6 ? 1 : 3;
+				l->top += scroll;
+				if (l->top > l->numitems-l->height)
+					l->top = l->numitems-l->height;
+
+				if (l->generic.callback)
+					l->generic.callback( l, QM_GOTFOCUS );
+
+				// make scrolling silent
+				return (menu_null_sound);
+			}
+			return (menu_buzz_sound);
+
 		case K_KP_UPARROW:
 		case K_UPARROW:
 			if( l->curvalue == 0 ) {
@@ -1076,7 +1102,6 @@
 
 			return (menu_move_sound);
 
-	case K_MWHEELDOWN:
 		case K_KP_DOWNARROW:
 		case K_DOWNARROW:
 			if( l->curvalue == l->numitems - 1 ) {
@@ -1183,14 +1208,14 @@
 				// past end of list box, do page down
 				l->top = (j+1) - l->height;
 			}
-
+			
 			if (l->curvalue != j)
 			{
 				l->oldvalue = l->curvalue;
 				l->curvalue = j;
 				if (l->generic.callback)
 					l->generic.callback( l, QM_GOTFOCUS );
-				return ( menu_move_sound );
+				return ( menu_move_sound );			
 			}
 
 			return (menu_buzz_sound);
@@ -1216,7 +1241,6 @@
 	float*		color;
 	qboolean	hasfocus;
 	int			style;
-	int slen;
 
 	hasfocus = (l->generic.parent->cursor == l->generic.menuPosition);
 
@@ -1235,9 +1259,7 @@
 					u -= (l->width * SMALLCHAR_WIDTH) / 2 + 1;
 				}
 
-				//UI_FillRect(u,y,l->width*SMALLCHAR_WIDTH,SMALLCHAR_HEIGHT+2,listbar_color);
-				slen = strlen(l->itemnames[i]);
-				UI_FillRect(u, y, slen * SMALLCHAR_WIDTH + 4, SMALLCHAR_HEIGHT + 2, listbar_color);
+				UI_FillRect(u,y,l->width*SMALLCHAR_WIDTH,SMALLCHAR_HEIGHT+2,listbar_color);
 				color = text_color_highlight;
 
 				if (hasfocus)
@@ -1346,18 +1368,17 @@
 void Menu_CursorMoved( menuframework_s *m )
 {
 	void (*callback)( void *self, int notification );
-
+	
 	if (m->cursor_prev == m->cursor)
 		return;
 
 	if (m->cursor_prev >= 0 && m->cursor_prev < m->nitems)
 	{
 		callback = ((menucommon_s*)(m->items[m->cursor_prev]))->callback;
-		if (callback) {
+		if (callback)
 			callback(m->items[m->cursor_prev],QM_LOSTFOCUS);
-		}
 	}
-
+	
 	if (m->cursor >= 0 && m->cursor < m->nitems)
 	{
 		callback = ((menucommon_s*)(m->items[m->cursor]))->callback;
@@ -1478,11 +1499,11 @@
 		{
 			// total subclassing, owner draws everything
 			itemptr->ownerdraw( itemptr );
-		}
-		else
+		}	
+		else 
 		{
 			switch (itemptr->type)
-			{
+			{	
 				case MTYPE_RADIOBUTTON:
 					RadioButton_Draw( (menuradiobutton_s*)itemptr );
 					break;
@@ -1490,19 +1511,19 @@
 				case MTYPE_FIELD:
 					MenuField_Draw( (menufield_s*)itemptr );
 					break;
-
+		
 				case MTYPE_SLIDER:
 					Slider_Draw( (menuslider_s*)itemptr );
 					break;
-
+ 
 				case MTYPE_SPINCONTROL:
 					SpinControl_Draw( (menulist_s*)itemptr );
 					break;
-
+		
 				case MTYPE_ACTION:
 					Action_Draw( (menuaction_s*)itemptr );
 					break;
-
+		
 				case MTYPE_BITMAP:
 					Bitmap_Draw( (menubitmap_s*)itemptr );
 					break;
@@ -1514,7 +1535,7 @@
 				case MTYPE_SCROLLLIST:
 					ScrollList_Draw( (menulist_s*)itemptr );
 					break;
-
+				
 				case MTYPE_PTEXT:
 					PText_Draw( (menutext_s*)itemptr );
 					break;
@@ -1527,7 +1548,7 @@
 					trap_Error( va("Menu_Draw: unknown type %d", itemptr->type) );
 			}
 		}
-#ifndef NQDEBUG
+#ifndef NDEBUG
 		if( uis.debug ) {
 			int	x;
 			int	y;
@@ -1595,12 +1616,11 @@
 	sfxHandle_t		sound = 0;
 	menucommon_s	*item;
 	int				cursor_prev;
-	char buf[MAX_STRING_CHARS];
 
 	// menu system keys
 	switch ( key )
 	{
-		//case K_MOUSE2:
+		case K_MOUSE2:
 		case K_ESCAPE:
 			UI_PopMenu();
 			return menu_out_sound;
@@ -1638,14 +1658,14 @@
 
 		if (sound) {
 			// key was handled
-			return sound;
+			return sound;		
 		}
 	}
 
 	// default handling
 	switch ( key )
 	{
-#if 0  //ndef NQDEBUG
+#ifndef NDEBUG
 		case K_F11:
 			uis.debug ^= 1;
 			break;
@@ -1654,7 +1674,6 @@
 			trap_Cmd_ExecuteText(EXEC_APPEND, "screenshot\n");
 			break;
 #endif
-	case K_MWHEELUP:
 		case K_KP_UPARROW:
 		case K_UPARROW:
 			cursor_prev    = m->cursor;
@@ -1667,7 +1686,6 @@
 			}
 			break;
 
-	case K_MWHEELDOWN:
 		case K_TAB:
 		case K_KP_DOWNARROW:
 		case K_DOWNARROW:
@@ -1710,20 +1728,9 @@
 		case K_AUX16:
 		case K_KP_ENTER:
 		case K_ENTER:
-			if (item) {
-				if (!(item->flags & (QMF_MOUSEONLY|QMF_GRAYED|QMF_INACTIVE))) {
+			if (item)
+				if (!(item->flags & (QMF_MOUSEONLY|QMF_GRAYED|QMF_INACTIVE)))
 					return (Menu_ActivateItem( m, item ));
-				} else {
-				}
-			}
-			break;
-	    default:
-			buf[0] = '\0';
-			trap_Key_GetBindingBuf(key, buf, sizeof(buf));
-			if (!*buf  ||  buf[0] == '+'  ||  buf[1] == '-'  ||  !Q_stricmpn(buf, "vstr", strlen("vstr") - 1)) {
-				break;
-			}
-			trap_Cmd_ExecuteText(EXEC_NOW, buf);
 			break;
 	}
 
@@ -1738,65 +1745,27 @@
 void Menu_Cache( void )
 {
 	uis.charset			= trap_R_RegisterShaderNoMip( "gfx/2d/bigchars" );
-
-	if (!uis.charset) {
-		uis.charset = trap_R_RegisterShaderNoMip("gfx/wc/openarenachars");
-		uis.charsetProp		= trap_R_RegisterShaderNoMip("gfx/wc/font1_prop.tga");
-		uis.charsetPropGlow	= trap_R_RegisterShaderNoMip("gfx/wc/font1_prop_glo.tga");
-		uis.charsetPropB	= trap_R_RegisterShaderNoMip("gfx/wc/font2_prop.tga");
-		//uis.charsetProp = uis.charset;
-		//uis.charsetPropGlow = uis.charset;
-		//uis.charsetPropB = uis.charset;
-		uis.showErrorMenu = qtrue;
-		//trap_Cvar_Set("com_errorMessage", "quakelive paks not found");
-		uis.cursor = trap_R_RegisterShaderNoMip("gfx/wc/3_cursor2");
-		uis.menuBackShader = uis.menuBackNoLogoShader = trap_R_RegisterShaderNoMip("gfx/wc/black.png");
-		return;
-	}
-
 	uis.charsetProp		= trap_R_RegisterShaderNoMip( "menu/art/font1_prop.tga" );
 	uis.charsetPropGlow	= trap_R_RegisterShaderNoMip( "menu/art/font1_prop_glo.tga" );
 	uis.charsetPropB	= trap_R_RegisterShaderNoMip( "menu/art/font2_prop.tga" );
-	//uis.cursor          = trap_R_RegisterShaderNoMip( "menu/art/3_cursor2" );
-	uis.cursor          = trap_R_RegisterShaderNoMip( "ui/assets/3_cursor3" );
+	uis.cursor          = trap_R_RegisterShaderNoMip( "menu/art/3_cursor2" );
 	uis.rb_on           = trap_R_RegisterShaderNoMip( "menu/art/switch_on" );
 	uis.rb_off          = trap_R_RegisterShaderNoMip( "menu/art/switch_off" );
 
 	uis.whiteShader = trap_R_RegisterShaderNoMip( "white" );
-	if (!uis.whiteShader) {
-		uis.whiteShader = trap_R_RegisterShaderNoMip("wcwhite");
-	}
 	if ( uis.glconfig.hardwareType == GLHW_RAGEPRO ) {
-		// the blend effect turns to shit with the normal
+		// the blend effect turns to shit with the normal 
 		uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menubackRagePro" );
 	} else {
-		//uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menuback" );
-		uis.menuBackShader = trap_R_RegisterShaderNoMip( "menubacknologo" );
+		uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menuback" );
 	}
 	uis.menuBackNoLogoShader = trap_R_RegisterShaderNoMip( "menubacknologo" );
 
-	//FIXME hack.. key handler depends on returning non zero sound if
-	// handled
-	menu_in_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_in_sound) {
-		menu_in_sound = -2;
-	}
+	menu_in_sound	= trap_S_RegisterSound( "sound/misc/menu1.wav", qfalse );
 	menu_move_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_move_sound) {
-		menu_move_sound = -3;
-	}
-	menu_out_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_out_sound) {
-		menu_out_sound = -4;
-	}
-	menu_buzz_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_buzz_sound) {
-		menu_buzz_sound = -5;
-	}
+	menu_out_sound	= trap_S_RegisterSound( "sound/misc/menu3.wav", qfalse );
+	menu_buzz_sound	= trap_S_RegisterSound( "sound/misc/menu4.wav", qfalse );
 	weaponChangeSound	= trap_S_RegisterSound( "sound/weapons/change.wav", qfalse );
-	if (!weaponChangeSound) {
-		weaponChangeSound = -6;
-	}
 
 	// need a nonzero sound, make an empty sound for this
 	menu_null_sound = -1;
@@ -1805,3 +1774,4 @@
 	sliderButton_0 = trap_R_RegisterShaderNoMip( "menu/art/sliderbutt_0" );
 	sliderButton_1 = trap_R_RegisterShaderNoMip( "menu/art/sliderbutt_1" );
 }
+	

```

### `openarena-engine`  — sha256 `740b01ec7d3e...`, 37576 bytes

_Diff stat: +62 / -136 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\q3_ui\ui_qmenu.c	2026-04-16 20:02:25.210502700 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\q3_ui\ui_qmenu.c	2026-04-16 22:48:25.898194800 +0100
@@ -55,7 +55,7 @@
 vec4_t text_color_normal    = {1.00f, 0.43f, 0.00f, 1.00f};	// light orange
 vec4_t text_color_highlight = {1.00f, 1.00f, 0.00f, 1.00f};	// bright yellow
 vec4_t listbar_color        = {1.00f, 0.43f, 0.00f, 0.30f};	// transluscent orange
-vec4_t text_color_status    = {1.00f, 1.00f, 1.00f, 1.00f};	// bright white
+vec4_t text_color_status    = {1.00f, 1.00f, 1.00f, 1.00f};	// bright white	
 
 // action widget
 static void	Action_Init( menuaction_s *a );
@@ -81,7 +81,7 @@
 static void Text_Draw( menutext_s *b );
 
 // scrolllist widget
-void	ScrollList_Init( menulist_s *l );
+static void	ScrollList_Init( menulist_s *l );
 sfxHandle_t ScrollList_Key( menulist_s *l, int key );
 
 // proportional text widget
@@ -111,7 +111,7 @@
 {
 	int		x;
 	int		y;
-	char	buff[512];
+	char	buff[512];	
 	float*	color;
 
 	x = t->generic.x;
@@ -126,7 +126,7 @@
 	// possible value
 	if (t->string)
 		strcat(buff,t->string);
-
+		
 	if (t->generic.flags & QMF_GRAYED)
 		color = text_color_disabled;
 	else
@@ -327,16 +327,16 @@
 		if (b->shader)
 			UI_DrawHandlePic( x, y, w, h, b->shader );
 
-		if (  ( (b->generic.flags & QMF_PULSE)
+		if (  ( (b->generic.flags & QMF_PULSE) 
 			|| (b->generic.flags & QMF_PULSEIFFOCUS) )
 		      && (Menu_ItemAtCursor( b->generic.parent ) == b))
-		{
-			if (b->focuscolor)
+		{	
+			if (b->focuscolor)			
 			{
 				tempcolor[0] = b->focuscolor[0];
 				tempcolor[1] = b->focuscolor[1];
 				tempcolor[2] = b->focuscolor[2];
-				color        = tempcolor;
+				color        = tempcolor;	
 			}
 			else
 				color = pulse_color;
@@ -347,7 +347,7 @@
 			trap_R_SetColor( NULL );
 		}
 		else if ((b->generic.flags & QMF_HIGHLIGHT) || ((b->generic.flags & QMF_HIGHLIGHT_IF_FOCUS) && (Menu_ItemAtCursor( b->generic.parent ) == b)))
-		{
+		{	
 			if (b->focuscolor)
 			{
 				trap_R_SetColor( b->focuscolor );
@@ -376,7 +376,7 @@
 		len = 0;
 
 	// left justify text
-	a->generic.left   = a->generic.x;
+	a->generic.left   = a->generic.x; 
 	a->generic.right  = a->generic.x + len*BIGCHAR_WIDTH;
 	a->generic.top    = a->generic.y;
 	a->generic.bottom = a->generic.y + BIGCHAR_HEIGHT;
@@ -518,7 +518,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( rb->generic.left, rb->generic.top, rb->generic.right-rb->generic.left+1, rb->generic.bottom-rb->generic.top+1, listbar_color );
+		UI_FillRect( rb->generic.left, rb->generic.top, rb->generic.right-rb->generic.left+1, rb->generic.bottom-rb->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -552,7 +552,7 @@
 	else
 		len = 0;
 
-	s->generic.left   = s->generic.x - (len+1)*SMALLCHAR_WIDTH;
+	s->generic.left   = s->generic.x - (len+1)*SMALLCHAR_WIDTH; 
 	s->generic.right  = s->generic.x + (SLIDER_RANGE+2+1)*SMALLCHAR_WIDTH;
 	s->generic.top    = s->generic.y;
 	s->generic.bottom = s->generic.y + SMALLCHAR_HEIGHT;
@@ -595,7 +595,7 @@
 			}
 			else
 				sound = menu_buzz_sound;
-			break;
+			break;			
 
 		case K_KP_RIGHTARROW:
 		case K_RIGHTARROW:
@@ -606,7 +606,7 @@
 			}
 			else
 				sound = menu_buzz_sound;
-			break;
+			break;			
 
 		default:
 			// key not handled
@@ -633,7 +633,7 @@
 	float		*color;
 	int			button;
 	qboolean	focus;
-
+	
 	x =	s->generic.x;
 	y = s->generic.y;
 	focus = (s->generic.parent->cursor == s->generic.menuPosition);
@@ -697,7 +697,7 @@
 	int x;
 	int y;
 	qboolean focus;
-
+	
 	x =	s->generic.x;
 	y = s->generic.y;
 	focus = (s->generic.parent->cursor == s->generic.menuPosition);
@@ -720,7 +720,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color );
+		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -779,7 +779,7 @@
 			len = l;
 
 		s->numitems++;
-	}
+	}		
 
 	s->generic.top	  =	s->generic.y;
 	s->generic.right  =	s->generic.x + (len+1)*SMALLCHAR_WIDTH;
@@ -798,15 +798,15 @@
 	sound = 0;
 	switch (key)
 	{
-	    case K_KP_RIGHTARROW:
-	    case K_RIGHTARROW:
+		case K_KP_RIGHTARROW:
+		case K_RIGHTARROW:
 		case K_MOUSE1:
 			s->curvalue++;
 			if (s->curvalue >= s->numitems)
 				s->curvalue = 0;
 			sound = menu_move_sound;
 			break;
-
+		
 		case K_KP_LEFTARROW:
 		case K_LEFTARROW:
 			s->curvalue--;
@@ -858,7 +858,7 @@
 	if ( focus )
 	{
 		// draw cursor
-		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color );
+		UI_FillRect( s->generic.left, s->generic.top, s->generic.right-s->generic.left+1, s->generic.bottom-s->generic.top+1, listbar_color ); 
 		UI_DrawChar( x, y, 13, UI_CENTER|UI_BLINK|UI_SMALLFONT, color);
 	}
 
@@ -871,7 +871,7 @@
 ScrollList_Init
 =================
 */
-void ScrollList_Init( menulist_s *l )
+static void ScrollList_Init( menulist_s *l )
 {
 	int		w;
 
@@ -881,16 +881,16 @@
 
 	if( !l->columns ) {
 		l->columns = 1;
-		l->separation = 0;
+		l->seperation = 0;
 	}
-	else if( !l->separation ) {
-		l->separation = 3;
+	else if( !l->seperation ) {
+		l->seperation = 3;
 	}
 
-	w = ( (l->width + l->separation) * l->columns - l->separation) * SMALLCHAR_WIDTH;
+	w = ( (l->width + l->seperation) * l->columns - l->seperation) * SMALLCHAR_WIDTH;
 
 	l->generic.left   =	l->generic.x;
-	l->generic.top    = l->generic.y;
+	l->generic.top    = l->generic.y;	
 	l->generic.right  =	l->generic.x + w;
 	l->generic.bottom =	l->generic.y + l->height * SMALLCHAR_HEIGHT;
 
@@ -911,38 +911,29 @@
 	int	y;
 	int	w;
 	int	i;
-	int	j;
+	int	j;	
 	int	c;
 	int	cursorx;
 	int	cursory;
 	int	column;
 	int	index;
-	static int clickTime = 0;
-	qboolean doubleClicked;
 
 	switch (key)
 	{
-        case K_MOUSE1:
-			if (trap_Milliseconds() - clickTime < ui_doubleClickTime.integer) {
-				clickTime = 0;
-				doubleClicked = qtrue;
-			} else {
-				clickTime = trap_Milliseconds();
-				doubleClicked = qfalse;
-			}
+		case K_MOUSE1:
 			if (l->generic.flags & QMF_HASMOUSEFOCUS)
 			{
 				// check scroll region
 				x = l->generic.x;
 				y = l->generic.y;
-				w = ( (l->width + l->separation) * l->columns - l->separation) * SMALLCHAR_WIDTH;
+				w = ( (l->width + l->seperation) * l->columns - l->seperation) * SMALLCHAR_WIDTH;
 				if( l->generic.flags & QMF_CENTER_JUSTIFY ) {
 					x -= w / 2;
 				}
 				if (UI_CursorInRect( x, y, w, l->height*SMALLCHAR_HEIGHT ))
 				{
 					cursorx = (uis.cursorx - x)/SMALLCHAR_WIDTH;
-					column = cursorx / (l->width + l->separation);
+					column = cursorx / (l->width + l->seperation);
 					cursory = (uis.cursory - y)/SMALLCHAR_HEIGHT;
 					index = column * l->height + cursory;
 					if (l->top + index < l->numitems)
@@ -955,20 +946,12 @@
 							l->generic.callback( l, QM_GOTFOCUS );
 							return (menu_move_sound);
 						}
-
 					}
-
-
-				}
-
-				if (doubleClicked  &&  l->generic.callback) {
-					l->generic.callback(l, QM_DOUBLECLICKED);
 				}
-
+			
 				// absorbed, silent sound effect
 				return (menu_null_sound);
 			}
-
 			break;
 
 		case K_KP_HOME:
@@ -996,7 +979,7 @@
 				l->top = l->curvalue - (l->height - 1);
 			}
 			if (l->top < 0)
-				l->top = 0;
+				l->top = 0;			
 
 			if (l->oldvalue != l->curvalue && l->generic.callback)
 			{
@@ -1051,7 +1034,6 @@
 			}
 			return (menu_buzz_sound);
 
-	case K_MWHEELUP:
 		case K_KP_UPARROW:
 		case K_UPARROW:
 			if( l->curvalue == 0 ) {
@@ -1076,7 +1058,6 @@
 
 			return (menu_move_sound);
 
-	case K_MWHEELDOWN:
 		case K_KP_DOWNARROW:
 		case K_DOWNARROW:
 			if( l->curvalue == l->numitems - 1 ) {
@@ -1183,14 +1164,14 @@
 				// past end of list box, do page down
 				l->top = (j+1) - l->height;
 			}
-
+			
 			if (l->curvalue != j)
 			{
 				l->oldvalue = l->curvalue;
 				l->curvalue = j;
 				if (l->generic.callback)
 					l->generic.callback( l, QM_GOTFOCUS );
-				return ( menu_move_sound );
+				return ( menu_move_sound );			
 			}
 
 			return (menu_buzz_sound);
@@ -1216,7 +1197,6 @@
 	float*		color;
 	qboolean	hasfocus;
 	int			style;
-	int slen;
 
 	hasfocus = (l->generic.parent->cursor == l->generic.menuPosition);
 
@@ -1235,9 +1215,7 @@
 					u -= (l->width * SMALLCHAR_WIDTH) / 2 + 1;
 				}
 
-				//UI_FillRect(u,y,l->width*SMALLCHAR_WIDTH,SMALLCHAR_HEIGHT+2,listbar_color);
-				slen = strlen(l->itemnames[i]);
-				UI_FillRect(u, y, slen * SMALLCHAR_WIDTH + 4, SMALLCHAR_HEIGHT + 2, listbar_color);
+				UI_FillRect(u,y,l->width*SMALLCHAR_WIDTH,SMALLCHAR_HEIGHT+2,listbar_color);
 				color = text_color_highlight;
 
 				if (hasfocus)
@@ -1263,7 +1241,7 @@
 
 			y += SMALLCHAR_HEIGHT;
 		}
-		x += (l->width + l->separation) * SMALLCHAR_WIDTH;
+		x += (l->width + l->seperation) * SMALLCHAR_WIDTH;
 	}
 }
 
@@ -1346,18 +1324,17 @@
 void Menu_CursorMoved( menuframework_s *m )
 {
 	void (*callback)( void *self, int notification );
-
+	
 	if (m->cursor_prev == m->cursor)
 		return;
 
 	if (m->cursor_prev >= 0 && m->cursor_prev < m->nitems)
 	{
 		callback = ((menucommon_s*)(m->items[m->cursor_prev]))->callback;
-		if (callback) {
+		if (callback)
 			callback(m->items[m->cursor_prev],QM_LOSTFOCUS);
-		}
 	}
-
+	
 	if (m->cursor >= 0 && m->cursor < m->nitems)
 	{
 		callback = ((menucommon_s*)(m->items[m->cursor]))->callback;
@@ -1478,11 +1455,11 @@
 		{
 			// total subclassing, owner draws everything
 			itemptr->ownerdraw( itemptr );
-		}
-		else
+		}	
+		else 
 		{
 			switch (itemptr->type)
-			{
+			{	
 				case MTYPE_RADIOBUTTON:
 					RadioButton_Draw( (menuradiobutton_s*)itemptr );
 					break;
@@ -1490,19 +1467,19 @@
 				case MTYPE_FIELD:
 					MenuField_Draw( (menufield_s*)itemptr );
 					break;
-
+		
 				case MTYPE_SLIDER:
 					Slider_Draw( (menuslider_s*)itemptr );
 					break;
-
+ 
 				case MTYPE_SPINCONTROL:
 					SpinControl_Draw( (menulist_s*)itemptr );
 					break;
-
+		
 				case MTYPE_ACTION:
 					Action_Draw( (menuaction_s*)itemptr );
 					break;
-
+		
 				case MTYPE_BITMAP:
 					Bitmap_Draw( (menubitmap_s*)itemptr );
 					break;
@@ -1514,7 +1491,7 @@
 				case MTYPE_SCROLLLIST:
 					ScrollList_Draw( (menulist_s*)itemptr );
 					break;
-
+				
 				case MTYPE_PTEXT:
 					PText_Draw( (menutext_s*)itemptr );
 					break;
@@ -1527,7 +1504,7 @@
 					trap_Error( va("Menu_Draw: unknown type %d", itemptr->type) );
 			}
 		}
-#ifndef NQDEBUG
+#ifndef NDEBUG
 		if( uis.debug ) {
 			int	x;
 			int	y;
@@ -1595,12 +1572,11 @@
 	sfxHandle_t		sound = 0;
 	menucommon_s	*item;
 	int				cursor_prev;
-	char buf[MAX_STRING_CHARS];
 
 	// menu system keys
 	switch ( key )
 	{
-		//case K_MOUSE2:
+		case K_MOUSE2:
 		case K_ESCAPE:
 			UI_PopMenu();
 			return menu_out_sound;
@@ -1638,14 +1614,14 @@
 
 		if (sound) {
 			// key was handled
-			return sound;
+			return sound;		
 		}
 	}
 
 	// default handling
 	switch ( key )
 	{
-#if 0  //ndef NQDEBUG
+#ifndef NDEBUG
 		case K_F11:
 			uis.debug ^= 1;
 			break;
@@ -1654,7 +1630,6 @@
 			trap_Cmd_ExecuteText(EXEC_APPEND, "screenshot\n");
 			break;
 #endif
-	case K_MWHEELUP:
 		case K_KP_UPARROW:
 		case K_UPARROW:
 			cursor_prev    = m->cursor;
@@ -1667,7 +1642,6 @@
 			}
 			break;
 
-	case K_MWHEELDOWN:
 		case K_TAB:
 		case K_KP_DOWNARROW:
 		case K_DOWNARROW:
@@ -1710,20 +1684,9 @@
 		case K_AUX16:
 		case K_KP_ENTER:
 		case K_ENTER:
-			if (item) {
-				if (!(item->flags & (QMF_MOUSEONLY|QMF_GRAYED|QMF_INACTIVE))) {
+			if (item)
+				if (!(item->flags & (QMF_MOUSEONLY|QMF_GRAYED|QMF_INACTIVE)))
 					return (Menu_ActivateItem( m, item ));
-				} else {
-				}
-			}
-			break;
-	    default:
-			buf[0] = '\0';
-			trap_Key_GetBindingBuf(key, buf, sizeof(buf));
-			if (!*buf  ||  buf[0] == '+'  ||  buf[1] == '-'  ||  !Q_stricmpn(buf, "vstr", strlen("vstr") - 1)) {
-				break;
-			}
-			trap_Cmd_ExecuteText(EXEC_NOW, buf);
 			break;
 	}
 
@@ -1738,65 +1701,27 @@
 void Menu_Cache( void )
 {
 	uis.charset			= trap_R_RegisterShaderNoMip( "gfx/2d/bigchars" );
-
-	if (!uis.charset) {
-		uis.charset = trap_R_RegisterShaderNoMip("gfx/wc/openarenachars");
-		uis.charsetProp		= trap_R_RegisterShaderNoMip("gfx/wc/font1_prop.tga");
-		uis.charsetPropGlow	= trap_R_RegisterShaderNoMip("gfx/wc/font1_prop_glo.tga");
-		uis.charsetPropB	= trap_R_RegisterShaderNoMip("gfx/wc/font2_prop.tga");
-		//uis.charsetProp = uis.charset;
-		//uis.charsetPropGlow = uis.charset;
-		//uis.charsetPropB = uis.charset;
-		uis.showErrorMenu = qtrue;
-		//trap_Cvar_Set("com_errorMessage", "quakelive paks not found");
-		uis.cursor = trap_R_RegisterShaderNoMip("gfx/wc/3_cursor2");
-		uis.menuBackShader = uis.menuBackNoLogoShader = trap_R_RegisterShaderNoMip("gfx/wc/black.png");
-		return;
-	}
-
 	uis.charsetProp		= trap_R_RegisterShaderNoMip( "menu/art/font1_prop.tga" );
 	uis.charsetPropGlow	= trap_R_RegisterShaderNoMip( "menu/art/font1_prop_glo.tga" );
 	uis.charsetPropB	= trap_R_RegisterShaderNoMip( "menu/art/font2_prop.tga" );
-	//uis.cursor          = trap_R_RegisterShaderNoMip( "menu/art/3_cursor2" );
-	uis.cursor          = trap_R_RegisterShaderNoMip( "ui/assets/3_cursor3" );
+	uis.cursor          = trap_R_RegisterShaderNoMip( "menu/art/3_cursor2" );
 	uis.rb_on           = trap_R_RegisterShaderNoMip( "menu/art/switch_on" );
 	uis.rb_off          = trap_R_RegisterShaderNoMip( "menu/art/switch_off" );
 
 	uis.whiteShader = trap_R_RegisterShaderNoMip( "white" );
-	if (!uis.whiteShader) {
-		uis.whiteShader = trap_R_RegisterShaderNoMip("wcwhite");
-	}
 	if ( uis.glconfig.hardwareType == GLHW_RAGEPRO ) {
-		// the blend effect turns to shit with the normal
+		// the blend effect turns to shit with the normal 
 		uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menubackRagePro" );
 	} else {
-		//uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menuback" );
-		uis.menuBackShader = trap_R_RegisterShaderNoMip( "menubacknologo" );
+		uis.menuBackShader	= trap_R_RegisterShaderNoMip( "menuback" );
 	}
 	uis.menuBackNoLogoShader = trap_R_RegisterShaderNoMip( "menubacknologo" );
 
-	//FIXME hack.. key handler depends on returning non zero sound if
-	// handled
-	menu_in_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_in_sound) {
-		menu_in_sound = -2;
-	}
+	menu_in_sound	= trap_S_RegisterSound( "sound/misc/menu1.wav", qfalse );
 	menu_move_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_move_sound) {
-		menu_move_sound = -3;
-	}
-	menu_out_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_out_sound) {
-		menu_out_sound = -4;
-	}
-	menu_buzz_sound	= trap_S_RegisterSound( "sound/misc/menu2.wav", qfalse );
-	if (!menu_buzz_sound) {
-		menu_buzz_sound = -5;
-	}
+	menu_out_sound	= trap_S_RegisterSound( "sound/misc/menu3.wav", qfalse );
+	menu_buzz_sound	= trap_S_RegisterSound( "sound/misc/menu4.wav", qfalse );
 	weaponChangeSound	= trap_S_RegisterSound( "sound/weapons/change.wav", qfalse );
-	if (!weaponChangeSound) {
-		weaponChangeSound = -6;
-	}
 
 	// need a nonzero sound, make an empty sound for this
 	menu_null_sound = -1;
@@ -1805,3 +1730,4 @@
 	sliderButton_0 = trap_R_RegisterShaderNoMip( "menu/art/sliderbutt_0" );
 	sliderButton_1 = trap_R_RegisterShaderNoMip( "menu/art/sliderbutt_1" );
 }
+	

```

### `openarena-gamecode`  — sha256 `cbcd9afb7315...`, 39546 bytes

_Diff stat: +139 / -158 lines_

_(full diff is 20085 bytes — see files directly)_
