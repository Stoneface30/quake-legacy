# Diff: `code/client/cl_input.c`
**Canonical:** `wolfcamql-src` (sha256 `026e1f0f25c2...`, 30931 bytes)

## Variants

### `quake3-source`  — sha256 `e4dc41bfbb99...`, 24768 bytes

_Diff stat: +83 / -279 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_input.c	2026-04-16 20:02:25.170217200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\quake3-source\code\client\cl_input.c	2026-04-16 20:02:19.890592200 +0100
@@ -15,17 +15,16 @@
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
-along with Quake III Arena source code; if not, write to the Free Software
+along with Foobar; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 ===========================================================================
 */
 // cl.input.c  -- builds an intended movement command to send to the server
 
 #include "client.h"
-#include "keys.h"
 
-static unsigned frame_msec;
-static int old_com_frameTime;
+unsigned	frame_msec;
+int			old_com_frameTime;
 
 /*
 ===============================================================================
@@ -53,10 +52,6 @@
 kbutton_t	in_strafe, in_speed;
 kbutton_t	in_up, in_down;
 
-#ifdef USE_VOIP
-kbutton_t	in_voiprecord;
-#endif
-
 kbutton_t	in_buttons[16];
 
 
@@ -221,20 +216,6 @@
 void IN_StrafeDown(void) {IN_KeyDown(&in_strafe);}
 void IN_StrafeUp(void) {IN_KeyUp(&in_strafe);}
 
-#ifdef USE_VOIP
-void IN_VoipRecordDown(void)
-{
-	IN_KeyDown(&in_voiprecord);
-	Cvar_Set("cl_voipSend", "1");
-}
-
-void IN_VoipRecordUp(void)
-{
-	IN_KeyUp(&in_voiprecord);
-	Cvar_Set("cl_voipSend", "0");
-}
-#endif
-
 void IN_Button0Down(void) {IN_KeyDown(&in_buttons[0]);}
 void IN_Button0Up(void) {IN_KeyUp(&in_buttons[0]);}
 void IN_Button1Down(void) {IN_KeyDown(&in_buttons[1]);}
@@ -268,25 +249,22 @@
 void IN_Button15Down(void) {IN_KeyDown(&in_buttons[15]);}
 void IN_Button15Up(void) {IN_KeyUp(&in_buttons[15]);}
 
+void IN_ButtonDown (void) {
+	IN_KeyDown(&in_buttons[1]);}
+void IN_ButtonUp (void) {
+	IN_KeyUp(&in_buttons[1]);}
+
 void IN_CenterView (void) {
 	cl.viewangles[PITCH] = -SHORT2ANGLE(cl.snap.ps.delta_angles[PITCH]);
 }
 
-#if 0
-void IN_PlusVstr (void)
-{
-	int i;
-
-	Com_Printf("vstr %d\n", Cmd_Argc());
-
-	for (i = 0;  i < Cmd_Argc();  i++) {
-		Com_Printf("%d: %s\n", i, Cmd_Argv(i));
-	}
-}
-#endif
 
 //==========================================================================
 
+cvar_t	*cl_upspeed;
+cvar_t	*cl_forwardspeed;
+cvar_t	*cl_sidespeed;
+
 cvar_t	*cl_yawspeed;
 cvar_t	*cl_pitchspeed;
 
@@ -333,7 +311,7 @@
 
 	//
 	// adjust for speed key / running
-	// the walking flag is to keep animations consistent
+	// the walking flag is to keep animations consistant
 	// even during acceleration and develeration
 	//
 	if ( in_speed.active ^ cl_run->integer ) {
@@ -372,16 +350,14 @@
 CL_MouseEvent
 =================
 */
-void CL_MouseEvent( int dx, int dy, int time, qboolean active ) {
-	if ( Key_GetCatcher( ) & KEYCATCH_UI ) {
-		VM_Call( uivm, UI_MOUSE_EVENT, dx, dy, active );
-	} else if (Key_GetCatcher( ) & KEYCATCH_CGAME) {
-		VM_Call (cgvm, CG_MOUSE_EVENT, dx, dy, active );
+void CL_MouseEvent( int dx, int dy, int time ) {
+	if ( cls.keyCatchers & KEYCATCH_UI ) {
+		VM_Call( uivm, UI_MOUSE_EVENT, dx, dy );
+	} else if (cls.keyCatchers & KEYCATCH_CGAME) {
+		VM_Call (cgvm, CG_MOUSE_EVENT, dx, dy);
 	} else {
-		if (active) {
-			cl.mouseDx[cl.mouseIndex] += dx;
-			cl.mouseDy[cl.mouseIndex] += dy;
-		}
+		cl.mouseDx[cl.mouseIndex] += dx;
+		cl.mouseDy[cl.mouseIndex] += dy;
 	}
 }
 
@@ -405,15 +381,13 @@
 =================
 */
 void CL_JoystickMove( usercmd_t *cmd ) {
+	int		movespeed;
 	float	anglespeed;
 
-	float yaw     = j_yaw->value     * cl.joystickAxis[j_yaw_axis->integer];
-	float right   = j_side->value    * cl.joystickAxis[j_side_axis->integer];
-	float forward = j_forward->value * cl.joystickAxis[j_forward_axis->integer];
-	float pitch   = j_pitch->value   * cl.joystickAxis[j_pitch_axis->integer];
-	float up      = j_up->value      * cl.joystickAxis[j_up_axis->integer];
-
-	if ( !(in_speed.active ^ cl_run->integer) ) {
+	if ( in_speed.active ^ cl_run->integer ) {
+		movespeed = 2;
+	} else {
+		movespeed = 1;
 		cmd->buttons |= BUTTON_WALKING;
 	}
 
@@ -424,22 +398,18 @@
 	}
 
 	if ( !in_strafe.active ) {
-		cl.viewangles[YAW] += anglespeed * yaw;
-		cmd->rightmove = ClampChar( cmd->rightmove + (int)right );
+		cl.viewangles[YAW] += anglespeed * cl_yawspeed->value * cl.joystickAxis[AXIS_SIDE];
 	} else {
-		cl.viewangles[YAW] += anglespeed * right;
-		cmd->rightmove = ClampChar( cmd->rightmove + (int)yaw );
+		cmd->rightmove = ClampChar( cmd->rightmove + cl.joystickAxis[AXIS_SIDE] );
 	}
 
 	if ( in_mlooking ) {
-		cl.viewangles[PITCH] += anglespeed * forward;
-		cmd->forwardmove = ClampChar( cmd->forwardmove + (int)pitch );
+		cl.viewangles[PITCH] += anglespeed * cl_pitchspeed->value * cl.joystickAxis[AXIS_FORWARD];
 	} else {
-		cl.viewangles[PITCH] += anglespeed * pitch;
-		cmd->forwardmove = ClampChar( cmd->forwardmove + (int)forward );
+		cmd->forwardmove = ClampChar( cmd->forwardmove + cl.joystickAxis[AXIS_FORWARD] );
 	}
 
-	cmd->upmove = ClampChar( cmd->upmove + (int)up );
+	cmd->upmove = ClampChar( cmd->upmove + cl.joystickAxis[AXIS_UP] );
 }
 
 /*
@@ -447,88 +417,52 @@
 CL_MouseMove
 =================
 */
-
-void CL_MouseMove(usercmd_t *cmd)
-{
-	float mx, my;
+void CL_MouseMove( usercmd_t *cmd ) {
+	float	mx, my;
+	float	accelSensitivity;
+	float	rate;
 
 	// allow mouse smoothing
-	if (m_filter->integer)
-	{
-		mx = (cl.mouseDx[0] + cl.mouseDx[1]) * 0.5f;
-		my = (cl.mouseDy[0] + cl.mouseDy[1]) * 0.5f;
-	}
-	else
-	{
+	if ( m_filter->integer ) {
+		mx = ( cl.mouseDx[0] + cl.mouseDx[1] ) * 0.5;
+		my = ( cl.mouseDy[0] + cl.mouseDy[1] ) * 0.5;
+	} else {
 		mx = cl.mouseDx[cl.mouseIndex];
 		my = cl.mouseDy[cl.mouseIndex];
 	}
-	
 	cl.mouseIndex ^= 1;
 	cl.mouseDx[cl.mouseIndex] = 0;
 	cl.mouseDy[cl.mouseIndex] = 0;
 
-	if (mx == 0.0f && my == 0.0f)
-		return;
-	
-	if (cl_mouseAccel->value != 0.0f)
-	{
-		if(cl_mouseAccelStyle->integer == 0)
-		{
-			float accelSensitivity;
-			float rate;
-			
-			rate = sqrt(mx * mx + my * my) / (float) frame_msec;
-
-			accelSensitivity = cl_sensitivity->value + rate * cl_mouseAccel->value;
-			mx *= accelSensitivity;
-			my *= accelSensitivity;
-			
-			if(cl_showMouseRate->integer)
-				Com_Printf("rate: %f, accelSensitivity: %f\n", rate, accelSensitivity);
-		}
-		else
-		{
-			float rate[2];
-			float power[2];
-
-			// sensitivity remains pretty much unchanged at low speeds
-			// cl_mouseAccel is a power value to how the acceleration is shaped
-			// cl_mouseAccelOffset is the rate for which the acceleration will have doubled the non accelerated amplification
-			// NOTE: decouple the config cvars for independent acceleration setup along X and Y?
-
-			rate[0] = fabs(mx) / (float) frame_msec;
-			rate[1] = fabs(my) / (float) frame_msec;
-			power[0] = powf(rate[0] / cl_mouseAccelOffset->value, cl_mouseAccel->value);
-			power[1] = powf(rate[1] / cl_mouseAccelOffset->value, cl_mouseAccel->value);
+	rate = sqrt( mx * mx + my * my ) / (float)frame_msec;
+	accelSensitivity = cl_sensitivity->value + rate * cl_mouseAccel->value;
 
-			mx = cl_sensitivity->value * (mx + ((mx < 0) ? -power[0] : power[0]) * cl_mouseAccelOffset->value);
-			my = cl_sensitivity->value * (my + ((my < 0) ? -power[1] : power[1]) * cl_mouseAccelOffset->value);
+	// scale by FOV
+	accelSensitivity *= cl.cgameSensitivity;
 
-			if(cl_showMouseRate->integer)
-				Com_Printf("ratex: %f, ratey: %f, powx: %f, powy: %f\n", rate[0], rate[1], power[0], power[1]);
-		}
-	}
-	else
-	{
-		mx *= cl_sensitivity->value;
-		my *= cl_sensitivity->value;
+	if ( rate && cl_showMouseRate->integer ) {
+		Com_Printf( "%f : %f\n", rate, accelSensitivity );
 	}
 
-	// ingame FOV
-	mx *= cl.cgameSensitivity;
-	my *= cl.cgameSensitivity;
+	mx *= accelSensitivity;
+	my *= accelSensitivity;
+
+	if (!mx && !my) {
+		return;
+	}
 
 	// add mouse X/Y movement to cmd
-	if(in_strafe.active)
-		cmd->rightmove = ClampChar(cmd->rightmove + m_side->value * mx);
-	else
+	if ( in_strafe.active ) {
+		cmd->rightmove = ClampChar( cmd->rightmove + m_side->value * mx );
+	} else {
 		cl.viewangles[YAW] -= m_yaw->value * mx;
+	}
 
-	if ((in_mlooking || cl_freelook->integer) && !in_strafe.active)
+	if ( (in_mlooking || cl_freelook->integer) && !in_strafe.active ) {
 		cl.viewangles[PITCH] += m_pitch->value * my;
-	else
-		cmd->forwardmove = ClampChar(cmd->forwardmove - m_forward->value * my);
+	} else {
+		cmd->forwardmove = ClampChar( cmd->forwardmove - m_forward->value * my );
+	}
 }
 
 
@@ -552,13 +486,13 @@
 		in_buttons[i].wasPressed = qfalse;
 	}
 
-	if ( Key_GetCatcher( ) ) {
+	if ( cls.keyCatchers ) {
 		cmd->buttons |= BUTTON_TALK;
 	}
 
 	// allow the game to know if any key at all is
 	// currently pressed, even if it isn't bound to anything
-	if ( anykeydown && Key_GetCatcher( ) == 0 ) {
+	if ( anykeydown && !cls.keyCatchers ) {
 		cmd->buttons |= BUTTON_ANY;
 	}
 }
@@ -625,10 +559,10 @@
 	// draw debug graphs of turning for mouse testing
 	if ( cl_debugMove->integer ) {
 		if ( cl_debugMove->integer == 1 ) {
-			SCR_DebugGraph( fabs(cl.viewangles[YAW] - oldAngles[YAW]) );
+			SCR_DebugGraph( abs(cl.viewangles[YAW] - oldAngles[YAW]), 0 );
 		}
 		if ( cl_debugMove->integer == 2 ) {
-			SCR_DebugGraph( fabs(cl.viewangles[PITCH] - oldAngles[PITCH]) );
+			SCR_DebugGraph( abs(cl.viewangles[PITCH] - oldAngles[PITCH]), 0 );
 		}
 	}
 
@@ -644,21 +578,16 @@
 =================
 */
 void CL_CreateNewCommands( void ) {
+	usercmd_t	*cmd;
 	int			cmdNum;
 
 	// no need to create usercmds until we have a gamestate
-	if ( clc.state < CA_PRIMED ) {
+	if ( cls.state < CA_PRIMED ) {
 		return;
 	}
 
 	frame_msec = com_frameTime - old_com_frameTime;
 
-	// if running over 1000fps, act as if each frame is 1ms
-	// prevents divisions by zero
-	if ( frame_msec < 1 ) {
-		frame_msec = 1;
-	}
-
 	// if running less than 5fps, truncate the extra time to prevent
 	// unexpected moves after a hitch
 	if ( frame_msec > 200 ) {
@@ -671,6 +600,7 @@
 	cl.cmdNumber++;
 	cmdNum = cl.cmdNumber & CMD_MASK;
 	cl.cmds[cmdNum] = CL_CreateCmd ();
+	cmd = &cl.cmds[cmdNum];
 }
 
 /*
@@ -689,7 +619,7 @@
 	int		delta;
 
 	// don't send anything if playing back a demo
-	if ( clc.demoplaying || clc.state == CA_CINEMATIC ) {
+	if ( clc.demoplaying || cls.state == CA_CINEMATIC ) {
 		return qfalse;
 	}
 
@@ -701,8 +631,8 @@
 
 	// if we don't have a valid gamestate yet, only send
 	// one packet a second
-	if ( clc.state != CA_ACTIVE && 
-		clc.state != CA_PRIMED && 
+	if ( cls.state != CA_ACTIVE && 
+		cls.state != CA_PRIMED && 
 		!*clc.downloadTempName &&
 		cls.realtime - clc.lastPacketSentTime < 1000 ) {
 		return qfalse;
@@ -714,7 +644,7 @@
 	}
 
 	// send every frame for LAN
-	if ( cl_lanForcePackets->integer && Sys_IsLANAddress( clc.netchan.remoteAddress ) ) {
+	if ( Sys_IsLANAddress( clc.netchan.remoteAddress ) ) {
 		return qtrue;
 	}
 
@@ -766,7 +696,7 @@
 	int			count, key;
 
 	// don't send anything if playing back a demo
-	if ( clc.demoplaying || clc.state == CA_CINEMATIC ) {
+	if ( clc.demoplaying || cls.state == CA_CINEMATIC ) {
 		return;
 	}
 
@@ -809,58 +739,6 @@
 		count = MAX_PACKET_USERCMDS;
 		Com_Printf("MAX_PACKET_USERCMDS\n");
 	}
-
-#ifdef USE_VOIP
-	if (clc.voipOutgoingDataSize > 0)
-	{
-		if((clc.voipFlags & VOIP_SPATIAL) || Com_IsVoipTarget(clc.voipTargets, sizeof(clc.voipTargets), -1))
-		{
-			MSG_WriteByte (&buf, clc_voip);
-			MSG_WriteByte (&buf, clc.voipOutgoingGeneration);
-			MSG_WriteLong (&buf, clc.voipOutgoingSequence);
-			MSG_WriteByte (&buf, clc.voipOutgoingDataFrames);
-			MSG_WriteData (&buf, clc.voipTargets, sizeof(clc.voipTargets));
-			MSG_WriteByte(&buf, clc.voipFlags);
-			MSG_WriteShort (&buf, clc.voipOutgoingDataSize);
-			MSG_WriteData (&buf, clc.voipOutgoingData, clc.voipOutgoingDataSize);
-
-			// If we're recording a demo, we have to fake a server packet with
-			//  this VoIP data so it gets to disk; the server doesn't send it
-			//  back to us, and we might as well eliminate concerns about dropped
-			//  and misordered packets here.
-			if(clc.demorecording && !clc.demowaiting)
-			{
-				const int voipSize = clc.voipOutgoingDataSize;
-				msg_t fakemsg;
-				byte fakedata[MAX_MSGLEN];
-				MSG_Init (&fakemsg, fakedata, sizeof (fakedata));
-				MSG_Bitstream (&fakemsg);
-				MSG_WriteLong (&fakemsg, clc.reliableAcknowledge);
-				MSG_WriteByte (&fakemsg, svc_voip);
-				MSG_WriteShort (&fakemsg, clc.clientNum);
-				MSG_WriteByte (&fakemsg, clc.voipOutgoingGeneration);
-				MSG_WriteLong (&fakemsg, clc.voipOutgoingSequence);
-				MSG_WriteByte (&fakemsg, clc.voipOutgoingDataFrames);
-				MSG_WriteShort (&fakemsg, clc.voipOutgoingDataSize );
-				MSG_WriteBits (&fakemsg, clc.voipFlags, VOIP_FLAGCNT);
-				MSG_WriteData (&fakemsg, clc.voipOutgoingData, voipSize);
-				MSG_WriteByte (&fakemsg, svc_EOF);
-				CL_WriteDemoMessage (&fakemsg, 0);
-			}
-
-			clc.voipOutgoingSequence += clc.voipOutgoingDataFrames;
-			clc.voipOutgoingDataSize = 0;
-			clc.voipOutgoingDataFrames = 0;
-		}
-		else
-		{
-			// We have data, but no targets. Silently discard all data
-			clc.voipOutgoingDataSize = 0;
-			clc.voipOutgoingDataFrames = 0;
-		}
-	}
-#endif
-
 	if ( count >= 1 ) {
 		if ( cl_showSend->integer ) {
 			Com_Printf( "(%i)", count );
@@ -882,10 +760,7 @@
 		// also use the message acknowledge
 		key ^= clc.serverMessageSequence;
 		// also use the last acknowledged server command in the key
-		key ^= MSG_HashKey(clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1) ], 32);
-
-		// testing hash
-		//Com_Printf("^5hash: %x  '%s'\n", MSG_HashKey(clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1) ], 32), clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1)]);
+		key ^= Com_HashKey(clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1) ], 32);
 
 		// write all the commands, including the predicted command
 		for ( i = 0 ; i < count ; i++ ) {
@@ -909,7 +784,17 @@
 		Com_Printf( "%i ", buf.cursize );
 	}
 
-	CL_Netchan_Transmit (&clc.netchan, &buf);
+	CL_Netchan_Transmit (&clc.netchan, &buf);	
+
+	// clients never really should have messages large enough
+	// to fragment, but in case they do, fire them all off
+	// at once
+	// TTimo: this causes a packet burst, which is bad karma for winsock
+	// added a WARNING message, we'll see if there are legit situations where this happens
+	while ( clc.netchan.unsentFragments ) {
+		Com_DPrintf( "WARNING: #462 unsent fragments (not supposed to happen!)\n" );
+		CL_Netchan_TransmitNextFragment( &clc.netchan );
+	}
 }
 
 /*
@@ -921,7 +806,7 @@
 */
 void CL_SendCmd( void ) {
 	// don't send any message if not connected
-	if ( clc.state < CA_CONNECTED ) {
+	if ( cls.state < CA_CONNECTED ) {
 		return;
 	}
 
@@ -1011,87 +896,6 @@
 	Cmd_AddCommand ("+mlook", IN_MLookDown);
 	Cmd_AddCommand ("-mlook", IN_MLookUp);
 
-#ifdef USE_VOIP
-	Cmd_AddCommand ("+voiprecord", IN_VoipRecordDown);
-	Cmd_AddCommand ("-voiprecord", IN_VoipRecordUp);
-#endif
-
-	//Cmd_AddCommand ("+vstr", IN_PlusVstr);
-
 	cl_nodelta = Cvar_Get ("cl_nodelta", "0", 0);
 	cl_debugMove = Cvar_Get ("cl_debugMove", "0", 0);
 }
-
-/*
-============
-CL_ShutdownInput
-============
-*/
-void CL_ShutdownInput(void)
-{
-	Cmd_RemoveCommand("centerview");
-
-	Cmd_RemoveCommand("+moveup");
-	Cmd_RemoveCommand("-moveup");
-	Cmd_RemoveCommand("+movedown");
-	Cmd_RemoveCommand("-movedown");
-	Cmd_RemoveCommand("+left");
-	Cmd_RemoveCommand("-left");
-	Cmd_RemoveCommand("+right");
-	Cmd_RemoveCommand("-right");
-	Cmd_RemoveCommand("+forward");
-	Cmd_RemoveCommand("-forward");
-	Cmd_RemoveCommand("+back");
-	Cmd_RemoveCommand("-back");
-	Cmd_RemoveCommand("+lookup");
-	Cmd_RemoveCommand("-lookup");
-	Cmd_RemoveCommand("+lookdown");
-	Cmd_RemoveCommand("-lookdown");
-	Cmd_RemoveCommand("+strafe");
-	Cmd_RemoveCommand("-strafe");
-	Cmd_RemoveCommand("+moveleft");
-	Cmd_RemoveCommand("-moveleft");
-	Cmd_RemoveCommand("+moveright");
-	Cmd_RemoveCommand("-moveright");
-	Cmd_RemoveCommand("+speed");
-	Cmd_RemoveCommand("-speed");
-	Cmd_RemoveCommand("+attack");
-	Cmd_RemoveCommand("-attack");
-	Cmd_RemoveCommand("+button0");
-	Cmd_RemoveCommand("-button0");
-	Cmd_RemoveCommand("+button1");
-	Cmd_RemoveCommand("-button1");
-	Cmd_RemoveCommand("+button2");
-	Cmd_RemoveCommand("-button2");
-	Cmd_RemoveCommand("+button3");
-	Cmd_RemoveCommand("-button3");
-	Cmd_RemoveCommand("+button4");
-	Cmd_RemoveCommand("-button4");
-	Cmd_RemoveCommand("+button5");
-	Cmd_RemoveCommand("-button5");
-	Cmd_RemoveCommand("+button6");
-	Cmd_RemoveCommand("-button6");
-	Cmd_RemoveCommand("+button7");
-	Cmd_RemoveCommand("-button7");
-	Cmd_RemoveCommand("+button8");
-	Cmd_RemoveCommand("-button8");
-	Cmd_RemoveCommand("+button9");
-	Cmd_RemoveCommand("-button9");
-	Cmd_RemoveCommand("+button10");
-	Cmd_RemoveCommand("-button10");
-	Cmd_RemoveCommand("+button11");
-	Cmd_RemoveCommand("-button11");
-	Cmd_RemoveCommand("+button12");
-	Cmd_RemoveCommand("-button12");
-	Cmd_RemoveCommand("+button13");
-	Cmd_RemoveCommand("-button13");
-	Cmd_RemoveCommand("+button14");
-	Cmd_RemoveCommand("-button14");
-	Cmd_RemoveCommand("+mlook");
-	Cmd_RemoveCommand("-mlook");
-
-#ifdef USE_VOIP
-	Cmd_RemoveCommand("+voiprecord");
-	Cmd_RemoveCommand("-voiprecord");
-#endif
-}

```

### `ioquake3`  — sha256 `7847fc60cebe...`, 30392 bytes

_Diff stat: +10 / -30 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_input.c	2026-04-16 20:02:25.170217200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\ioquake3\code\client\cl_input.c	2026-04-16 20:02:21.527568200 +0100
@@ -22,10 +22,9 @@
 // cl.input.c  -- builds an intended movement command to send to the server
 
 #include "client.h"
-#include "keys.h"
 
-static unsigned frame_msec;
-static int old_com_frameTime;
+unsigned	frame_msec;
+int			old_com_frameTime;
 
 /*
 ===============================================================================
@@ -272,18 +271,6 @@
 	cl.viewangles[PITCH] = -SHORT2ANGLE(cl.snap.ps.delta_angles[PITCH]);
 }
 
-#if 0
-void IN_PlusVstr (void)
-{
-	int i;
-
-	Com_Printf("vstr %d\n", Cmd_Argc());
-
-	for (i = 0;  i < Cmd_Argc();  i++) {
-		Com_Printf("%d: %s\n", i, Cmd_Argv(i));
-	}
-}
-#endif
 
 //==========================================================================
 
@@ -372,16 +359,14 @@
 CL_MouseEvent
 =================
 */
-void CL_MouseEvent( int dx, int dy, int time, qboolean active ) {
+void CL_MouseEvent( int dx, int dy, int time ) {
 	if ( Key_GetCatcher( ) & KEYCATCH_UI ) {
-		VM_Call( uivm, UI_MOUSE_EVENT, dx, dy, active );
+		VM_Call( uivm, UI_MOUSE_EVENT, dx, dy );
 	} else if (Key_GetCatcher( ) & KEYCATCH_CGAME) {
-		VM_Call (cgvm, CG_MOUSE_EVENT, dx, dy, active );
+		VM_Call (cgvm, CG_MOUSE_EVENT, dx, dy);
 	} else {
-		if (active) {
-			cl.mouseDx[cl.mouseIndex] += dx;
-			cl.mouseDy[cl.mouseIndex] += dy;
-		}
+		cl.mouseDx[cl.mouseIndex] += dx;
+		cl.mouseDy[cl.mouseIndex] += dy;
 	}
 }
 
@@ -815,7 +800,7 @@
 	{
 		if((clc.voipFlags & VOIP_SPATIAL) || Com_IsVoipTarget(clc.voipTargets, sizeof(clc.voipTargets), -1))
 		{
-			MSG_WriteByte (&buf, clc_voip);
+			MSG_WriteByte (&buf, clc_voipOpus);
 			MSG_WriteByte (&buf, clc.voipOutgoingGeneration);
 			MSG_WriteLong (&buf, clc.voipOutgoingSequence);
 			MSG_WriteByte (&buf, clc.voipOutgoingDataFrames);
@@ -836,7 +821,7 @@
 				MSG_Init (&fakemsg, fakedata, sizeof (fakedata));
 				MSG_Bitstream (&fakemsg);
 				MSG_WriteLong (&fakemsg, clc.reliableAcknowledge);
-				MSG_WriteByte (&fakemsg, svc_voip);
+				MSG_WriteByte (&fakemsg, svc_voipOpus);
 				MSG_WriteShort (&fakemsg, clc.clientNum);
 				MSG_WriteByte (&fakemsg, clc.voipOutgoingGeneration);
 				MSG_WriteLong (&fakemsg, clc.voipOutgoingSequence);
@@ -884,9 +869,6 @@
 		// also use the last acknowledged server command in the key
 		key ^= MSG_HashKey(clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1) ], 32);
 
-		// testing hash
-		//Com_Printf("^5hash: %x  '%s'\n", MSG_HashKey(clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1) ], 32), clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1)]);
-
 		// write all the commands, including the predicted command
 		for ( i = 0 ; i < count ; i++ ) {
 			j = (cl.cmdNumber - count + i + 1) & CMD_MASK;
@@ -909,7 +891,7 @@
 		Com_Printf( "%i ", buf.cursize );
 	}
 
-	CL_Netchan_Transmit (&clc.netchan, &buf);
+	CL_Netchan_Transmit (&clc.netchan, &buf);	
 }
 
 /*
@@ -1016,8 +998,6 @@
 	Cmd_AddCommand ("-voiprecord", IN_VoipRecordUp);
 #endif
 
-	//Cmd_AddCommand ("+vstr", IN_PlusVstr);
-
 	cl_nodelta = Cvar_Get ("cl_nodelta", "0", 0);
 	cl_debugMove = Cvar_Get ("cl_debugMove", "0", 0);
 }

```

### `quake3e`  — sha256 `0c8304d238b7...`, 33503 bytes

_Diff stat: +358 / -359 lines_

_(full diff is 38112 bytes — see files directly)_

### `openarena-engine`  — sha256 `350e702d943e...`, 30353 bytes

_Diff stat: +21 / -53 lines_

```diff
--- G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\client\cl_input.c	2026-04-16 20:02:25.170217200 +0100
+++ G:\QUAKE_LEGACY\tools\quake-source\openarena-engine\code\client\cl_input.c	2026-04-16 22:48:25.730201700 +0100
@@ -22,10 +22,9 @@
 // cl.input.c  -- builds an intended movement command to send to the server
 
 #include "client.h"
-#include "keys.h"
 
-static unsigned frame_msec;
-static int old_com_frameTime;
+unsigned	frame_msec;
+int			old_com_frameTime;
 
 /*
 ===============================================================================
@@ -272,18 +271,6 @@
 	cl.viewangles[PITCH] = -SHORT2ANGLE(cl.snap.ps.delta_angles[PITCH]);
 }
 
-#if 0
-void IN_PlusVstr (void)
-{
-	int i;
-
-	Com_Printf("vstr %d\n", Cmd_Argc());
-
-	for (i = 0;  i < Cmd_Argc();  i++) {
-		Com_Printf("%d: %s\n", i, Cmd_Argv(i));
-	}
-}
-#endif
 
 //==========================================================================
 
@@ -333,7 +320,7 @@
 
 	//
 	// adjust for speed key / running
-	// the walking flag is to keep animations consistent
+	// the walking flag is to keep animations consistant
 	// even during acceleration and develeration
 	//
 	if ( in_speed.active ^ cl_run->integer ) {
@@ -372,16 +359,14 @@
 CL_MouseEvent
 =================
 */
-void CL_MouseEvent( int dx, int dy, int time, qboolean active ) {
+void CL_MouseEvent( int dx, int dy, int time ) {
 	if ( Key_GetCatcher( ) & KEYCATCH_UI ) {
-		VM_Call( uivm, UI_MOUSE_EVENT, dx, dy, active );
+		VM_Call( uivm, UI_MOUSE_EVENT, dx, dy );
 	} else if (Key_GetCatcher( ) & KEYCATCH_CGAME) {
-		VM_Call (cgvm, CG_MOUSE_EVENT, dx, dy, active );
+		VM_Call (cgvm, CG_MOUSE_EVENT, dx, dy);
 	} else {
-		if (active) {
-			cl.mouseDx[cl.mouseIndex] += dx;
-			cl.mouseDy[cl.mouseIndex] += dy;
-		}
+		cl.mouseDx[cl.mouseIndex] += dx;
+		cl.mouseDy[cl.mouseIndex] += dy;
 	}
 }
 
@@ -407,12 +392,6 @@
 void CL_JoystickMove( usercmd_t *cmd ) {
 	float	anglespeed;
 
-	float yaw     = j_yaw->value     * cl.joystickAxis[j_yaw_axis->integer];
-	float right   = j_side->value    * cl.joystickAxis[j_side_axis->integer];
-	float forward = j_forward->value * cl.joystickAxis[j_forward_axis->integer];
-	float pitch   = j_pitch->value   * cl.joystickAxis[j_pitch_axis->integer];
-	float up      = j_up->value      * cl.joystickAxis[j_up_axis->integer];
-
 	if ( !(in_speed.active ^ cl_run->integer) ) {
 		cmd->buttons |= BUTTON_WALKING;
 	}
@@ -424,22 +403,22 @@
 	}
 
 	if ( !in_strafe.active ) {
-		cl.viewangles[YAW] += anglespeed * yaw;
-		cmd->rightmove = ClampChar( cmd->rightmove + (int)right );
+		cl.viewangles[YAW] += anglespeed * j_yaw->value * cl.joystickAxis[j_yaw_axis->integer];
+		cmd->rightmove = ClampChar( cmd->rightmove + (int) (j_side->value * cl.joystickAxis[j_side_axis->integer]) );
 	} else {
-		cl.viewangles[YAW] += anglespeed * right;
-		cmd->rightmove = ClampChar( cmd->rightmove + (int)yaw );
+		cl.viewangles[YAW] += anglespeed * j_side->value * cl.joystickAxis[j_side_axis->integer];
+		cmd->rightmove = ClampChar( cmd->rightmove + (int) (j_yaw->value * cl.joystickAxis[j_yaw_axis->integer]) );
 	}
 
 	if ( in_mlooking ) {
-		cl.viewangles[PITCH] += anglespeed * forward;
-		cmd->forwardmove = ClampChar( cmd->forwardmove + (int)pitch );
+		cl.viewangles[PITCH] += anglespeed * j_forward->value * cl.joystickAxis[j_forward_axis->integer];
+		cmd->forwardmove = ClampChar( cmd->forwardmove + (int) (j_pitch->value * cl.joystickAxis[j_pitch_axis->integer]) );
 	} else {
-		cl.viewangles[PITCH] += anglespeed * pitch;
-		cmd->forwardmove = ClampChar( cmd->forwardmove + (int)forward );
+		cl.viewangles[PITCH] += anglespeed * j_pitch->value * cl.joystickAxis[j_pitch_axis->integer];
+		cmd->forwardmove = ClampChar( cmd->forwardmove + (int) (j_forward->value * cl.joystickAxis[j_forward_axis->integer]) );
 	}
 
-	cmd->upmove = ClampChar( cmd->upmove + (int)up );
+	cmd->upmove = ClampChar( cmd->upmove + (int) (j_up->value * cl.joystickAxis[j_up_axis->integer]) );
 }
 
 /*
@@ -471,7 +450,7 @@
 	if (mx == 0.0f && my == 0.0f)
 		return;
 	
-	if (cl_mouseAccel->value != 0.0f)
+	if (cl_mouseAccel->value != 0.0f && cl_mouseAccelOffset->value > 0.0f)
 	{
 		if(cl_mouseAccelStyle->integer == 0)
 		{
@@ -625,10 +604,10 @@
 	// draw debug graphs of turning for mouse testing
 	if ( cl_debugMove->integer ) {
 		if ( cl_debugMove->integer == 1 ) {
-			SCR_DebugGraph( fabs(cl.viewangles[YAW] - oldAngles[YAW]) );
+			SCR_DebugGraph( abs(cl.viewangles[YAW] - oldAngles[YAW]) );
 		}
 		if ( cl_debugMove->integer == 2 ) {
-			SCR_DebugGraph( fabs(cl.viewangles[PITCH] - oldAngles[PITCH]) );
+			SCR_DebugGraph( abs(cl.viewangles[PITCH] - oldAngles[PITCH]) );
 		}
 	}
 
@@ -653,12 +632,6 @@
 
 	frame_msec = com_frameTime - old_com_frameTime;
 
-	// if running over 1000fps, act as if each frame is 1ms
-	// prevents divisions by zero
-	if ( frame_msec < 1 ) {
-		frame_msec = 1;
-	}
-
 	// if running less than 5fps, truncate the extra time to prevent
 	// unexpected moves after a hitch
 	if ( frame_msec > 200 ) {
@@ -884,9 +857,6 @@
 		// also use the last acknowledged server command in the key
 		key ^= MSG_HashKey(clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1) ], 32);
 
-		// testing hash
-		//Com_Printf("^5hash: %x  '%s'\n", MSG_HashKey(clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1) ], 32), clc.serverCommands[ clc.serverCommandSequence & (MAX_RELIABLE_COMMANDS-1)]);
-
 		// write all the commands, including the predicted command
 		for ( i = 0 ; i < count ; i++ ) {
 			j = (cl.cmdNumber - count + i + 1) & CMD_MASK;
@@ -909,7 +879,7 @@
 		Com_Printf( "%i ", buf.cursize );
 	}
 
-	CL_Netchan_Transmit (&clc.netchan, &buf);
+	CL_Netchan_Transmit (&clc.netchan, &buf);	
 }
 
 /*
@@ -1016,8 +986,6 @@
 	Cmd_AddCommand ("-voiprecord", IN_VoipRecordUp);
 #endif
 
-	//Cmd_AddCommand ("+vstr", IN_PlusVstr);
-
 	cl_nodelta = Cvar_Get ("cl_nodelta", "0", 0);
 	cl_debugMove = Cvar_Get ("cl_debugMove", "0", 0);
 }

```
