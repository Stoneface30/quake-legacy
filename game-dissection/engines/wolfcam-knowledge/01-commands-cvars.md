# 01 — Commands & Cvars (wolfcamql)

License: GPL-2.0 (wolfcamql) — extracted via static source scan, no inference.
Generated from: G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-src/

Scan method: Python walk over `code/` matching `Cmd_AddCommand(...)`, `trap_AddCommand(...)`, the
`cgame/cg_consolecmds.c:commands[]` table, cvar tables `cvarTable[]` in `cg_main.c`/`ui_main.c`,
`Cvar_Get(...)` and `trap_Cvar_Register(...)` calls. Commented-out (`//`) lines excluded.

Totals: **449 command registrations**, **1983 cvar registrations** (a cvar
registered in several files appears once per site).

ioquake3 baseline loaded from `G:/QUAKE_LEGACY/tools/quake-source/ioquake3/code/` (723 distinct cvar names). Any name not present there is tagged wolfcam-specific.

---

## A. Console Commands

Handler column: C function bound to the command, or `(cgame forward)` for `trap_AddCommand` entries
where the cgame module merely forwards the token to the server.

| Name | Handler | Source |
|------|---------|--------|
| `+acc` | `CG_AccStatsDown_f` | cgame/cg_consolecmds.c:8423 |
| `+attack` | `IN_Button0Down` | client/cl_input.c:979 |
| `+back` | `IN_BackDown` | client/cl_input.c:965 |
| `+button0` | `IN_Button0Down` | client/cl_input.c:981 |
| `+button1` | `IN_Button1Down` | client/cl_input.c:983 |
| `+button10` | `IN_Button10Down` | client/cl_input.c:1001 |
| `+button11` | `IN_Button11Down` | client/cl_input.c:1003 |
| `+button12` | `IN_Button12Down` | client/cl_input.c:1005 |
| `+button13` | `IN_Button13Down` | client/cl_input.c:1007 |
| `+button14` | `IN_Button14Down` | client/cl_input.c:1009 |
| `+button2` | `IN_Button2Down` | client/cl_input.c:985 |
| `+button3` | `IN_Button3Down` | client/cl_input.c:987 |
| `+button4` | `IN_Button4Down` | client/cl_input.c:989 |
| `+button5` | `IN_Button5Down` | client/cl_input.c:991 |
| `+button6` | `IN_Button6Down` | client/cl_input.c:993 |
| `+button7` | `IN_Button7Down` | client/cl_input.c:995 |
| `+button8` | `IN_Button8Down` | client/cl_input.c:997 |
| `+button9` | `IN_Button9Down` | client/cl_input.c:999 |
| `+chat` | `CG_ChatDown_f` | cgame/cg_consolecmds.c:8561 |
| `+forward` | `IN_ForwardDown` | client/cl_input.c:963 |
| `+info` | `CG_InfoDown_f` | cgame/cg_consolecmds.c:8544 |
| `+left` | `IN_LeftDown` | client/cl_input.c:959 |
| `+lookdown` | `IN_LookdownDown` | client/cl_input.c:969 |
| `+lookup` | `IN_LookupDown` | client/cl_input.c:967 |
| `+mlook` | `IN_MLookDown` | client/cl_input.c:1011 |
| `+mouseseek` | `CG_MouseSeekDown_f` | cgame/cg_consolecmds.c:8558 |
| `+movedown` | `IN_DownDown` | client/cl_input.c:957 |
| `+moveleft` | `IN_MoveleftDown` | client/cl_input.c:973 |
| `+moveright` | `IN_MoverightDown` | client/cl_input.c:975 |
| `+moveup` | `IN_UpDown` | client/cl_input.c:955 |
| `+right` | `IN_RightDown` | client/cl_input.c:961 |
| `+scores` | `CG_ScoresDown_f` | cgame/cg_consolecmds.c:8421 |
| `+speed` | `IN_SpeedDown` | client/cl_input.c:977 |
| `+strafe` | `IN_StrafeDown` | client/cl_input.c:971 |
| `+voiprecord` | `IN_VoipRecordDown` | client/cl_input.c:1015 |
| `+zoom` | `CG_ZoomDown_f` | cgame/cg_consolecmds.c:8425 |
| `-acc` | `CG_AccStatsUp_f` | cgame/cg_consolecmds.c:8424 |
| `-attack` | `IN_Button0Up` | client/cl_input.c:980 |
| `-back` | `IN_BackUp` | client/cl_input.c:966 |
| `-button0` | `IN_Button0Up` | client/cl_input.c:982 |
| `-button1` | `IN_Button1Up` | client/cl_input.c:984 |
| `-button10` | `IN_Button10Up` | client/cl_input.c:1002 |
| `-button11` | `IN_Button11Up` | client/cl_input.c:1004 |
| `-button12` | `IN_Button12Up` | client/cl_input.c:1006 |
| `-button13` | `IN_Button13Up` | client/cl_input.c:1008 |
| `-button14` | `IN_Button14Up` | client/cl_input.c:1010 |
| `-button2` | `IN_Button2Up` | client/cl_input.c:986 |
| `-button3` | `IN_Button3Up` | client/cl_input.c:988 |
| `-button4` | `IN_Button4Up` | client/cl_input.c:990 |
| `-button5` | `IN_Button5Up` | client/cl_input.c:992 |
| `-button6` | `IN_Button6Up` | client/cl_input.c:994 |
| `-button7` | `IN_Button7Up` | client/cl_input.c:996 |
| `-button8` | `IN_Button8Up` | client/cl_input.c:998 |
| `-button9` | `IN_Button9Up` | client/cl_input.c:1000 |
| `-chat` | `CG_ChatUp_f` | cgame/cg_consolecmds.c:8562 |
| `-forward` | `IN_ForwardUp` | client/cl_input.c:964 |
| `-info` | `CG_InfoUp_f` | cgame/cg_consolecmds.c:8545 |
| `-left` | `IN_LeftUp` | client/cl_input.c:960 |
| `-lookdown` | `IN_LookdownUp` | client/cl_input.c:970 |
| `-lookup` | `IN_LookupUp` | client/cl_input.c:968 |
| `-mlook` | `IN_MLookUp` | client/cl_input.c:1012 |
| `-mouseseek` | `CG_MouseSeekUp_f` | cgame/cg_consolecmds.c:8559 |
| `-movedown` | `IN_DownUp` | client/cl_input.c:958 |
| `-moveleft` | `IN_MoveleftUp` | client/cl_input.c:974 |
| `-moveright` | `IN_MoverightUp` | client/cl_input.c:976 |
| `-moveup` | `IN_UpUp` | client/cl_input.c:956 |
| `-right` | `IN_RightUp` | client/cl_input.c:962 |
| `-scores` | `CG_ScoresUp_f` | cgame/cg_consolecmds.c:8422 |
| `-speed` | `IN_SpeedUp` | client/cl_input.c:978 |
| `-strafe` | `IN_StrafeUp` | client/cl_input.c:972 |
| `-voiprecord` | `IN_VoipRecordUp` | client/cl_input.c:1016 |
| `-zoom` | `CG_ZoomUp_f` | cgame/cg_consolecmds.c:8426 |
| `addbot` | `(cgame forward)` | cgame/cg_consolecmds.c:8676 |
| `addcamerapoint` | `CG_AddCameraPoint_f` | cgame/cg_consolecmds.c:8510 |
| `addchatline` | `CG_AddChatLine_f` | cgame/cg_consolecmds.c:8563 |
| `adddecal` | `CG_AddDecal_f` | cgame/cg_consolecmds.c:8586 |
| `addmirrorsurface` | `CG_AddMirrorSurface_f` | cgame/cg_consolecmds.c:8575 |
| `alias` | `Cmd_Alias_f` | qcommon/cmd.c:1320 |
| `at` | `CG_AddAtCommand_f` | cgame/cg_consolecmds.c:8546 |
| `backtrace` | `Sys_Backtrace_f` | sys/sys_main.c:366 |
| `banaddr` | `SV_BanAddr_f` | server/sv_ccmds.c:1701 |
| `banClient` | `SV_BanNum_f` | server/sv_ccmds.c:1668 |
| `bandel` | `SV_BanDel_f` | server/sv_ccmds.c:1703 |
| `banUser` | `SV_Ban_f` | server/sv_ccmds.c:1667 |
| `bind` | `Key_Bind_f` | client/cl_keys.c:1373 |
| `bindlist` | `Key_Bindlist_f` | client/cl_keys.c:1378 |
| `cadd` | `Cvar_Add_f` | qcommon/cvar.c:1641 |
| `callteamvote` | `(cgame forward)` | cgame/cg_consolecmds.c:8680 |
| `callvote` | `(cgame forward)` | cgame/cg_consolecmds.c:8678 |
| `camtracesave` | `CG_CamtraceSave_f` | cgame/cg_consolecmds.c:8515 |
| `cconfigstrings` | `CG_ConfigStrings_f` | cgame/cg_consolecmds.c:8567 |
| `ccopy` | `Cvar_Copy_f` | qcommon/cvar.c:1639 |
| `cdiv` | `Cvar_Divide_f` | qcommon/cvar.c:1647 |
| `centerprint` | `CG_ConsoleCenterPrint_f` | cgame/cg_consolecmds.c:8603 |
| `centerroll` | `CG_CenterRoll_f` | cgame/cg_consolecmds.c:8507 |
| `centerview` | `IN_CenterView` | client/cl_input.c:953 |
| `changeconfigstring` | `CG_ChangeConfigString_f` | cgame/cg_consolecmds.c:8566 |
| `changefield` | `CG_ChangeSelectedField_f` | cgame/cg_consolecmds.c:8533 |
| `changeVectors` | `MSG_ReportChangeVectors_f` | qcommon/common.c:3048 |
| `chase` | `CG_Chase_f` | cgame/cg_consolecmds.c:8509 |
| `cinematic` | `CL_PlayCinematic_f` | client/cl_main.c:7157 |
| `cinematic_restart` | `CL_RestartCinematic_f` | client/cl_main.c:7158 |
| `cinematiclist` | `CL_ListCinematic_f` | client/cl_main.c:7159 |
| `clear` | `Con_Clear_f` | client/cl_console.c:523 |
| `clearallremappedshaders` | `R_ClearAllRemappedShaders_f` | renderergl1/tr_init.c:2003 |
| `clearallremappedshaders` | `R_ClearAllRemappedShaders_f` | renderergl2/tr_init.c:2198 |
| `clearat` | `CG_ClearAtCommands_f` | cgame/cg_consolecmds.c:8548 |
| `clearcamerapoints` | `CG_ClearCameraPoints_f` | cgame/cg_consolecmds.c:8511 |
| `clearcvarinterp` | `CG_ClearCvarInterp_f` | cgame/cg_consolecmds.c:8565 |
| `clearfragmessage` | `CG_ClearFragMessage_f` | cgame/cg_consolecmds.c:8489 |
| `clearfx` | `CG_ClearFX_f` | cgame/cg_consolecmds.c:8538 |
| `clearjumps` | `CG_ClearJumps_f` | cgame/cg_consolecmds.c:8557 |
| `clearremappedshader` | `CG_ClearRemappedShader_f` | cgame/cg_consolecmds.c:8572 |
| `clearscene` | `CG_ClearScene_f` | cgame/cg_consolecmds.c:8543 |
| `clientinfo` | `CL_Clientinfo_f` | client/cl_main.c:7149 |
| `clientkick` | `SV_KickNum_f` | server/sv_ccmds.c:1674 |
| `clientoverride` | `CG_ClientOverride_f` | cgame/cg_consolecmds.c:8540 |
| `cmd` | `CL_ForwardToServer_f` | client/cl_main.c:7147 |
| `cmdlist` | `Cmd_List_f` | qcommon/cmd.c:1313 |
| `cmul` | `Cvar_Multiply_f` | qcommon/cvar.c:1645 |
| `condump` | `Con_Dump_f` | client/cl_console.c:524 |
| `configstrings` | `CL_Configstrings_f` | client/cl_main.c:7148 |
| `confirmOrder` | `CG_ConfirmOrder_f` | cgame/cg_consolecmds.c:8444 |
| `connect` | `CL_Connect_f` | client/cl_main.c:7161 |
| `crash` | `Com_Crash_f` | qcommon/common.c:3148 |
| `createcolorskins` | `R_CreateColorSkins_f` | renderergl1/tr_init.c:1999 |
| `createcolorskins` | `R_CreateColorSkins_f` | renderergl2/tr_init.c:2194 |
| `csub` | `Cvar_Subtract_f` | qcommon/cvar.c:1643 |
| `cvar_modified` | `Cvar_ListModified_f` | qcommon/cvar.c:1669 |
| `cvar_restart` | `Cvar_Restart_f` | qcommon/cvar.c:1670 |
| `cvarinterp` | `CG_CvarInterp_f` | cgame/cg_consolecmds.c:8564 |
| `cvarlist` | `Cvar_List_f` | qcommon/cvar.c:1668 |
| `cvarsearch` | `Cvar_Search_f` | qcommon/cvar.c:1665 |
| `debugcpmamvd` | `CG_DebugCpmaMvd_f` | cgame/cg_consolecmds.c:8602 |
| `deletecamerapoint` | `CG_DeleteCameraPoint_f` | cgame/cg_consolecmds.c:8518 |
| `demo` | `CL_PlayDemo_f` | client/cl_main.c:7154 |
| `demo_scale` | `CG_DemoScale_f` | cgame/cg_consolecmds.c:8569 |
| `denyOrder` | `CG_DenyOrder_f` | cgame/cg_consolecmds.c:8445 |
| `devmap` | `SV_Map_f` | server/sv_ccmds.c:1684 |
| `devmapnext` | `SV_DevmapNext_f` | server/sv_ccmds.c:1707 |
| `devmapprev` | `SV_DevmapPrev_f` | server/sv_ccmds.c:1708 |
| `dir` | `FS_Dir_f` | qcommon/files.c:3781 |
| `disconnect` | `CL_Disconnect_f` | client/cl_main.c:7152 |
| `dof` | `CG_Q3mmeDemoDofCommand_f` | cgame/cg_consolecmds.c:8596 |
| `drawrawpath` | `CG_DrawRawPath_f` | cgame/cg_consolecmds.c:8508 |
| `dumpents` | `CG_DumpEnts_f` | cgame/cg_consolecmds.c:8576 |
| `dumpstats` | `CG_DumpStats_f` | cgame/cg_consolecmds.c:8498 |
| `dumpuser` | `SV_DumpUser_f` | server/sv_ccmds.c:1678 |
| `ecam` | `CG_ChangeSelectedCameraPoints_f` | cgame/cg_consolecmds.c:8522 |
| `echo` | `Cmd_Echo_f` | qcommon/cmd.c:1324 |
| `echopopup` | `CG_EchoPopup_f` | cgame/cg_consolecmds.c:8483 |
| `echopopupclear` | `CG_EchoPopupClear_f` | cgame/cg_consolecmds.c:8484 |
| `echopopupcvar` | `CG_EchoPopupCvar_f` | cgame/cg_consolecmds.c:8485 |
| `editcamerapoint` | `CG_EditCameraPoint_f` | cgame/cg_consolecmds.c:8520 |
| `entityfilter` | `CG_EntityFilter_f` | cgame/cg_consolecmds.c:8552 |
| `entityfreeze` | `CG_EntityFreeze_f` | cgame/cg_consolecmds.c:8554 |
| `error` | `Com_Error_f` | qcommon/common.c:3147 |
| `eventfilter` | `CG_EventFilter_f` | cgame/cg_consolecmds.c:8584 |
| `exceptaddr` | `SV_ExceptAddr_f` | server/sv_ccmds.c:1702 |
| `exceptdel` | `SV_ExceptDel_f` | server/sv_ccmds.c:1704 |
| `exec` | `Cmd_Exec_f` | qcommon/cmd.c:1314 |
| `exec_at_time` | `CG_ExecAtTime_f` | cgame/cg_consolecmds.c:8551 |
| `execq` | `Cmd_Exec_f` | qcommon/cmd.c:1316 |
| `exportCubemaps` | `R_ExportCubemaps_f` | renderergl2/tr_init.c:2193 |
| `fastforward` | `CL_FastForward_f` | client/cl_main.c:7183 |
| `fdir` | `FS_NewDir_f` | qcommon/files.c:3782 |
| `flushbans` | `SV_FlushBans_f` | server/sv_ccmds.c:1705 |
| `follow` | `Wolfcam_Follow_f` | cgame/cg_consolecmds.c:8471 |
| `follow` | `(cgame forward)` | cgame/cg_consolecmds.c:8672 |
| `follownext` | `(cgame forward)` | cgame/cg_consolecmds.c:8673 |
| `followprev` | `(cgame forward)` | cgame/cg_consolecmds.c:8674 |
| `fontlist` | `R_FontList_f` | renderergl1/tr_init.c:1993 |
| `fontlist` | `R_FontList_f` | renderergl2/tr_init.c:2186 |
| `fragforward` | `CG_FragForward_f` | cgame/cg_consolecmds.c:8502 |
| `freecam` | `CG_FreeCam_f` | cgame/cg_consolecmds.c:8478 |
| `freecamlookatplayer` | `CG_FreecamLookAtPlayer_f` | cgame/cg_consolecmds.c:8570 |
| `freecamsetpos` | `CG_SetViewPos_f` | cgame/cg_consolecmds.c:8480 |
| `freeze` | `Com_Freeze_f` | qcommon/common.c:3149 |
| `fs_openedList` | `CL_OpenedPK3List_f` | client/cl_main.c:7170 |
| `fs_referencedList` | `CL_ReferencedPK3List_f` | client/cl_main.c:7171 |
| `fxload` | `CG_FXLoad_f` | cgame/cg_consolecmds.c:8535 |
| `fxmath` | `CG_FXMath_f` | cgame/cg_consolecmds.c:8534 |
| `g_fov` | `CG_Gfov_f` | cgame/cg_consolecmds.c:8568 |
| `game_restart` | `Com_GameRestart_f` | qcommon/common.c:3051 |
| `gfxinfo` | `GfxInfo_f` | renderergl1/tr_init.c:1997 |
| `gfxinfo` | `GfxInfo_f` | renderergl2/tr_init.c:2190 |
| `gfxmeminfo` | `GfxMemInfo_f` | renderergl2/tr_init.c:2192 |
| `give` | `(cgame forward)` | cgame/cg_consolecmds.c:8666 |
| `globalservers` | `CL_GlobalServers_f` | client/cl_main.c:7164 |
| `god` | `(cgame forward)` | cgame/cg_consolecmds.c:8667 |
| `gotoad` | `CG_GotoAdvertisement_f` | cgame/cg_consolecmds.c:8539 |
| `gotoview` | `CG_GotoView_f` | cgame/cg_consolecmds.c:8493 |
| `gotoviewpointmark` | `CG_GotoViewPointMark_f` | cgame/cg_consolecmds.c:8525 |
| `heartbeat` | `SV_Heartbeat_f` | server/sv_ccmds.c:1662 |
| `hunklog` | `Hunk_Log` | qcommon/common.c:1782 |
| `hunksmalllog` | `Hunk_SmallLog` | qcommon/common.c:1783 |
| `idcamera` | `CG_idCamera_f` | cgame/cg_consolecmds.c:8466 |
| `ifeq` | `Cmd_Ifeq_f` | qcommon/cmd.c:1326 |
| `ifeqf` | `Cmd_Ifeqf_f` | qcommon/cmd.c:1333 |
| `ifgt` | `Cmd_Ifgt_f` | qcommon/cmd.c:1328 |
| `ifgte` | `Cmd_Ifgte_f` | qcommon/cmd.c:1329 |
| `ifgtef` | `Cmd_Ifgtef_f` | qcommon/cmd.c:1336 |
| `ifgtf` | `Cmd_Ifgtf_f` | qcommon/cmd.c:1335 |
| `iflt` | `Cmd_Iflt_f` | qcommon/cmd.c:1330 |
| `iflte` | `Cmd_Iflte_f` | qcommon/cmd.c:1331 |
| `ifltef` | `Cmd_Ifltef_f` | qcommon/cmd.c:1338 |
| `ifltf` | `Cmd_Ifltf_f` | qcommon/cmd.c:1337 |
| `ifneq` | `Cmd_Ifneq_f` | qcommon/cmd.c:1327 |
| `ifneqf` | `Cmd_Ifneqf_f` | qcommon/cmd.c:1334 |
| `imagelist` | `R_ImageList_f` | renderergl1/tr_init.c:1988 |
| `imagelist` | `R_ImageList_f` | renderergl2/tr_init.c:2181 |
| `in_restart` | `Sys_In_Restart_f` | sys/sys_main.c:367 |
| `kick` | `SV_Kick_f` | server/sv_ccmds.c:1663 |
| `kickall` | `SV_KickAll_f` | server/sv_ccmds.c:1672 |
| `kickbots` | `SV_KickBots_f` | server/sv_ccmds.c:1671 |
| `kicknum` | `SV_KickNum_f` | server/sv_ccmds.c:1673 |
| `kill` | `(cgame forward)` | cgame/cg_consolecmds.c:8653 |
| `killcountreset` | `CG_KillCountReset_f` | cgame/cg_consolecmds.c:8588 |
| `killserver` | `SV_KillServer_f` | server/sv_ccmds.c:1691 |
| `levelshot` | `(cgame forward)` | cgame/cg_consolecmds.c:8675 |
| `listat` | `CG_ListAtCommands_f` | cgame/cg_consolecmds.c:8547 |
| `listbans` | `SV_ListBans_f` | server/sv_ccmds.c:1700 |
| `listcvarchanges` | `Cvar_ListChanges_f` | qcommon/cvar.c:1661 |
| `listentities` | `CG_ListEntities_f` | cgame/cg_consolecmds.c:8486 |
| `listentityfilter` | `CG_ListEntityFilter_f` | cgame/cg_consolecmds.c:8553 |
| `listentityfreeze` | `CG_ListEntityFreeze_f` | cgame/cg_consolecmds.c:8555 |
| `listeventfilter` | `CG_ListEventFilter_f` | cgame/cg_consolecmds.c:8585 |
| `listfxscripts` | `CG_ListFxScripts_f` | cgame/cg_consolecmds.c:8581 |
| `listplayermodels` | `Wolfcam_List_Player_Models_f` | cgame/cg_consolecmds.c:8475 |
| `listremappedshaders` | `R_ListRemappedShaders_f` | renderergl1/tr_init.c:2002 |
| `listremappedshaders` | `R_ListRemappedShaders_f` | renderergl2/tr_init.c:2197 |
| `listtimeditems` | `CG_ListTimedItems_f` | cgame/cg_consolecmds.c:8476 |
| `loadcamera` | `CG_LoadCamera_f` | cgame/cg_consolecmds.c:8516 |
| `loaddefered` | `(cgame forward)` | cgame/cg_consolecmds.c:8684 |
| `loaddeferred` | `CG_LoadDeferredPlayers` | cgame/cg_consolecmds.c:8468 |
| `loadhud` | `CG_LoadHud_f` | cgame/cg_consolecmds.c:8439 |
| `loadmenu` | `CG_LoadMenu_f` | cgame/cg_consolecmds.c:8477 |
| `loadq3mmecamera` | `CG_LoadQ3mmeCamera_f` | cgame/cg_consolecmds.c:8595 |
| `loadq3mmedof` | `CG_LoadQ3mmeDof_f` | cgame/cg_consolecmds.c:8598 |
| `localents` | `CG_LocalEnts_f` | cgame/cg_consolecmds.c:8537 |
| `localservers` | `CL_LocalServers_f` | client/cl_main.c:7163 |
| `loop` | `CG_Loop_f` | cgame/cg_consolecmds.c:8501 |
| `map` | `SV_Map_f` | server/sv_ccmds.c:1681 |
| `map_restart` | `SV_MapRestart_f` | server/sv_ccmds.c:1679 |
| `meminfo` | `Com_Meminfo_f` | qcommon/common.c:1776 |
| `memoryremaining` | `Com_MemoryRemaining_f` | qcommon/common.c:1777 |
| `messagemode` | `Con_MessageMode_f` | client/cl_console.c:519 |
| `messagemode2` | `Con_MessageMode2_f` | client/cl_console.c:520 |
| `messagemode3` | `Con_MessageMode3_f` | client/cl_console.c:521 |
| `messagemode4` | `Con_MessageMode4_f` | client/cl_console.c:522 |
| `minimize` | `GLimp_Minimize` | renderergl1/tr_init.c:1998 |
| `minimize` | `GLimp_Minimize` | renderergl2/tr_init.c:2191 |
| `modelist` | `R_ModeList_f` | renderergl1/tr_init.c:1992 |
| `modelist` | `R_ModeList_f` | renderergl2/tr_init.c:2185 |
| `modellist` | `R_Modellist_f` | renderergl1/tr_init.c:1991 |
| `modellist` | `R_Modellist_f` | renderergl2/tr_init.c:2184 |
| `move` | `CG_Move_f` | cgame/cg_consolecmds.c:8573 |
| `moveoffset` | `CG_MoveOffset_f` | cgame/cg_consolecmds.c:8574 |
| `music` | `S_Music_f` | client/snd_main.c:588 |
| `net_restart` | `NET_Restart_f` | qcommon/net_ip.c:1596 |
| `nextfield` | `CG_SelectNextField_f` | cgame/cg_consolecmds.c:8531 |
| `nextframe` | `CG_TestModelNextFrame_f` | cgame/cg_consolecmds.c:8416 |
| `nextOrder` | `CG_NextOrder_f` | cgame/cg_consolecmds.c:8443 |
| `nextskin` | `CG_TestModelNextSkin_f` | cgame/cg_consolecmds.c:8418 |
| `nextTeamMember` | `CG_NextTeamMember_f` | cgame/cg_consolecmds.c:8441 |
| `noclip` | `(cgame forward)` | cgame/cg_consolecmds.c:8669 |
| `notarget` | `(cgame forward)` | cgame/cg_consolecmds.c:8668 |
| `path` | `FS_Path_f` | qcommon/files.c:3780 |
| `pause` | `CL_Pause_f` | client/cl_main.c:7189 |
| `ping` | `CL_Ping_f` | client/cl_main.c:7167 |
| `play` | `S_Play_f` | client/snd_main.c:587 |
| `playcamera` | `CG_PlayCamera_f` | cgame/cg_consolecmds.c:8512 |
| `players` | `Wolfcam_Players_f` | cgame/cg_consolecmds.c:8469 |
| `playersw` | `Wolfcam_Playersw_f` | cgame/cg_consolecmds.c:8470 |
| `playpath` | `CG_PlayPath_f` | cgame/cg_consolecmds.c:8505 |
| `playq3mmecamera` | `CG_PlayQ3mmeCamera_f` | cgame/cg_consolecmds.c:8592 |
| `pov` | `CL_Pov_f` | client/cl_main.c:7194 |
| `prevfield` | `CG_SelectPrevField_f` | cgame/cg_consolecmds.c:8532 |
| `prevframe` | `CG_TestModelPrevFrame_f` | cgame/cg_consolecmds.c:8417 |
| `prevskin` | `CG_TestModelPrevSkin_f` | cgame/cg_consolecmds.c:8419 |
| `prevTeamMember` | `CG_PrevTeamMember_f` | cgame/cg_consolecmds.c:8442 |
| `print` | `Cvar_Print_f` | qcommon/cvar.c:1636 |
| `printdatadir` | `CL_PrintDataDir_f` | client/cl_main.c:7191 |
| `printdirvector` | `CG_PrintDirVector_f` | cgame/cg_consolecmds.c:8582 |
| `printentitydistance` | `CG_PrintEntityDistance_f` | cgame/cg_consolecmds.c:8589 |
| `printentitystate` | `CG_PrintEntityState_f` | cgame/cg_consolecmds.c:8487 |
| `printjumps` | `CG_PrintJumps_f` | cgame/cg_consolecmds.c:8556 |
| `printlegsinfo` | `CG_PrintLegsInfo_f` | cgame/cg_consolecmds.c:8560 |
| `printnextentitystate` | `CG_PrintNextEntityState_f` | cgame/cg_consolecmds.c:8488 |
| `printplayerstate` | `CG_PrintPlayerState_f` | cgame/cg_consolecmds.c:8542 |
| `printtime` | `CG_PrintTime_f` | cgame/cg_consolecmds.c:8587 |
| `printviewparms` | `R_PrintViewParms_f` | renderergl1/tr_init.c:2000 |
| `printviewparms` | `R_PrintViewParms_f` | renderergl2/tr_init.c:2195 |
| `q3mmecamera` | `CG_Q3mmeDemoCameraCommand_f` | cgame/cg_consolecmds.c:8590 |
| `quit` | `Com_Quit_f` | qcommon/common.c:3047 |
| `rcon` | `CL_Rcon_f` | client/cl_main.c:7165 |
| `reconnect` | `CL_Reconnect_f` | client/cl_main.c:7162 |
| `record` | `CL_Record_f` | client/cl_main.c:7153 |
| `recordpath` | `CG_RecordPath_f` | cgame/cg_consolecmds.c:8504 |
| `rehashbans` | `SV_RehashBans_f` | server/sv_ccmds.c:1699 |
| `remaplasttwoshaders` | `R_RemapLastTwoShaders_f` | renderergl1/tr_init.c:2001 |
| `remaplasttwoshaders` | `R_RemapLastTwoShaders_f` | renderergl2/tr_init.c:2196 |
| `remapshader` | `CG_RemapShader_f` | cgame/cg_consolecmds.c:8571 |
| `removeat` | `CG_RemoveAtCommand_f` | cgame/cg_consolecmds.c:8549 |
| `reset` | `Cvar_Reset_f` | qcommon/cvar.c:1657 |
| `reseta` | `Cvar_CvarResetAllMatching_f` | qcommon/cvar.c:1663 |
| `resetcenterprinttime` | `CG_ResetCenterPrintTime_f` | cgame/cg_consolecmds.c:8604 |
| `rewind` | `CL_Rewind_f` | client/cl_main.c:7182 |
| `runfx` | `CG_RunFx_f` | cgame/cg_consolecmds.c:8578 |
| `runfxall` | `CG_RunFxAll_f` | cgame/cg_consolecmds.c:8580 |
| `runfxat` | `CG_RunFxAt_f` | cgame/cg_consolecmds.c:8579 |
| `s_info` | `S_SoundInfo` | client/snd_main.c:592 |
| `s_list` | `S_SoundList` | client/snd_main.c:590 |
| `s_stop` | `S_StopAllSounds` | client/snd_main.c:591 |
| `saveat` | `CG_SaveAtCommands_f` | cgame/cg_consolecmds.c:8550 |
| `savecamera` | `CG_SaveCamera_f` | cgame/cg_consolecmds.c:8514 |
| `saveq3mmecamera` | `CG_SaveQ3mmeCamera_f` | cgame/cg_consolecmds.c:8594 |
| `saveq3mmedof` | `CG_SaveQ3mmeDof_f` | cgame/cg_consolecmds.c:8597 |
| `say` | `(cgame forward)` | cgame/cg_consolecmds.c:8654 |
| `say` | `SV_ConSay_f` | server/sv_ccmds.c:1693 |
| `say_team` | `(cgame forward)` | cgame/cg_consolecmds.c:8655 |
| `sayto` | `CL_Sayto_f` | client/cl_main.c:7178 |
| `sayto` | `SV_ConSayto_f` | server/sv_ccmds.c:1695 |
| `scoresDown` | `CG_scrollScoresDown_f` | cgame/cg_consolecmds.c:8463 |
| `scoresUp` | `CG_scrollScoresUp_f` | cgame/cg_consolecmds.c:8464 |
| `screenshot` | `R_ScreenShot_f` | renderergl1/tr_init.c:1994 |
| `screenshot` | `R_ScreenShot_f` | renderergl2/tr_init.c:2187 |
| `screenshotJPEG` | `R_ScreenShotJPEG_f` | renderergl1/tr_init.c:1995 |
| `screenshotJPEG` | `R_ScreenShotJPEG_f` | renderergl2/tr_init.c:2188 |
| `screenshotPNG` | `R_ScreenShotPNG_f` | renderergl1/tr_init.c:1996 |
| `screenshotPNG` | `R_ScreenShotPNG_f` | renderergl2/tr_init.c:2189 |
| `sectorlist` | `SV_SectorList_f` | server/sv_ccmds.c:1680 |
| `seek` | `CL_Seek_f` | client/cl_main.c:7185 |
| `seekclock` | `CG_SeekClock_f` | cgame/cg_consolecmds.c:8482 |
| `seekend` | `CL_SeekEnd_f` | client/cl_main.c:7186 |
| `seeknext` | `CL_SeekNext_f` | client/cl_main.c:7187 |
| `seeknextround` | `CG_SeekNextRound_f` | cgame/cg_consolecmds.c:8600 |
| `seekprev` | `CL_SeekPrev_f` | client/cl_main.c:7188 |
| `seekprevround` | `CG_SeekPrevRound_f` | cgame/cg_consolecmds.c:8601 |
| `seekservertime` | `CL_SeekServerTime_f` | client/cl_main.c:7184 |
| `selectcamerapoint` | `CG_SelectCameraPoint_f` | cgame/cg_consolecmds.c:8517 |
| `serverinfo` | `SV_Serverinfo_f` | server/sv_ccmds.c:1676 |
| `serverstatus` | `CL_ServerStatus_f` | client/cl_main.c:7168 |
| `servertime` | `CG_ServerTime_f` | cgame/cg_consolecmds.c:8496 |
| `set` | `Cvar_Set_f` | qcommon/cvar.c:1649 |
| `seta` | `Cvar_Set_f` | qcommon/cvar.c:1655 |
| `setcolortable` | `CL_SetColorTable_f` | client/cl_main.c:7193 |
| `setenv` | `Com_Setenv_f` | qcommon/common.c:3046 |
| `setloopend` | `CG_SetLoopEnd_f` | cgame/cg_consolecmds.c:8500 |
| `setloopstart` | `CG_SetLoopStart_f` | cgame/cg_consolecmds.c:8499 |
| `sets` | `Cvar_Set_f` | qcommon/cvar.c:1651 |
| `setu` | `Cvar_Set_f` | qcommon/cvar.c:1653 |
| `setviewangles` | `CG_SetViewAngles_f` | cgame/cg_consolecmds.c:8481 |
| `setviewpointmark` | `CG_SetViewPointMark_f` | cgame/cg_consolecmds.c:8523 |
| `setviewpos` | `CG_SetViewPos_f` | cgame/cg_consolecmds.c:8479 |
| `setviewpos` | `(cgame forward)` | cgame/cg_consolecmds.c:8677 |
| `shaderlist` | `R_ShaderList_f` | renderergl1/tr_init.c:1989 |
| `shaderlist` | `R_ShaderList_f` | renderergl2/tr_init.c:2182 |
| `showip` | `CL_ShowIP_f` | client/cl_main.c:7169 |
| `sizedown` | `CG_SizeDown_f` | cgame/cg_consolecmds.c:8428 |
| `sizeup` | `CG_SizeUp_f` | cgame/cg_consolecmds.c:8427 |
| `skinlist` | `R_SkinList_f` | renderergl1/tr_init.c:1990 |
| `skinlist` | `R_SkinList_f` | renderergl2/tr_init.c:2183 |
| `snd_restart` | `CL_Snd_Restart_f` | client/cl_main.c:7150 |
| `spdevmap` | `SV_Map_f` | server/sv_ccmds.c:1688 |
| `spLose` | `CG_spLose_f` | cgame/cg_consolecmds.c:8461 |
| `spmap` | `SV_Map_f` | server/sv_ccmds.c:1686 |
| `spWin` | `CG_spWin_f` | cgame/cg_consolecmds.c:8460 |
| `stall` | `CL_Stall_f` | client/cl_main.c:7192 |
| `startOrbit` | `CG_StartOrbit_f` | cgame/cg_consolecmds.c:8465 |
| `stats` | `(cgame forward)` | cgame/cg_consolecmds.c:8682 |
| `status` | `SV_Status_f` | server/sv_ccmds.c:1675 |
| `stopcamera` | `CG_StopCamera_f` | cgame/cg_consolecmds.c:8513 |
| `stopdumpents` | `CG_StopDumpEnts_f` | cgame/cg_consolecmds.c:8577 |
| `stopidcamera` | `CG_idCameraStop_f` | cgame/cg_consolecmds.c:8467 |
| `stopmovement` | `CG_StopMovement_f` | cgame/cg_consolecmds.c:8495 |
| `stopmusic` | `S_StopMusic_f` | client/snd_main.c:589 |
| `stopplaypath` | `CG_StopPlayPath_f` | cgame/cg_consolecmds.c:8506 |
| `stopq3mmecamera` | `CG_StopQ3mmeCamera_f` | cgame/cg_consolecmds.c:8593 |
| `stoprecord` | `CL_StopRecord_f` | client/cl_main.c:7160 |
| `stopvideo` | `CL_StopVideo_f` | client/cl_main.c:7175 |
| `streamdemo` | `CL_StreamDemo_f` | client/cl_main.c:7156 |
| `systeminfo` | `SV_Systeminfo_f` | server/sv_ccmds.c:1677 |
| `taskCamp` | `CG_TaskCamp_f` | cgame/cg_consolecmds.c:8449 |
| `taskDefense` | `CG_TaskDefense_f` | cgame/cg_consolecmds.c:8447 |
| `taskEscort` | `CG_TaskEscort_f` | cgame/cg_consolecmds.c:8452 |
| `taskFollow` | `CG_TaskFollow_f` | cgame/cg_consolecmds.c:8450 |
| `taskOffense` | `CG_TaskOffense_f` | cgame/cg_consolecmds.c:8446 |
| `taskOwnFlag` | `CG_TaskOwnFlag_f` | cgame/cg_consolecmds.c:8454 |
| `taskPatrol` | `CG_TaskPatrol_f` | cgame/cg_consolecmds.c:8448 |
| `taskRetrieve` | `CG_TaskRetrieve_f` | cgame/cg_consolecmds.c:8451 |
| `taskSuicide` | `CG_TaskSuicide_f` | cgame/cg_consolecmds.c:8453 |
| `tauntDeathInsult` | `CG_TauntDeathInsult_f` | cgame/cg_consolecmds.c:8458 |
| `tauntGauntlet` | `CG_TauntGauntlet_f` | cgame/cg_consolecmds.c:8459 |
| `tauntKillInsult` | `CG_TauntKillInsult_f` | cgame/cg_consolecmds.c:8455 |
| `tauntPraise` | `CG_TauntPraise_f` | cgame/cg_consolecmds.c:8456 |
| `tauntTaunt` | `CG_TauntTaunt_f` | cgame/cg_consolecmds.c:8457 |
| `tcmd` | `CG_TargetCommand_f` | cgame/cg_consolecmds.c:8432 |
| `team` | `(cgame forward)` | cgame/cg_consolecmds.c:8671 |
| `teamtask` | `(cgame forward)` | cgame/cg_consolecmds.c:8683 |
| `teamvote` | `(cgame forward)` | cgame/cg_consolecmds.c:8681 |
| `tell` | `(cgame forward)` | cgame/cg_consolecmds.c:8656 |
| `tell` | `SV_ConTell_f` | server/sv_ccmds.c:1694 |
| `tell_attacker` | `CG_TellAttacker_f` | cgame/cg_consolecmds.c:8434 |
| `tell_target` | `CG_TellTarget_f` | cgame/cg_consolecmds.c:8433 |
| `testgun` | `CG_TestGun_f` | cgame/cg_consolecmds.c:8414 |
| `testmenu` | `CG_TestMenu_f` | cgame/cg_consolecmds.c:8541 |
| `testmodel` | `CG_TestModel_f` | cgame/cg_consolecmds.c:8415 |
| `toggle` | `Cvar_Toggle_f` | qcommon/cvar.c:1637 |
| `toggleconsole` | `Con_ToggleConsole_f` | client/cl_console.c:517 |
| `togglemenu` | `Con_ToggleMenu_f` | client/cl_console.c:518 |
| `touchFile` | `FS_TouchFile_f` | qcommon/files.c:3783 |
| `unalias` | `Cmd_Unalias_f` | qcommon/cmd.c:1322 |
| `unaliasall` | `Cmd_Unaliasall_f` | qcommon/cmd.c:1323 |
| `unbind` | `Key_Unbind_f` | client/cl_keys.c:1375 |
| `unbindall` | `Key_Unbindall_f` | client/cl_keys.c:1377 |
| `unset` | `Cvar_Unset_f` | qcommon/cvar.c:1659 |
| `vibrate` | `CG_Vibrate_f` | cgame/cg_consolecmds.c:8536 |
| `vid_restart` | `CL_Vid_Restart_f` | client/cl_main.c:7151 |
| `video` | `CL_Video_f` | client/cl_main.c:7174 |
| `view` | `CG_ViewEnt_f` | cgame/cg_consolecmds.c:8490 |
| `viewpos` | `CG_Viewpos_f` | cgame/cg_consolecmds.c:8420 |
| `viewunlockpitch` | `CG_ViewUnlockPitch_f` | cgame/cg_consolecmds.c:8492 |
| `viewunlockyaw` | `CG_ViewUnlockYaw_f` | cgame/cg_consolecmds.c:8491 |
| `vminfo` | `VM_VmInfo_f` | qcommon/vm.c:78 |
| `vmprofile` | `VM_VmProfile_f` | qcommon/vm.c:77 |
| `voip` | `CL_Voip_f` | client/cl_cgame.c:1829 |
| `vosay` | `(cgame forward)` | cgame/cg_consolecmds.c:8662 |
| `vosay_team` | `(cgame forward)` | cgame/cg_consolecmds.c:8663 |
| `vote` | `(cgame forward)` | cgame/cg_consolecmds.c:8679 |
| `votell` | `(cgame forward)` | cgame/cg_consolecmds.c:8664 |
| `vsay` | `(cgame forward)` | cgame/cg_consolecmds.c:8658 |
| `vsay_team` | `(cgame forward)` | cgame/cg_consolecmds.c:8659 |
| `vstr` | `Cmd_Vstr_f` | qcommon/cmd.c:1318 |
| `vtaunt` | `(cgame forward)` | cgame/cg_consolecmds.c:8661 |
| `vtell` | `(cgame forward)` | cgame/cg_consolecmds.c:8660 |
| `vtell_attacker` | `CG_VoiceTellAttacker_f` | cgame/cg_consolecmds.c:8437 |
| `vtell_target` | `CG_VoiceTellTarget_f` | cgame/cg_consolecmds.c:8436 |
| `wait` | `Cmd_Wait_f` | qcommon/cmd.c:1325 |
| `wcstats` | `Wolfcam_Weapon_Stats_f` | cgame/cg_consolecmds.c:8472 |
| `wcstatsall` | `Wolfcam_Weapon_Statsall_f` | cgame/cg_consolecmds.c:8473 |
| `wcstatsresetall` | `Wolfcam_Reset_Weapon_Stats_f` | cgame/cg_consolecmds.c:8474 |
| `weapnext` | `CG_NextWeapon_f` | cgame/cg_consolecmds.c:8429 |
| `weapon` | `CG_Weapon_f` | cgame/cg_consolecmds.c:8431 |
| `weapprev` | `CG_PrevWeapon_f` | cgame/cg_consolecmds.c:8430 |
| `where` | `(cgame forward)` | cgame/cg_consolecmds.c:8670 |
| `which` | `FS_Which_f` | qcommon/files.c:3784 |
| `writeconfig` | `Com_WriteConfig_f` | qcommon/common.c:3049 |
| `zonelog` | `Z_LogHeap` | qcommon/common.c:1779 |

*Total:* **449**

---

## B. Cvars — wolfcam-specific (NEW vs ioquake3)

Name starts with `wolfcam_`, `wc_`, `cg_draw2d`, OR name is absent from the ioquake3 baseline. Heuristic — some names may exist in ioq3 under a different module; verify before assuming absolute novelty.

| Name | Default | Flags | Source |
|------|---------|-------|--------|
| `cg_accWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:2241 |
| `cg_accX` | `450` | CVAR_ARCHIVE | cgame/cg_main.c:2239 |
| `cg_accY` | `100` | CVAR_ARCHIVE | cgame/cg_main.c:2240 |
| `cg_adShaderOverride` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2466 |
| `cg_allowLargeSprites` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2422 |
| `cg_allowServerOverride` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2499 |
| `cg_allowSpritePassThrough` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2423 |
| `cg_ambientSounds` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2058 |
| `cg_animationsIgnoreTimescale` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2410 |
| `cg_animationsRate` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2411 |
| `cg_attackDefendVoiceStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2522 |
| `cg_audioAnnouncer` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2203 |
| `cg_audioAnnouncerDominationPoint` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2218 |
| `cg_audioAnnouncerFlagStatus` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2211 |
| `cg_audioAnnouncerFragLimit` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2214 |
| `cg_audioAnnouncerLastStanding` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2217 |
| `cg_audioAnnouncerLead` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2212 |
| `cg_audioAnnouncerPowerup` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2219 |
| `cg_audioAnnouncerRewards` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2204 |
| `cg_audioAnnouncerRewardsFirst` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2205 |
| `cg_audioAnnouncerRound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2206 |
| `cg_audioAnnouncerRoundReward` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2207 |
| `cg_audioAnnouncerScore` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2216 |
| `cg_audioAnnouncerTeamVote` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2210 |
| `cg_audioAnnouncerTimeLimit` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2213 |
| `cg_audioAnnouncerVote` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2209 |
| `cg_audioAnnouncerWarmup` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2208 |
| `cg_audioAnnouncerWin` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2215 |
| `cg_autoChaseMissile` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1679 |
| `cg_autoChaseMissileFilter` | `gl rl pg bfg gh ng pl` | CVAR_ARCHIVE | cgame/cg_main.c:1680 |
| `cg_autoFontScaling` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1931 |
| `cg_autoFontScalingThreshold` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1932 |
| `cg_battleSuitKillCounter` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2462 |
| `cg_bleedTime` | `500` | CVAR_ARCHIVE | cgame/cg_main.c:1773 |
| `cg_blueTeamFlagColor` | `0x0000ff` | CVAR_ARCHIVE | cgame/cg_main.c:2158 |
| `cg_blueTeamHeadColor` | `0x0000ff` | CVAR_ARCHIVE | cgame/cg_main.c:2149 |
| `cg_blueTeamHeadModel` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2145 |
| `cg_blueTeamHeadSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2146 |
| `cg_blueTeamLegsColor` | `0x0000ff` | CVAR_ARCHIVE | cgame/cg_main.c:2151 |
| `cg_blueTeamLegsSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2148 |
| `cg_blueTeamModel` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2144 |
| `cg_blueTeamRailColor1` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2152 |
| `cg_blueTeamRailColor2` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2153 |
| `cg_blueTeamRailItemColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2154 |
| `cg_blueTeamRailNudge` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2157 |
| `cg_blueTeamRailRings` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2156 |
| `cg_blueTeamTorsoColor` | `0x0000ff` | CVAR_ARCHIVE | cgame/cg_main.c:2150 |
| `cg_blueTeamTorsoSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2147 |
| `cg_buzzerSound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2505 |
| `cg_cameraAddUsePreviousValues` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2431 |
| `cg_cameraDebugPath` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2433 |
| `cg_cameraDefaultOriginType` | `splineBezier` | CVAR_ARCHIVE | cgame/cg_main.c:2432 |
| `cg_cameraQue` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2429 |
| `cg_cameraRewindTime` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2428 |
| `cg_cameraSmoothFactor` | `1.5` | CVAR_ARCHIVE | cgame/cg_main.c:2434 |
| `cg_cameraUpdateFreeCam` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2430 |
| `cg_chaseMovementKeys` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2617 |
| `cg_chaseThirdPerson` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2615 |
| `cg_chaseUpdateFreeCam` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2616 |
| `cg_chatBeep` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1980 |
| `cg_chatBeepMaxTime` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1981 |
| `cg_chatHistoryLength` | `15` | CVAR_ARCHIVE | cgame/cg_main.c:1979 |
| `cg_chatLines` | `10` | CVAR_ARCHIVE | cgame/cg_main.c:1978 |
| `cg_chatTime` | `5000` | CVAR_ARCHIVE | cgame/cg_main.c:1977 |
| `cg_checkForOfflineDemo` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2339 |
| `cg_clientOverrideIgnoreTeamSettings` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2448 |
| `cg_colorCodeUseForegroundAlpha` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2614 |
| `cg_colorCodeWhiteUseForegroundColor` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2613 |
| `cg_compMode` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2418 |
| `cg_cpmaInvisibility` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2621 |
| `cg_cpmaNtfBlueHeadColor` | `0x00a5ff` | CVAR_ARCHIVE | cgame/cg_main.c:2175 |
| `cg_cpmaNtfBlueLegsColor` | `0x0000ff` | CVAR_ARCHIVE | cgame/cg_main.c:2177 |
| `cg_cpmaNtfBlueRailColor` | `0x00a5ff` | CVAR_ARCHIVE | cgame/cg_main.c:2184 |
| `cg_cpmaNtfBlueTorsoColor` | `0x00a5ff` | CVAR_ARCHIVE | cgame/cg_main.c:2176 |
| `cg_cpmaNtfModelSkin` | `bright` | CVAR_ARCHIVE | cgame/cg_main.c:2179 |
| `cg_cpmaNtfRedHeadColor` | `0xff5a00` | CVAR_ARCHIVE | cgame/cg_main.c:2172 |
| `cg_cpmaNtfRedLegsColor` | `0xff0000` | CVAR_ARCHIVE | cgame/cg_main.c:2174 |
| `cg_cpmaNtfRedRailColor` | `0xff5a00` | CVAR_ARCHIVE | cgame/cg_main.c:2183 |
| `cg_cpmaNtfRedTorsoColor` | `0xff5a00` | CVAR_ARCHIVE | cgame/cg_main.c:2173 |
| `cg_cpmaNtfScoreboardClassModel` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2180 |
| `cg_cpmaSound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2584 |
| `cg_cpmaUseNtfEnemyColors` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2171 |
| `cg_cpmaUseNtfModels` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2170 |
| `cg_cpmaUseNtfRailColors` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2182 |
| `cg_crosshairAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1590 |
| `cg_crosshairAlphaAdjust` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1591 |
| `cg_crosshairBrightness` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1589 |
| `cg_crosshairColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1581 |
| `cg_crosshairHitColor` | `0xff0000` | CVAR_ARCHIVE | cgame/cg_main.c:1585 |
| `cg_crosshairHitStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1584 |
| `cg_crosshairHitTime` | `200` | CVAR_ARCHIVE | cgame/cg_main.c:1586 |
| `cg_crosshairPulse` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1582 |
| `cg_customMirrorSurfaces` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2483 |
| `cg_damageFeedbackInterval` | `800` | CVAR_ARCHIVE | cgame/cg_main.c:2415 |
| `cg_damagePlum` | `none g mg sg gl rl lg rg pg bfg gh cg ng pl hmg` | CVAR_ARCHIVE | cgame/cg_main.c:1796 |
| `cg_damagePlumAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1808 |
| `cg_damagePlumBounce` | `120` | CVAR_ARCHIVE | cgame/cg_main.c:1800 |
| `cg_damagePlumColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1807 |
| `cg_damagePlumColorStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1797 |
| `cg_damagePlumFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1803 |
| `cg_damagePlumFontStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1804 |
| `cg_damagePlumGravity` | `250` | CVAR_ARCHIVE | cgame/cg_main.c:1801 |
| `cg_damagePlumPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1805 |
| `cg_damagePlumRandomVelocity` | `70` | CVAR_ARCHIVE | cgame/cg_main.c:1802 |
| `cg_damagePlumScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1806 |
| `cg_damagePlumSumHack` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1809 |
| `cg_damagePlumTarget` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1798 |
| `cg_damagePlumTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:1799 |
| `cg_deadBodyColor` | `0x101010` | CVAR_ARCHIVE | cgame/cg_main.c:2198 |
| `cg_deathShowOwnCorpse` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2451 |
| `cg_deathStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2450 |
| `cg_debugAds` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2467 |
| `cg_debugImpactOrigin` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1603 |
| `cg_debugLightningImpactDistance` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2309 |
| `cg_debugServerCommands` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1650 |
| `cg_demoSmoothing` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2313 |
| `cg_demoSmoothingAngles` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2314 |
| `cg_demoSmoothingTeleportCheck` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2315 |
| `cg_demoStepSmoothing` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2484 |
| `cg_disallowEnemyModelForTeammates` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2199 |
| `cg_dominationPointEnemyAlpha` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2518 |
| `cg_dominationPointEnemyColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2517 |
| `cg_dominationPointNeutralAlpha` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2520 |
| `cg_dominationPointNeutralColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2519 |
| `cg_dominationPointTeamAlpha` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2516 |
| `cg_dominationPointTeamColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2515 |
| `cg_donka_rtcw_good_spellers` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2252 |
| `cg_draw2D` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1418 |
| `cg_drawAmmoWarningAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1482 |
| `cg_drawAmmoWarningAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1489 |
| `cg_drawAmmoWarningColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1488 |
| `cg_drawAmmoWarningFont` | `qlfont` | CVAR_ARCHIVE | cgame/cg_main.c:1484 |
| `cg_drawAmmoWarningPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1485 |
| `cg_drawAmmoWarningScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1486 |
| `cg_drawAmmoWarningStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:1483 |
| `cg_drawAmmoWarningWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1492 |
| `cg_drawAmmoWarningX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1480 |
| `cg_drawAmmoWarningY` | `64` | CVAR_ARCHIVE | cgame/cg_main.c:1481 |
| `cg_drawAttackerAlign` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1515 |
| `cg_drawAttackerAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1523 |
| `cg_drawAttackerColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1522 |
| `cg_drawAttackerFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1524 |
| `cg_drawAttackerFadeTime` | `10000` | CVAR_ARCHIVE | cgame/cg_main.c:1525 |
| `cg_drawAttackerFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1517 |
| `cg_drawAttackerImageScale` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1520 |
| `cg_drawAttackerPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1518 |
| `cg_drawAttackerScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1519 |
| `cg_drawAttackerStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1516 |
| `cg_drawAttackerTime` | `10000` | CVAR_ARCHIVE | cgame/cg_main.c:1521 |
| `cg_drawAttackerWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1526 |
| `cg_drawAttackerX` | `640` | CVAR_ARCHIVE | cgame/cg_main.c:1513 |
| `cg_drawAttackerY` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1514 |
| `cg_drawBBox` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2086 |
| `cg_drawCameraPath` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2316 |
| `cg_drawCameraPathAngles` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2317 |
| `cg_drawCameraPointInfo` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2319 |
| `cg_drawCameraPointInfoAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2322 |
| `cg_drawCameraPointInfoAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2329 |
| `cg_drawCameraPointInfoBackgroundAlpha` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2332 |
| `cg_drawCameraPointInfoBackgroundColor` | `0x000000` | CVAR_ARCHIVE | cgame/cg_main.c:2331 |
| `cg_drawCameraPointInfoColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2327 |
| `cg_drawCameraPointInfoFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2324 |
| `cg_drawCameraPointInfoPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2325 |
| `cg_drawCameraPointInfoScale` | `0.20` | CVAR_ARCHIVE | cgame/cg_main.c:2326 |
| `cg_drawCameraPointInfoSelectedColor` | `0xff5a5a` | CVAR_ARCHIVE | cgame/cg_main.c:2328 |
| `cg_drawCameraPointInfoStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2323 |
| `cg_drawCameraPointInfoWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2330 |
| `cg_drawCameraPointInfoX` | `60` | CVAR_ARCHIVE | cgame/cg_main.c:2320 |
| `cg_drawCameraPointInfoY` | `60` | CVAR_ARCHIVE | cgame/cg_main.c:2321 |
| `cg_drawCenterPrint` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1993 |
| `cg_drawCenterPrintAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1996 |
| `cg_drawCenterPrintAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2003 |
| `cg_drawCenterPrintColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2002 |
| `cg_drawCenterPrintFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2004 |
| `cg_drawCenterPrintFadeTime` | `200` | CVAR_ARCHIVE | cgame/cg_main.c:2005 |
| `cg_drawCenterPrintFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1998 |
| `cg_drawCenterPrintLineSpacing` | `6.0` | CVAR_ARCHIVE | cgame/cg_main.c:2008 |
| `cg_drawCenterPrintOld` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2007 |
| `cg_drawCenterPrintPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1999 |
| `cg_drawCenterPrintScale` | `0.35` | CVAR_ARCHIVE | cgame/cg_main.c:2000 |
| `cg_drawCenterPrintStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:1997 |
| `cg_drawCenterPrintTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:2001 |
| `cg_drawCenterPrintWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2006 |
| `cg_drawCenterPrintX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1994 |
| `cg_drawCenterPrintY` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1995 |
| `cg_drawClientItemTimer` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1422 |
| `cg_drawClientItemTimerAlign` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1432 |
| `cg_drawClientItemTimerAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1430 |
| `cg_drawClientItemTimerFilter` | `rmygqb` | CVAR_ARCHIVE | cgame/cg_main.c:1423 |
| `cg_drawClientItemTimerFont` | `q3small` | CVAR_ARCHIVE | cgame/cg_main.c:1428 |
| `cg_drawClientItemTimerForceMegaHealthWearOff` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1439 |
| `cg_drawClientItemTimerIcon` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1434 |
| `cg_drawClientItemTimerIconSize` | `20` | CVAR_ARCHIVE | cgame/cg_main.c:1435 |
| `cg_drawClientItemTimerIconXoffset` | `-55` | CVAR_ARCHIVE | cgame/cg_main.c:1436 |
| `cg_drawClientItemTimerIconYoffset` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1437 |
| `cg_drawClientItemTimerPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1429 |
| `cg_drawClientItemTimerScale` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1426 |
| `cg_drawClientItemTimerSpacing` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1433 |
| `cg_drawClientItemTimerStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:1431 |
| `cg_drawClientItemTimerTextColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1427 |
| `cg_drawClientItemTimerWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1438 |
| `cg_drawClientItemTimerX` | `635` | CVAR_ARCHIVE | cgame/cg_main.c:1424 |
| `cg_drawClientItemTimerY` | `150` | CVAR_ARCHIVE | cgame/cg_main.c:1425 |
| `cg_drawCpmaMvdIndicator` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1914 |
| `cg_drawCpmaMvdIndicatorAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1917 |
| `cg_drawCpmaMvdIndicatorAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1923 |
| `cg_drawCpmaMvdIndicatorColor` | `0x00ffff` | CVAR_ARCHIVE | cgame/cg_main.c:1922 |
| `cg_drawCpmaMvdIndicatorPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1920 |
| `cg_drawCpmaMvdIndicatorScale` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1921 |
| `cg_drawCpmaMvdIndicatorStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:1918 |
| `cg_drawCpmaMvdIndicatorWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1924 |
| `cg_drawCpmaMvdIndicatorX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1915 |
| `cg_drawCpmaMvdIndicatorY` | `80` | CVAR_ARCHIVE | cgame/cg_main.c:1916 |
| `cg_drawCrosshairNamesAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1534 |
| `cg_drawCrosshairNamesAlpha` | `77` | CVAR_ARCHIVE | cgame/cg_main.c:1541 |
| `cg_drawCrosshairNamesColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1540 |
| `cg_drawCrosshairNamesFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1542 |
| `cg_drawCrosshairNamesFadeTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:1543 |
| `cg_drawCrosshairNamesFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1536 |
| `cg_drawCrosshairNamesPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1537 |
| `cg_drawCrosshairNamesScale` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1538 |
| `cg_drawCrosshairNamesStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1535 |
| `cg_drawCrosshairNamesTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:1539 |
| `cg_drawCrosshairNamesWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1544 |
| `cg_drawCrosshairNamesX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1532 |
| `cg_drawCrosshairNamesY` | `190` | CVAR_ARCHIVE | cgame/cg_main.c:1533 |
| `cg_drawCrosshairTeammateHealth` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1546 |
| `cg_drawCrosshairTeammateHealthAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1549 |
| `cg_drawCrosshairTeammateHealthAlpha` | `77` | CVAR_ARCHIVE | cgame/cg_main.c:1556 |
| `cg_drawCrosshairTeammateHealthColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1555 |
| `cg_drawCrosshairTeammateHealthFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1557 |
| `cg_drawCrosshairTeammateHealthFadeTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:1558 |
| `cg_drawCrosshairTeammateHealthFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1551 |
| `cg_drawCrosshairTeammateHealthPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1552 |
| `cg_drawCrosshairTeammateHealthScale` | `0.125` | CVAR_ARCHIVE | cgame/cg_main.c:1553 |
| `cg_drawCrosshairTeammateHealthStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1550 |
| `cg_drawCrosshairTeammateHealthTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:1554 |
| `cg_drawCrosshairTeammateHealthWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1559 |
| `cg_drawCrosshairTeammateHealthX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1547 |
| `cg_drawCrosshairTeammateHealthY` | `200` | CVAR_ARCHIVE | cgame/cg_main.c:1548 |
| `cg_drawDeadFriendTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:2580 |
| `cg_drawDominationPointStatus` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2524 |
| `cg_drawDominationPointStatusAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2533 |
| `cg_drawDominationPointStatusBackgroundColor` | `0x000000` | CVAR_ARCHIVE | cgame/cg_main.c:2532 |
| `cg_drawDominationPointStatusEnemyColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2530 |
| `cg_drawDominationPointStatusFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2527 |
| `cg_drawDominationPointStatusPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2528 |
| `cg_drawDominationPointStatusScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:2529 |
| `cg_drawDominationPointStatusTeamColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2531 |
| `cg_drawDominationPointStatusTextAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2535 |
| `cg_drawDominationPointStatusTextColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2534 |
| `cg_drawDominationPointStatusTextStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:2536 |
| `cg_drawDominationPointStatusX` | `258` | CVAR_ARCHIVE | cgame/cg_main.c:2525 |
| `cg_drawDominationPointStatusY` | `365` | CVAR_ARCHIVE | cgame/cg_main.c:2526 |
| `cg_drawEntNumbers` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2311 |
| `cg_drawEventNumbers` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2312 |
| `cg_drawFightMessage` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2587 |
| `cg_drawFlagCarrier` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1759 |
| `cg_drawFlagCarrierSize` | `10` | CVAR_ARCHIVE | cgame/cg_main.c:1760 |
| `cg_drawFoe` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1751 |
| `cg_drawFoeMaxWidth` | `24.0` | CVAR_ARCHIVE | cgame/cg_main.c:1753 |
| `cg_drawFoeMinWidth` | `4.0` | CVAR_ARCHIVE | cgame/cg_main.c:1752 |
| `cg_drawFollowing` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1902 |
| `cg_drawFollowingAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1905 |
| `cg_drawFollowingAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1911 |
| `cg_drawFollowingColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1910 |
| `cg_drawFollowingPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1908 |
| `cg_drawFollowingScale` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1909 |
| `cg_drawFollowingStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:1906 |
| `cg_drawFollowingWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1912 |
| `cg_drawFollowingX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1903 |
| `cg_drawFollowingY` | `50` | CVAR_ARCHIVE | cgame/cg_main.c:1904 |
| `cg_drawFPSAlign` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1452 |
| `cg_drawFPSAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1459 |
| `cg_drawFPSColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1458 |
| `cg_drawFPSNoText` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1449 |
| `cg_drawFPSPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1455 |
| `cg_drawFPSScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1456 |
| `cg_drawFPSStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1453 |
| `cg_drawFPSWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1462 |
| `cg_drawFPSX` | `635` | CVAR_ARCHIVE | cgame/cg_main.c:1450 |
| `cg_drawFPSY` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1451 |
| `cg_drawFragMessageAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2256 |
| `cg_drawFragMessageAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2263 |
| `cg_drawFragMessageColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2262 |
| `cg_drawFragMessageFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2264 |
| `cg_drawFragMessageFadeTime` | `200` | CVAR_ARCHIVE | cgame/cg_main.c:2265 |
| `cg_drawFragMessageFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2258 |
| `cg_drawFragMessageFreezeTeamTokens` | `You froze %v, your teammate` | CVAR_ARCHIVE | cgame/cg_main.c:2270 |
| `cg_drawFragMessageFreezeTokens` | `You froze %v` | CVAR_ARCHIVE | cgame/cg_main.c:2269 |
| `cg_drawFragMessageIconScale` | `1.5` | CVAR_ARCHIVE | cgame/cg_main.c:2271 |
| `cg_drawFragMessagePointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2259 |
| `cg_drawFragMessageScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:2260 |
| `cg_drawFragMessageSeparate` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2253 |
| `cg_drawFragMessageStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:2257 |
| `cg_drawFragMessageTeamTokens` | `You fragged %v, your teammate` | CVAR_ARCHIVE | cgame/cg_main.c:2267 |
| `cg_drawFragMessageThawTokens` | `You thawed %v` | CVAR_ARCHIVE | cgame/cg_main.c:2268 |
| `cg_drawFragMessageTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:2261 |
| `cg_drawFragMessageTokens` | `You fragged %v` | CVAR_ARCHIVE | cgame/cg_main.c:2266 |
| `cg_drawFragMessageWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2272 |
| `cg_drawFragMessageX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:2254 |
| `cg_drawFragMessageY` | `120` | CVAR_ARCHIVE | cgame/cg_main.c:2255 |
| `cg_drawFriendMaxWidth` | `24.0` | CVAR_ARCHIVE | cgame/cg_main.c:1750 |
| `cg_drawFriendMinWidth` | `4.0` | CVAR_ARCHIVE | cgame/cg_main.c:1749 |
| `cg_drawFriendStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1748 |
| `cg_drawFullWeaponBar` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1942 |
| `cg_drawHitFlagCarrierTime` | `1500` | CVAR_ARCHIVE | cgame/cg_main.c:1761 |
| `cg_drawHitFriendTime` | `1500` | CVAR_ARCHIVE | cgame/cg_main.c:2581 |
| `cg_drawInfected` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1758 |
| `cg_drawItemPickups` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1885 |
| `cg_drawItemPickupsAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1889 |
| `cg_drawItemPickupsAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1896 |
| `cg_drawItemPickupsColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1895 |
| `cg_drawItemPickupsCount` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1899 |
| `cg_drawItemPickupsFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1897 |
| `cg_drawItemPickupsFadeTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:1898 |
| `cg_drawItemPickupsImageScale` | `0.5` | CVAR_ARCHIVE | cgame/cg_main.c:1888 |
| `cg_drawItemPickupsPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1892 |
| `cg_drawItemPickupsScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1893 |
| `cg_drawItemPickupsStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1890 |
| `cg_drawItemPickupsTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:1894 |
| `cg_drawItemPickupsWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1900 |
| `cg_drawItemPickupsX` | `8` | CVAR_ARCHIVE | cgame/cg_main.c:1886 |
| `cg_drawItemPickupsY` | `360` | CVAR_ARCHIVE | cgame/cg_main.c:1887 |
| `cg_drawJumpSpeeds` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1706 |
| `cg_drawJumpSpeedsAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1711 |
| `cg_drawJumpSpeedsAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1717 |
| `cg_drawJumpSpeedsColor` | `0xffff00` | CVAR_ARCHIVE | cgame/cg_main.c:1716 |
| `cg_drawJumpSpeedsFont` | `q3big` | CVAR_ARCHIVE | cgame/cg_main.c:1713 |
| `cg_drawJumpSpeedsMax` | `12` | CVAR_ARCHIVE | cgame/cg_main.c:1708 |
| `cg_drawJumpSpeedsNoText` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1707 |
| `cg_drawJumpSpeedsPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1714 |
| `cg_drawJumpSpeedsScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1715 |
| `cg_drawJumpSpeedsStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1712 |
| `cg_drawJumpSpeedsTime` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1720 |
| `cg_drawJumpSpeedsTimeAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1724 |
| `cg_drawJumpSpeedsTimeAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1730 |
| `cg_drawJumpSpeedsTimeColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1729 |
| `cg_drawJumpSpeedsTimeFont` | `q3big` | CVAR_ARCHIVE | cgame/cg_main.c:1726 |
| `cg_drawJumpSpeedsTimeNoText` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1721 |
| `cg_drawJumpSpeedsTimePointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1727 |
| `cg_drawJumpSpeedsTimeScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1728 |
| `cg_drawJumpSpeedsTimeStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1725 |
| `cg_drawJumpSpeedsTimeWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1731 |
| `cg_drawJumpSpeedsTimeX` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1722 |
| `cg_drawJumpSpeedsTimeY` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1723 |
| `cg_drawJumpSpeedsWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1718 |
| `cg_drawJumpSpeedsX` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1709 |
| `cg_drawJumpSpeedsY` | `300` | CVAR_ARCHIVE | cgame/cg_main.c:1710 |
| `cg_drawKeyPress` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2611 |
| `cg_drawOrigin` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1857 |
| `cg_drawOriginAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1860 |
| `cg_drawOriginAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1866 |
| `cg_drawOriginColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1865 |
| `cg_drawOriginFont` | `q3big` | CVAR_ARCHIVE | cgame/cg_main.c:1862 |
| `cg_drawOriginPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1863 |
| `cg_drawOriginScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1864 |
| `cg_drawOriginStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1861 |
| `cg_drawOriginWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1867 |
| `cg_drawOriginX` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1858 |
| `cg_drawOriginY` | `420` | CVAR_ARCHIVE | cgame/cg_main.c:1859 |
| `cg_drawPlayerNames` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2286 |
| `cg_drawPlayerNamesAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2293 |
| `cg_drawPlayerNamesColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2292 |
| `cg_drawPlayerNamesFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2289 |
| `cg_drawPlayerNamesPointSize` | `16` | CVAR_ARCHIVE | cgame/cg_main.c:2290 |
| `cg_drawPlayerNamesScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:2291 |
| `cg_drawPlayerNamesStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:2288 |
| `cg_drawPlayerNamesY` | `64` | CVAR_ARCHIVE | cgame/cg_main.c:2287 |
| `cg_drawPlayersLeft` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1870 |
| `cg_drawPowerupAvailable` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1878 |
| `cg_drawPowerupAvailableAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1881 |
| `cg_drawPowerupAvailableFadeEnd` | `520.0` | CVAR_ARCHIVE | cgame/cg_main.c:1883 |
| `cg_drawPowerupAvailableFadeStart` | `705.0` | CVAR_ARCHIVE | cgame/cg_main.c:1882 |
| `cg_drawPowerupAvailableOffset` | `90.0` | CVAR_ARCHIVE | cgame/cg_main.c:1880 |
| `cg_drawPowerupAvailableScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1879 |
| `cg_drawPowerupRespawn` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1873 |
| `cg_drawPowerupRespawnAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1876 |
| `cg_drawPowerupRespawnOffset` | `90.0` | CVAR_ARCHIVE | cgame/cg_main.c:1875 |
| `cg_drawPowerupRespawnScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1874 |
| `cg_drawPowerups` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1871 |
| `cg_drawProxWarning` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2471 |
| `cg_drawProxWarningAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2474 |
| `cg_drawProxWarningAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2480 |
| `cg_drawProxWarningColor` | `0xfe0000` | CVAR_ARCHIVE | cgame/cg_main.c:2479 |
| `cg_drawProxWarningPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2477 |
| `cg_drawProxWarningScale` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:2478 |
| `cg_drawProxWarningStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:2475 |
| `cg_drawProxWarningWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2481 |
| `cg_drawProxWarningX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:2472 |
| `cg_drawProxWarningY` | `80` | CVAR_ARCHIVE | cgame/cg_main.c:2473 |
| `cg_drawRaceTime` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1733 |
| `cg_drawRaceTimeAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1737 |
| `cg_drawRaceTimeAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1743 |
| `cg_drawRaceTimeColor` | `0xffff99` | CVAR_ARCHIVE | cgame/cg_main.c:1742 |
| `cg_drawRaceTimeFont` | `q3big` | CVAR_ARCHIVE | cgame/cg_main.c:1739 |
| `cg_drawRaceTimeNoText` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1734 |
| `cg_drawRaceTimePointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1740 |
| `cg_drawRaceTimeScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1741 |
| `cg_drawRaceTimeStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1738 |
| `cg_drawRaceTimeWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1744 |
| `cg_drawRaceTimeX` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1735 |
| `cg_drawRaceTimeY` | `420` | CVAR_ARCHIVE | cgame/cg_main.c:1736 |
| `cg_drawRewardsAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1565 |
| `cg_drawRewardsAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1573 |
| `cg_drawRewardsColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1572 |
| `cg_drawRewardsFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1574 |
| `cg_drawRewardsFadeTime` | `200` | CVAR_ARCHIVE | cgame/cg_main.c:1575 |
| `cg_drawRewardsFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1567 |
| `cg_drawRewardsImageScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1570 |
| `cg_drawRewardsMax` | `10` | CVAR_ARCHIVE | cgame/cg_main.c:1562 |
| `cg_drawRewardsPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1568 |
| `cg_drawRewardsScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1569 |
| `cg_drawRewardsStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1566 |
| `cg_drawRewardsTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:1571 |
| `cg_drawRewardsWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1576 |
| `cg_drawRewardsX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:1563 |
| `cg_drawRewardsY` | `56` | CVAR_ARCHIVE | cgame/cg_main.c:1564 |
| `cg_drawScores` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1869 |
| `cg_drawSelf` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1754 |
| `cg_drawSelfIconStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1757 |
| `cg_drawSelfMaxWidth` | `24.0` | CVAR_ARCHIVE | cgame/cg_main.c:1756 |
| `cg_drawSelfMinWidth` | `4.0` | CVAR_ARCHIVE | cgame/cg_main.c:1755 |
| `cg_drawSnapshotAlign` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1467 |
| `cg_drawSnapshotAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1473 |
| `cg_drawSnapshotColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1472 |
| `cg_drawSnapshotFont` | `q3big` | CVAR_ARCHIVE | cgame/cg_main.c:1469 |
| `cg_drawSnapshotPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1470 |
| `cg_drawSnapshotScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1471 |
| `cg_drawSnapshotStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1468 |
| `cg_drawSnapshotWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1474 |
| `cg_drawSnapshotX` | `635` | CVAR_ARCHIVE | cgame/cg_main.c:1465 |
| `cg_drawSnapshotY` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1466 |
| `cg_drawSpawns` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1958 |
| `cg_drawSpawnsInitalZ` | `0.0` | CVAR_ARCHIVE | cgame/cg_main.c:1960 |
| `cg_drawSpawnsInitial` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1959 |
| `cg_drawSpawnsRespawns` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1961 |
| `cg_drawSpawnsRespawnsZ` | `0.0` | CVAR_ARCHIVE | cgame/cg_main.c:1962 |
| `cg_drawSpawnsShared` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1963 |
| `cg_drawSpawnsSharedZ` | `0.0` | CVAR_ARCHIVE | cgame/cg_main.c:1964 |
| `cg_drawSpecMessages` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2419 |
| `cg_drawSpeed` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1843 |
| `cg_drawSpeedAlign` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1847 |
| `cg_drawSpeedAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1853 |
| `cg_drawSpeedChangeColor` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1855 |
| `cg_drawSpeedColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1852 |
| `cg_drawSpeedNoText` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1846 |
| `cg_drawSpeedPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1850 |
| `cg_drawSpeedScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1851 |
| `cg_drawSpeedStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1848 |
| `cg_drawSpeedWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1854 |
| `cg_drawSpeedX` | `635` | CVAR_ARCHIVE | cgame/cg_main.c:1844 |
| `cg_drawSpeedY` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1845 |
| `cg_drawSprites` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2424 |
| `cg_drawSpritesDeadPlayers` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2426 |
| `cg_drawSpriteSelf` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2425 |
| `cg_drawTeamBackground` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1420 |
| `cg_drawTeamOverlayAlign` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1698 |
| `cg_drawTeamOverlayLineOffset` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1702 |
| `cg_drawTeamOverlayMaxPlayers` | `-1` | CVAR_ARCHIVE | cgame/cg_main.c:1703 |
| `cg_drawTeamOverlayPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1697 |
| `cg_drawTeamOverlayScale` | `0.2` | CVAR_ARCHIVE | cgame/cg_main.c:1699 |
| `cg_drawTeamOverlayWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1701 |
| `cg_drawTeamOverlayX` | `640` | CVAR_ARCHIVE | cgame/cg_main.c:1693 |
| `cg_drawTeamOverlayY` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1694 |
| `cg_drawTeamVote` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2022 |
| `cg_drawTeamVoteAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2025 |
| `cg_drawTeamVoteAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2031 |
| `cg_drawTeamVoteColor` | `0x00ffff` | CVAR_ARCHIVE | cgame/cg_main.c:2030 |
| `cg_drawTeamVoteFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2027 |
| `cg_drawTeamVotePointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2028 |
| `cg_drawTeamVoteScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:2029 |
| `cg_drawTeamVoteStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:2026 |
| `cg_drawTeamVoteWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2032 |
| `cg_drawTeamVoteX` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2023 |
| `cg_drawTeamVoteY` | `300` | CVAR_ARCHIVE | cgame/cg_main.c:2024 |
| `cg_drawTieredArmorAvailability` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2546 |
| `cg_drawViewPointMark` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2334 |
| `cg_drawVote` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2010 |
| `cg_drawVoteAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2013 |
| `cg_drawVoteAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2019 |
| `cg_drawVoteColor` | `0xffff00` | CVAR_ARCHIVE | cgame/cg_main.c:2018 |
| `cg_drawVoteFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2015 |
| `cg_drawVotePointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2016 |
| `cg_drawVoteScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:2017 |
| `cg_drawVoteStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:2014 |
| `cg_drawVoteWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2020 |
| `cg_drawVoteX` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2011 |
| `cg_drawVoteY` | `300` | CVAR_ARCHIVE | cgame/cg_main.c:2012 |
| `cg_drawWaitingForPlayers` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2034 |
| `cg_drawWaitingForPlayersAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2037 |
| `cg_drawWaitingForPlayersAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2043 |
| `cg_drawWaitingForPlayersColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2042 |
| `cg_drawWaitingForPlayersPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2040 |
| `cg_drawWaitingForPlayersScale` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:2041 |
| `cg_drawWaitingForPlayersStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:2038 |
| `cg_drawWaitingForPlayersWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2044 |
| `cg_drawWaitingForPlayersX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:2035 |
| `cg_drawWaitingForPlayersY` | `60` | CVAR_ARCHIVE | cgame/cg_main.c:2036 |
| `cg_drawWarmupString` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2046 |
| `cg_drawWarmupStringAlign` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2049 |
| `cg_drawWarmupStringAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2055 |
| `cg_drawWarmupStringColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2054 |
| `cg_drawWarmupStringFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2051 |
| `cg_drawWarmupStringPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:2052 |
| `cg_drawWarmupStringScale` | `0.6` | CVAR_ARCHIVE | cgame/cg_main.c:2053 |
| `cg_drawWarmupStringStyle` | `6` | CVAR_ARCHIVE | cgame/cg_main.c:2050 |
| `cg_drawWarmupStringWideScreen` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2056 |
| `cg_drawWarmupStringX` | `320` | CVAR_ARCHIVE | cgame/cg_main.c:2047 |
| `cg_drawWarmupStringY` | `60` | CVAR_ARCHIVE | cgame/cg_main.c:2048 |
| `cg_dumpEntsUseServerTime` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2489 |
| `cg_echoPopupScale` | `0.3` | CVAR_ARCHIVE | cgame/cg_main.c:2236 |
| `cg_echoPopupTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:2233 |
| `cg_echoPopupWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2237 |
| `cg_echoPopupX` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:2234 |
| `cg_echoPopupY` | `340` | CVAR_ARCHIVE | cgame/cg_main.c:2235 |
| `cg_enableAtCommands` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2460 |
| `cg_enableBreath` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1824 |
| `cg_enableDust` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1826 |
| `cg_enemyFlagColor` | `0x00ff00` | CVAR_ARCHIVE | cgame/cg_main.c:2110 |
| `cg_enemyHeadColor` | `0x2a8000` | CVAR_ARCHIVE | cgame/cg_main.c:2101 |
| `cg_enemyHeadModel` | `keel/bright` | CVAR_ARCHIVE | cgame/cg_main.c:2097 |
| `cg_enemyHeadSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2098 |
| `cg_enemyLegsColor` | `0x2a8000` | CVAR_ARCHIVE | cgame/cg_main.c:2103 |
| `cg_enemyLegsSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2100 |
| `cg_enemyModel` | `keel/bright` | CVAR_ARCHIVE | cgame/cg_main.c:2096 |
| `cg_enemyRailColor1` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2104 |
| `cg_enemyRailColor2` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2105 |
| `cg_enemyRailItemColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2109 |
| `cg_enemyRailNudge` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2108 |
| `cg_enemyRailRings` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2107 |
| `cg_enemyTorsoColor` | `0x2a8000` | CVAR_ARCHIVE | cgame/cg_main.c:2102 |
| `cg_enemyTorsoSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2099 |
| `cg_fadeAlpha` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2458 |
| `cg_fadeColor` | `0x000000` | CVAR_ARCHIVE | cgame/cg_main.c:2457 |
| `cg_fadeStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2459 |
| `cg_fallbackHeadModel` | `crash` | CVAR_ARCHIVE | cgame/cg_main.c:2201 |
| `cg_fallbackModel` | `crash` | CVAR_ARCHIVE | cgame/cg_main.c:2200 |
| `cg_fallKick` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2416 |
| `cg_firstPersonShaderWeaponBFG` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2368 |
| `cg_firstPersonShaderWeaponChainGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2372 |
| `cg_firstPersonShaderWeaponGauntlet` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2360 |
| `cg_firstPersonShaderWeaponGrapplingHook` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2369 |
| `cg_firstPersonShaderWeaponGrenadeLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2363 |
| `cg_firstPersonShaderWeaponHeavyMachineGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2373 |
| `cg_firstPersonShaderWeaponLightningGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2365 |
| `cg_firstPersonShaderWeaponMachineGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2361 |
| `cg_firstPersonShaderWeaponNailGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2370 |
| `cg_firstPersonShaderWeaponPlasmaGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2367 |
| `cg_firstPersonShaderWeaponProximityLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2371 |
| `cg_firstPersonShaderWeaponRailGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2366 |
| `cg_firstPersonShaderWeaponRocketLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2364 |
| `cg_firstPersonShaderWeaponShotgun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2362 |
| `cg_firstPersonSwitchSound` | `sound/wc/beep05` | CVAR_ARCHIVE | cgame/cg_main.c:2469 |
| `cg_flagStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2506 |
| `cg_flagTakenSound` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2507 |
| `cg_flightTrail` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2439 |
| `cg_forcePovModel` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1684 |
| `cg_forcePovModelIgnoreFreecamTeamSettings` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1685 |
| `cg_fovForceAspectHeight` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1381 |
| `cg_fovForceAspectWidth` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1380 |
| `cg_fovIntermission` | `90` | CVAR_ARCHIVE | cgame/cg_main.c:1382 |
| `cg_fovStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1379 |
| `cg_fovy` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1378 |
| `cg_fragIconHeightFixed` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2284 |
| `cg_fragMessageStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2250 |
| `cg_fragTokenAccuracyStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2283 |
| `cg_freecam_crosshair` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1971 |
| `cg_freecam_noclip` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1966 |
| `cg_freecam_pitch` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1969 |
| `cg_freecam_rollValue` | `0.5` | CVAR_ARCHIVE | cgame/cg_main.c:1973 |
| `cg_freecam_sensitivity` | `0.1` | CVAR_ARCHIVE | cgame/cg_main.c:1967 |
| `cg_freecam_speed` | `400` | CVAR_ARCHIVE | cgame/cg_main.c:1970 |
| `cg_freecam_unlockPitch` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1975 |
| `cg_freecam_useServerView` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1974 |
| `cg_freecam_useTeamSettings` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1972 |
| `cg_freecam_yaw` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1968 |
| `cg_fxCompiled` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2399 |
| `cg_fxDebugEntities` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2398 |
| `cg_fxfile` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2391 |
| `cg_fxinterval` | `25` | CVAR_ARCHIVE | cgame/cg_main.c:2392 |
| `cg_fxLightningGunImpactFps` | `125` | CVAR_ARCHIVE | cgame/cg_main.c:2397 |
| `cg_fxratio` | `0.002` | CVAR_ARCHIVE | cgame/cg_main.c:2393 |
| `cg_fxScriptMinDistance` | `0.001` | CVAR_ARCHIVE | cgame/cg_main.c:2395 |
| `cg_fxScriptMinEmitter` | `0.0` | CVAR_ARCHIVE | cgame/cg_main.c:2394 |
| `cg_fxScriptMinInterval` | `0.001` | CVAR_ARCHIVE | cgame/cg_main.c:2396 |
| `cg_fxThreads` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2401 |
| `cg_gameType` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2417 |
| `cg_gibBounceFactor` | `0.6` | CVAR_ARCHIVE | cgame/cg_main.c:1399 |
| `cg_gibColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1388 |
| `cg_gibDirScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1392 |
| `cg_gibFloatingOriginOffset` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:1406 |
| `cg_gibFloatingOriginOffsetZ` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1407 |
| `cg_gibFloatingRandomness` | `75` | CVAR_ARCHIVE | cgame/cg_main.c:1405 |
| `cg_gibFloatingVelocity` | `125` | CVAR_ARCHIVE | cgame/cg_main.c:1404 |
| `cg_gibGravity` | `800` | CVAR_ARCHIVE | cgame/cg_main.c:1400 |
| `cg_gibJump` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1389 |
| `cg_gibOriginOffset` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1393 |
| `cg_gibOriginOffsetZ` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1394 |
| `cg_gibRandomness` | `250` | CVAR_ARCHIVE | cgame/cg_main.c:1395 |
| `cg_gibRandomnessZ` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1396 |
| `cg_gibSparksColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1402 |
| `cg_gibSparksHighlight` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1403 |
| `cg_gibSparksSize` | `3.5` | CVAR_ARCHIVE | cgame/cg_main.c:1401 |
| `cg_gibStepTime` | `50` | CVAR_ARCHIVE | cgame/cg_main.c:1398 |
| `cg_gibTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:1397 |
| `cg_gibVelocity` | `600` | CVAR_ARCHIVE | cgame/cg_main.c:1390 |
| `cg_gibVelocityRandomness` | `250` | CVAR_ARCHIVE | cgame/cg_main.c:1391 |
| `cg_grenadeColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2244 |
| `cg_grenadeColorAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2245 |
| `cg_grenadeEnemyColor` | `0x00ff00` | CVAR_ARCHIVE | cgame/cg_main.c:2248 |
| `cg_grenadeEnemyColorAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2249 |
| `cg_grenadeTeamColor` | `0xffff00` | CVAR_ARCHIVE | cgame/cg_main.c:2246 |
| `cg_grenadeTeamColorAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2247 |
| `cg_gunSize` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1639 |
| `cg_gunSizeThirdPerson` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1640 |
| `cg_hasteTrail` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2440 |
| `cg_headShots` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2540 |
| `cg_helpIcon` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2509 |
| `cg_helpIconMaxWidth` | `32.0` | CVAR_ARCHIVE | cgame/cg_main.c:2512 |
| `cg_helpIconMinWidth` | `16.0` | CVAR_ARCHIVE | cgame/cg_main.c:2511 |
| `cg_helpIconStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:2510 |
| `cg_hitBeep` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1956 |
| `cg_hudBlueTeamColor` | `0x3366ff` | CVAR_ARCHIVE | cgame/cg_main.c:2089 |
| `cg_hudForceBlueTeamClanTag` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2094 |
| `cg_hudForceRedTeamClanTag` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2093 |
| `cg_hudNeutralTeamColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2091 |
| `cg_hudNoTeamColor` | `0xfecb32` | CVAR_ARCHIVE | cgame/cg_main.c:2090 |
| `cg_hudRedTeamColor` | `0xfe3219` | CVAR_ARCHIVE | cgame/cg_main.c:2088 |
| `cg_ignoreClientHeadModel` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2165 |
| `cg_ignoreServerPlaySound` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2220 |
| `cg_impactSparks` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1408 |
| `cg_impactSparksColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1412 |
| `cg_impactSparksHighlight` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1413 |
| `cg_impactSparksLifetime` | `250` | CVAR_ARCHIVE | cgame/cg_main.c:1409 |
| `cg_impactSparksSize` | `8` | CVAR_ARCHIVE | cgame/cg_main.c:1410 |
| `cg_impactSparksVelocity` | `128` | CVAR_ARCHIVE | cgame/cg_main.c:1411 |
| `cg_inheritPowerupShader` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2456 |
| `cg_interpolateMissiles` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2072 |
| `cg_itemFx` | `7` | CVAR_ARCHIVE | cgame/cg_main.c:1598 |
| `cg_itemSize` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1599 |
| `cg_itemSpawnPrint` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1441 |
| `cg_itemsWh` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1597 |
| `cg_itemTimers` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1443 |
| `cg_itemTimersAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1446 |
| `cg_itemTimersOffset` | `8.0` | CVAR_ARCHIVE | cgame/cg_main.c:1445 |
| `cg_itemTimersScale` | `1.3` | CVAR_ARCHIVE | cgame/cg_main.c:1444 |
| `cg_itemUseMessage` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2443 |
| `cg_itemUseSound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2444 |
| `cg_kickScale` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2413 |
| `cg_killBeep` | `7` | CVAR_ARCHIVE | cgame/cg_main.c:2449 |
| `cg_lagometerAlign` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1611 |
| `cg_lagometerAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1618 |
| `cg_lagometerAveragePing` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1620 |
| `cg_lagometerFlash` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1608 |
| `cg_lagometerFlashValue` | `80` | CVAR_ARCHIVE | cgame/cg_main.c:1609 |
| `cg_lagometerFont` | `q3big` | CVAR_ARCHIVE | cgame/cg_main.c:1613 |
| `cg_lagometerFontAlign` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1610 |
| `cg_lagometerFontAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:1619 |
| `cg_lagometerFontColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:1617 |
| `cg_lagometerFontPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1614 |
| `cg_lagometerFontScale` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1615 |
| `cg_lagometerFontStyle` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1612 |
| `cg_lagometerScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1616 |
| `cg_lagometerSnapshotPing` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1621 |
| `cg_lagometerWideScreen` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1622 |
| `cg_lagometerX` | `640` | CVAR_ARCHIVE | cgame/cg_main.c:1606 |
| `cg_lagometerY` | `336` | CVAR_ARCHIVE | cgame/cg_main.c:1607 |
| `cg_levelTimerDefaultTimeLimit` | `60` | CVAR_ARCHIVE | cgame/cg_main.c:2337 |
| `cg_levelTimerDirection` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2335 |
| `cg_levelTimerOvertimeReset` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2338 |
| `cg_lightningAngleOriginStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2308 |
| `cg_lightningImpact` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2300 |
| `cg_lightningImpactCap` | `192` | CVAR_ARCHIVE | cgame/cg_main.c:2303 |
| `cg_lightningImpactCapMin` | `60` | CVAR_ARCHIVE | cgame/cg_main.c:2304 |
| `cg_lightningImpactOthersSize` | `0.0` | CVAR_ARCHIVE | cgame/cg_main.c:2302 |
| `cg_lightningImpactProject` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2305 |
| `cg_lightningImpactSize` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:2301 |
| `cg_lightningRenderStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2307 |
| `cg_lightningSize` | `8` | CVAR_ARCHIVE | cgame/cg_main.c:2310 |
| `cg_lightningStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2306 |
| `cg_loadDefaultMenus` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2243 |
| `cg_localTime` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2445 |
| `cg_localTimeStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2446 |
| `cg_lowAmmoWarningBFG` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1506 |
| `cg_lowAmmoWarningChainGun` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:1510 |
| `cg_lowAmmoWarningGauntlet` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1498 |
| `cg_lowAmmoWarningGrapplingHook` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1507 |
| `cg_lowAmmoWarningGrenadeLauncher` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1501 |
| `cg_lowAmmoWarningLightningGun` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:1503 |
| `cg_lowAmmoWarningMachineGun` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:1499 |
| `cg_lowAmmoWarningNailGun` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:1508 |
| `cg_lowAmmoWarningPercentile` | `0.20` | CVAR_ARCHIVE | cgame/cg_main.c:1495 |
| `cg_lowAmmoWarningPlasmaGun` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:1505 |
| `cg_lowAmmoWarningProximityLauncher` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:1509 |
| `cg_lowAmmoWarningRailGun` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1504 |
| `cg_lowAmmoWarningRocketLauncher` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1502 |
| `cg_lowAmmoWarningShotgun` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1500 |
| `cg_lowAmmoWarningSound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1496 |
| `cg_lowAmmoWarningStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1494 |
| `cg_lowAmmoWeaponBarWarning` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1497 |
| `cg_markFadeTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:1602 |
| `cg_markTime` | `10000` | CVAR_ARCHIVE | cgame/cg_main.c:1601 |
| `cg_mouseSeekPollInterval` | `50` | CVAR_ARCHIVE | cgame/cg_main.c:2453 |
| `cg_mouseSeekScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:2452 |
| `cg_mouseSeekUseTimescale` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2454 |
| `cg_muzzleFlash` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2340 |
| `cg_neutralFlagColor` | `0xf6f600` | CVAR_ARCHIVE | cgame/cg_main.c:2168 |
| `cg_noItemUseMessage` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2441 |
| `cg_noItemUseSound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2442 |
| `cg_obituaryFadeTime` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:2277 |
| `cg_obituaryIconScale` | `1.5` | CVAR_ARCHIVE | cgame/cg_main.c:2275 |
| `cg_obituaryStack` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:2278 |
| `cg_obituaryTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:2276 |
| `cg_obituaryTokens` | `%k %i %v` | CVAR_ARCHIVE | cgame/cg_main.c:2274 |
| `cg_ourHeadColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2193 |
| `cg_ourHeadSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2190 |
| `cg_ourLegsColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2195 |
| `cg_ourLegsSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2192 |
| `cg_ourTorsoColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2194 |
| `cg_ourTorsoSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2191 |
| `cg_overallFontScale` | `1.125` | CVAR_ARCHIVE | cgame/cg_main.c:1933 |
| `cg_pathRewindTime` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2487 |
| `cg_pathSkipNum` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2488 |
| `cg_perKillStatsClearNotFiringExcludeSingleClickWeapons` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2297 |
| `cg_perKillStatsClearNotFiringTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:2296 |
| `cg_perKillStatsExcludePostKillSpam` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2295 |
| `cg_plasmaStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1839 |
| `cg_playerLeanScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:2427 |
| `cg_playerModelAllowServerOverride` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2498 |
| `cg_playerModelAllowServerScale` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2496 |
| `cg_playerModelAllowServerScaleDefault` | `1.1` | CVAR_ARCHIVE | cgame/cg_main.c:2497 |
| `cg_playerModelAutoScaleHeight` | `57` | CVAR_ARCHIVE | cgame/cg_main.c:2495 |
| `cg_playerModelForceHeadOffset` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2494 |
| `cg_playerModelForceHeadScale` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2493 |
| `cg_playerModelForceLegsScale` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2491 |
| `cg_playerModelForceScale` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2490 |
| `cg_playerModelForceTorsoScale` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2492 |
| `cg_playerShader` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2078 |
| `cg_powerupBlink` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2502 |
| `cg_powerupKillCounter` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2503 |
| `cg_powerupLight` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2501 |
| `cg_printSkillRating` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2299 |
| `cg_printTimeStamps` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2225 |
| `cg_proxMineTick` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2470 |
| `cg_q3mmeCameraSmoothPos` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2435 |
| `cg_q3mmeDofMarker` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2437 |
| `cg_qlFontScaling` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1930 |
| `cg_qlhud` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1929 |
| `cg_quadFireSound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2412 |
| `cg_quadKillCounter` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2461 |
| `cg_quadSoundRate` | `1000` | CVAR_ARCHIVE | cgame/cg_main.c:2583 |
| `cg_racePlayerShader` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2582 |
| `cg_railFromMuzzle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1634 |
| `cg_railItemColor` | `0xd4af37` | CVAR_ARCHIVE | cgame/cg_main.c:1632 |
| `cg_railNudge` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1627 |
| `cg_railQL` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1625 |
| `cg_railQLRailRingWhiteValue` | `0.45` | CVAR_ARCHIVE | cgame/cg_main.c:1626 |
| `cg_railRadius` | `4` | CVAR_ARCHIVE | cgame/cg_main.c:1629 |
| `cg_railRings` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1628 |
| `cg_railRotation` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1630 |
| `cg_railSpacing` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1631 |
| `cg_railUseOwnColors` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1633 |
| `cg_redRoverRoundStartSound` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2619 |
| `cg_redTeamFlagColor` | `0xff0000` | CVAR_ARCHIVE | cgame/cg_main.c:2142 |
| `cg_redTeamHeadColor` | `0xff0000` | CVAR_ARCHIVE | cgame/cg_main.c:2133 |
| `cg_redTeamHeadModel` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2129 |
| `cg_redTeamHeadSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2130 |
| `cg_redTeamLegsColor` | `0xff0000` | CVAR_ARCHIVE | cgame/cg_main.c:2135 |
| `cg_redTeamLegsSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2132 |
| `cg_redTeamModel` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2128 |
| `cg_redTeamRailColor1` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2136 |
| `cg_redTeamRailColor2` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2137 |
| `cg_redTeamRailItemColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2138 |
| `cg_redTeamRailNudge` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2141 |
| `cg_redTeamRailRings` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2140 |
| `cg_redTeamTorsoColor` | `0xff0000` | CVAR_ARCHIVE | cgame/cg_main.c:2134 |
| `cg_redTeamTorsoSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2131 |
| `cg_rewardAccuracy` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2602 |
| `cg_rewardAssist` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2595 |
| `cg_rewardCapture` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2590 |
| `cg_rewardComboKill` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2596 |
| `cg_rewardDefend` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2594 |
| `cg_rewardExcellent` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2592 |
| `cg_rewardFirstFrag` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2604 |
| `cg_rewardHeadshot` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2601 |
| `cg_rewardHumiliation` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2593 |
| `cg_rewardImpressive` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2591 |
| `cg_rewardMidAir` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2598 |
| `cg_rewardPerfect` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2605 |
| `cg_rewardPerforated` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2600 |
| `cg_rewardQuadGod` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2603 |
| `cg_rewardRampage` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2597 |
| `cg_rewardRevenge` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2599 |
| `cg_rewardsStack` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1578 |
| `cg_rocketAimBot` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2545 |
| `cg_roundScoreBoard` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2539 |
| `cg_scoreBoardAtIntermission` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1946 |
| `cg_scoreBoardForceLineHeight` | `-1` | CVAR_ARCHIVE | cgame/cg_main.c:1951 |
| `cg_scoreBoardForceLineHeightDefault` | `9` | CVAR_ARCHIVE | cgame/cg_main.c:1952 |
| `cg_scoreBoardForceLineHeightTeam` | `-1` | CVAR_ARCHIVE | cgame/cg_main.c:1953 |
| `cg_scoreBoardForceLineHeightTeamDefault` | `8` | CVAR_ARCHIVE | cgame/cg_main.c:1954 |
| `cg_scoreBoardOld` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1948 |
| `cg_scoreBoardOld` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:1949 |
| `cg_scoreBoardSpectatorScroll` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1944 |
| `cg_scoreBoardStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1943 |
| `cg_scoreBoardWarmup` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1947 |
| `cg_scoreBoardWhenDead` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1945 |
| `cg_screenDamage` | `0x700000` | CVAR_ARCHIVE | cgame/cg_main.c:2231 |
| `cg_screenDamage_Self` | `0x000000` | CVAR_ARCHIVE | cgame/cg_main.c:2229 |
| `cg_screenDamage_Team` | `0x700000` | CVAR_ARCHIVE | cgame/cg_main.c:2227 |
| `cg_screenDamageAlpha` | `200` | CVAR_ARCHIVE | cgame/cg_main.c:2230 |
| `cg_screenDamageAlpha_Self` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2228 |
| `cg_screenDamageAlpha_Team` | `200` | CVAR_ARCHIVE | cgame/cg_main.c:2226 |
| `cg_selfOnTeamOverlay` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1704 |
| `cg_serverCenterPrint` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1989 |
| `cg_serverCenterPrintToChat` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1990 |
| `cg_serverCenterPrintToConsole` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1991 |
| `cg_serverPrint` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1985 |
| `cg_serverPrintToChat` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1986 |
| `cg_serverPrintToConsole` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1987 |
| `cg_shotgunImpactSparks` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1414 |
| `cg_shotgunMarks` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1415 |
| `cg_shotgunRandomness` | `2.0` | CVAR_ARCHIVE | cgame/cg_main.c:1417 |
| `cg_shotgunStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1416 |
| `cg_simpleItemsBob` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1595 |
| `cg_simpleItemsHeightOffset` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1596 |
| `cg_simpleItemsScale` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1594 |
| `cg_smokeRadius_breath` | `16` | CVAR_ARCHIVE | cgame/cg_main.c:1823 |
| `cg_smokeRadius_dust` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1825 |
| `cg_smokeRadius_flight` | `8` | CVAR_ARCHIVE | cgame/cg_main.c:1827 |
| `cg_smokeRadius_GL` | `32` | CVAR_ARCHIVE | cgame/cg_main.c:1819 |
| `cg_smokeRadius_haste` | `8` | CVAR_ARCHIVE | cgame/cg_main.c:1828 |
| `cg_smokeRadius_NG` | `16` | CVAR_ARCHIVE | cgame/cg_main.c:1820 |
| `cg_smokeRadius_PL` | `32` | CVAR_ARCHIVE | cgame/cg_main.c:1822 |
| `cg_smokeRadius_RL` | `64` | CVAR_ARCHIVE | cgame/cg_main.c:1821 |
| `cg_smokeRadius_SG` | `32` | CVAR_ARCHIVE | cgame/cg_main.c:1818 |
| `cg_soundBuffer` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2586 |
| `cg_soundPvs` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2585 |
| `cg_spawnArmorTime` | `500` | CVAR_ARCHIVE | cgame/cg_main.c:2390 |
| `cg_specOffsetQL` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2609 |
| `cg_spectatorListQue` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2543 |
| `cg_spectatorListScore` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2542 |
| `cg_spectatorListSkillRating` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2541 |
| `cg_statusBarHeadStyle` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2620 |
| `cg_stepSmoothMaxChange` | `32` | CVAR_ARCHIVE | cgame/cg_main.c:2486 |
| `cg_stepSmoothTime` | `100` | CVAR_ARCHIVE | cgame/cg_main.c:2485 |
| `cg_teamChatBeep` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1982 |
| `cg_teamChatBeepMaxTime` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1983 |
| `cg_teamFlagColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2126 |
| `cg_teamHeadColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2117 |
| `cg_teamHeadModel` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2113 |
| `cg_teamHeadSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2114 |
| `cg_teamKillWarning` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2455 |
| `cg_teamLegsColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2119 |
| `cg_teamLegsSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2116 |
| `cg_teamModel` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2112 |
| `cg_teamRailColor1` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2120 |
| `cg_teamRailColor2` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2121 |
| `cg_teamRailItemColor` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2125 |
| `cg_teamRailNudge` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2124 |
| `cg_teamRailRings` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2123 |
| `cg_teamTorsoColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2118 |
| `cg_teamTorsoSkin` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2115 |
| `cg_testQlFont` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1926 |
| `cg_textBlueTeamColor` | `0x7ebefe` | CVAR_ARCHIVE | cgame/cg_main.c:2281 |
| `cg_textRedTeamColor` | `0xfc7e7d` | CVAR_ARCHIVE | cgame/cg_main.c:2280 |
| `cg_thawGibs` | `10` | CVAR_ARCHIVE | cgame/cg_main.c:1386 |
| `cg_thirdPersonAvoidSolid` | `1` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1670 |
| `cg_thirdPersonAvoidSolidSize` | `8` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1672 |
| `cg_thirdPersonFocusDistance` | `512.0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1664 |
| `cg_thirdPersonMaxPitch` | `-1` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1662 |
| `cg_thirdPersonMaxPlayerPitch` | `45` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1663 |
| `cg_thirdPersonMovementKeys` | `1` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1673 |
| `cg_thirdPersonNoMoveAngles` | `0 0 0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1674 |
| `cg_thirdPersonNoMoveUsePreviousAngles` | `1` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1675 |
| `cg_thirdPersonOffsetZ` | `0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1665 |
| `cg_thirdPersonPitchScale` | `1.0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1668 |
| `cg_thirdPersonPlayerCrouchHeightChange` | `1` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1667 |
| `cg_thirdPersonPlayerOffsetZ` | `8` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1666 |
| `cg_thirdPersonPlayerPitchScale` | `0.5` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1669 |
| `cg_thirdPersonShaderWeaponBFG` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2383 |
| `cg_thirdPersonShaderWeaponChainGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2387 |
| `cg_thirdPersonShaderWeaponGauntlet` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2375 |
| `cg_thirdPersonShaderWeaponGrapplingHook` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2384 |
| `cg_thirdPersonShaderWeaponGrenadeLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2378 |
| `cg_thirdPersonShaderWeaponHeavyMachineGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2388 |
| `cg_thirdPersonShaderWeaponLightningGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2380 |
| `cg_thirdPersonShaderWeaponMachineGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2376 |
| `cg_thirdPersonShaderWeaponNailGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2385 |
| `cg_thirdPersonShaderWeaponPlasmaGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2382 |
| `cg_thirdPersonShaderWeaponProximityLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2386 |
| `cg_thirdPersonShaderWeaponRailGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2381 |
| `cg_thirdPersonShaderWeaponRocketLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2379 |
| `cg_thirdPersonShaderWeaponShotgun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2377 |
| `cg_thirdPersonUseEntityAngles` | `1` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1676 |
| `cg_tracerChance` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1656 |
| `cg_tracerLength` | `100` | CVAR_ARCHIVE | cgame/cg_main.c:1658 |
| `cg_tracerWidth` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1657 |
| `cg_useCustomRedBlueFlagColor` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2162 |
| `cg_useCustomRedBlueModels` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2160 |
| `cg_useCustomRedBlueRail` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2161 |
| `cg_useDefaultTeamSkins` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2164 |
| `cg_useDemoFov` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2607 |
| `cg_useOriginalInterpolation` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2085 |
| `cg_useScoresUpdateTeam` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2612 |
| `cg_vibrate` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2405 |
| `cg_vibrateForce` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:2408 |
| `cg_vibrateMaxDistance` | `800` | CVAR_ARCHIVE | cgame/cg_main.c:2407 |
| `cg_vibrateTime` | `150.0` | CVAR_ARCHIVE | cgame/cg_main.c:2406 |
| `cg_warmupTime` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2447 |
| `cg_waterWarp` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2421 |
| `cg_weaponBar` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1935 |
| `cg_weaponBarFont` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1938 |
| `cg_weaponBarPointSize` | `24` | CVAR_ARCHIVE | cgame/cg_main.c:1939 |
| `cg_weaponBarWideScreen` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1940 |
| `cg_weaponBarX` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1936 |
| `cg_weaponBarY` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1937 |
| `cg_weaponBFG` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2353 |
| `cg_weaponChainGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2357 |
| `cg_weaponDefault` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2342 |
| `cg_weaponGauntlet` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2344 |
| `cg_weaponGrapplingHook` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2354 |
| `cg_weaponGrenadeLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2348 |
| `cg_weaponHeavyMachineGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2358 |
| `cg_weaponLightningGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2350 |
| `cg_weaponMachineGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2346 |
| `cg_weaponNailGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2355 |
| `cg_weaponNone` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2343 |
| `cg_weaponPlasmaGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2352 |
| `cg_weaponProximityLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2356 |
| `cg_weaponRailGun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2351 |
| `cg_weaponRocketLauncher` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2349 |
| `cg_weaponShotgun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2345 |
| `cg_weaponShotgun` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2347 |
| `cg_wh` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2074 |
| `cg_whAlpha` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:2080 |
| `cg_whColor` | `0xffffff` | CVAR_ARCHIVE | cgame/cg_main.c:2079 |
| `cg_whEnemyAlpha` | `30` | CVAR_ARCHIVE | cgame/cg_main.c:2083 |
| `cg_whEnemyColor` | `0xaf1f00` | CVAR_ARCHIVE | cgame/cg_main.c:2082 |
| `cg_whEnemyShader` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2081 |
| `cg_whIncludeDeadBody` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2075 |
| `cg_whIncludeProjectile` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2076 |
| `cg_whShader` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:2077 |
| `cg_wideScreen` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:2463 |
| `cg_wideScreenScoreBoardHack` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2464 |
| `cg_winLossMusic` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2588 |
| `cg_zoomBroken` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1376 |
| `cg_zoomFov` | `60` | CVAR_ARCHIVE | cgame/cg_main.c:1373 |
| `cg_zoomIgnoreTimescale` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1375 |
| `cg_zoomTime` | `150` | CVAR_ARCHIVE | cgame/cg_main.c:1374 |
| `cgr_bfgAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2571 |
| `cgr_bfgHave` | `0` | CVAR_ROM | cgame/cg_main.c:2557 |
| `cgr_chainGunAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2575 |
| `cgr_chainGunHave` | `0` | CVAR_ROM | cgame/cg_main.c:2561 |
| `cgr_gauntletAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2563 |
| `cgr_gauntletHave` | `0` | CVAR_ROM | cgame/cg_main.c:2549 |
| `cgr_grappleAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2572 |
| `cgr_grappleHave` | `0` | CVAR_ROM | cgame/cg_main.c:2558 |
| `cgr_grenadeLauncherAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2566 |
| `cgr_grenadeLauncherHave` | `0` | CVAR_ROM | cgame/cg_main.c:2552 |
| `cgr_lightningGunAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2568 |
| `cgr_lightningGunHave` | `0` | CVAR_ROM | cgame/cg_main.c:2554 |
| `cgr_machineGunAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2564 |
| `cgr_machineGunHave` | `0` | CVAR_ROM | cgame/cg_main.c:2550 |
| `cgr_nailGunAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2573 |
| `cgr_nailGunHave` | `0` | CVAR_ROM | cgame/cg_main.c:2559 |
| `cgr_plasmaGunAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2570 |
| `cgr_plasmaGunHave` | `0` | CVAR_ROM | cgame/cg_main.c:2556 |
| `cgr_proximityLauncherAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2574 |
| `cgr_proximityLauncherHave` | `0` | CVAR_ROM | cgame/cg_main.c:2560 |
| `cgr_railGunAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2569 |
| `cgr_railGunHave` | `0` | CVAR_ROM | cgame/cg_main.c:2555 |
| `cgr_rocketLauncherAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2567 |
| `cgr_rocketLauncherHave` | `0` | CVAR_ROM | cgame/cg_main.c:2553 |
| `cgr_selectedWeapon` | `0` | CVAR_ROM | cgame/cg_main.c:2577 |
| `cgr_shotgunAmmo` | `0` | CVAR_ROM | cgame/cg_main.c:2565 |
| `cgr_shotgunHave` | `0` | CVAR_ROM | cgame/cg_main.c:2551 |
| `cl_aviAllowLargeFiles` | `1` | CVAR_ARCHIVE | client/cl_main.c:6971 |
| `cl_aviAudioMatchVideoLength` | `1` | CVAR_ARCHIVE | client/cl_main.c:6978 |
| `cl_aviAudioWaitForVideoFrame` | `1` | CVAR_ARCHIVE | client/cl_main.c:6977 |
| `cl_aviCodec` | `uncompressed` | CVAR_ARCHIVE | client/cl_main.c:6970 |
| `cl_aviExtension` | `avi` | CVAR_ARCHIVE | client/cl_main.c:6973 |
| `cl_aviFetchMode` | `GL_RGB` | CVAR_ARCHIVE | client/cl_main.c:6972 |
| `cl_aviFrameRateDivider` | `1` | CVAR_ARCHIVE | client/cl_main.c:6969 |
| `cl_aviNoAudioHWOutput` | `1` | CVAR_ARCHIVE | client/cl_main.c:6976 |
| `cl_aviPipeCommand` | `-threads 0 -c:a aac -c:v libx264 -preset ultrafast -y -pix_fmt yuv420p -crf 19` | CVAR_ARCHIVE | client/cl_main.c:6974 |
| `cl_aviPipeExtension` | `mkv` | CVAR_ARCHIVE | client/cl_main.c:6975 |
| `cl_cinematicIgnoreSeek` | `0` | CVAR_ARCHIVE | client/cl_main.c:7018 |
| `cl_consoleAsChat` | `0` | CVAR_ARCHIVE | client/cl_main.c:7120 |
| `cl_demoFile` | `""` | CVAR_ROM | client/cl_main.c:7139 |
| `cl_demoFileBaseName` | `""` | CVAR_ROM | client/cl_main.c:7140 |
| `cl_demoFileCheckSystem` | `2` | CVAR_ARCHIVE | client/cl_main.c:7138 |
| `cl_downloadWorkshops` | `1` | CVAR_ARCHIVE | client/cl_main.c:7141 |
| `cl_freezeDemoPauseMusic` | `1` | CVAR_ARCHIVE | client/cl_main.c:6981 |
| `cl_freezeDemoPauseVideoRecording` | `0` | CVAR_ARCHIVE | client/cl_main.c:6980 |
| `cl_keepDemoFileInMemory` | `1` | CVAR_ARCHIVE | client/cl_main.c:7137 |
| `cl_maxRewindBackups` | `12` | CVAR_ARCHIVE \| CVAR_LATCH | client/cl_main.c:7123 |
| `cl_numberPadInput` | `0` | CVAR_ARCHIVE | client/cl_main.c:7121 |
| `cl_useq3gibs` | `0` | CVAR_ARCHIVE | client/cl_main.c:7119 |
| `cl_voipGainOtherPlayback` | `0.2` | CVAR_ARCHIVE | client/cl_main.c:7105 |
| `cl_voipOverallGain` | `1.0` | CVAR_ARCHIVE | client/cl_main.c:7104 |
| `cl_volumeShowMeter` | `0` | CVAR_ARCHIVE | client/cl_main.c:7142 |
| `com_autoWriteConfig` | `2` | CVAR_ARCHIVE | qcommon/common.c:3135 |
| `com_brokenDemo` | `0` | CVAR_INIT | qcommon/common.c:3139 |
| `com_execVerbose` | `0` | CVAR_ARCHIVE | qcommon/common.c:3136 |
| `com_idleSleep` | `1` | CVAR_ARCHIVE | qcommon/common.c:3138 |
| `com_logo` | `0` | CVAR_ARCHIVE | qcommon/common.c:3118 |
| `com_qlColors` | `1` | CVAR_ARCHIVE | qcommon/common.c:3137 |
| `com_timescaleSafe` | `1` | CVAR_ARCHIVE | qcommon/common.c:3090 |
| `com_workshopids` | `""` | CVAR_ROM | qcommon/common.c:3141 |
| `com_workshopids` | `""` | 0 | qcommon/files.c:3536 |
| `con_conspeed` | `3` | CVAR_ARCHIVE | client/cl_console.c:499 |
| `con_fracSize` | `0` | CVAR_ARCHIVE | client/cl_console.c:502 |
| `con_lineWidth` | `""` | CVAR_ARCHIVE | client/cl_console.c:507 |
| `con_rgb` | `""` | CVAR_ARCHIVE | client/cl_console.c:503 |
| `con_scaleNotify` | `1.0` | CVAR_ARCHIVE | client/cl_console.c:506 |
| `con_transparency` | `0.04` | CVAR_ARCHIVE | client/cl_console.c:501 |
| `debug_protocol` | `""` | 0 | q3_ui/ui_servers2.c:1610 |
| `debug_protocol` | `""` | 0 | ui/ui_main.c:5210 |
| `fs_quakelivedir` | `""` | CVAR_INIT | qcommon/files.c:3658 |
| `fs_searchWorkshops` | `1` | CVAR_ARCHIVE | qcommon/files.c:3659 |
| `fs_steamcmd` | `""` | CVAR_ARCHIVE | qcommon/files.c:3660 |
| `g_training` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2420 |
| `in_checkForStolenMouseFocus` | `0` | CVAR_ARCHIVE | sdl/sdl_input.c:1333 |
| `mme_blurFrames` | `0` | CVAR_ARCHIVE | renderercommon/tr_mme.c:367 |
| `mme_blurJitter` | `1` | CVAR_ARCHIVE | renderercommon/tr_mme.c:370 |
| `mme_blurOverlap` | `0` | CVAR_ARCHIVE | renderercommon/tr_mme.c:368 |
| `mme_blurStrength` | `0` | CVAR_ARCHIVE | renderercommon/tr_mme.c:371 |
| `mme_blurType` | `gaussian` | CVAR_ARCHIVE | renderercommon/tr_mme.c:369 |
| `mme_cpuSSE2` | `0` | CVAR_ARCHIVE | renderercommon/tr_mme.c:377 |
| `mme_depthFocus` | `0` | CVAR_ARCHIVE | renderercommon/tr_mme.c:380 |
| `mme_depthRange` | `2000` | CVAR_ARCHIVE | renderercommon/tr_mme.c:379 |
| `mme_dofFrames` | `0` | CVAR_ARCHIVE | renderercommon/tr_mme.c:373 |
| `mme_dofRadius` | `2` | CVAR_ARCHIVE | renderercommon/tr_mme.c:374 |
| `mme_dofVisualize` | `0` | CVAR_TEMP | renderercommon/tr_mme.c:375 |
| `mme_saveDepth` | `0` | CVAR_ARCHIVE | renderercommon/tr_mme.c:382 |
| `r_allowSoftwareGLCoreContext` | `0` | CVAR_LATCH | sdl/sdl_glimp.c:1336 |
| `r_colorSkinsFuzz` | `20` | CVAR_ARCHIVE | renderergl1/tr_image.c:1814 |
| `r_colorSkinsFuzz` | `20` | CVAR_ARCHIVE | renderergl2/tr_image.c:3385 |
| `r_colorSkinsIntensity` | `1.0` | CVAR_ARCHIVE | renderergl1/tr_image.c:1815 |
| `r_colorSkinsIntensity` | `1.0` | CVAR_ARCHIVE | renderergl2/tr_image.c:3386 |
| `r_fboStencil` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_glimp.c:1344 |
| `r_useCoreContext` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_glimp.c:1337 |
| `r_visibleWindowHeight` | `""` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_glimp.c:1343 |
| `r_visibleWindowWidth` | `""` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_glimp.c:1342 |
| `s_sdlWindowsForceDirectSound` | `1` | CVAR_ARCHIVE | sdl/sdl_snd.c:224 |
| `sv_broadcastAll` | `0` | CVAR_ARCHIVE | server/sv_init.c:690 |
| `sv_randomClientSlot` | `1` | CVAR_ARCHIVE | server/sv_init.c:691 |
| `ui_demoSortDirFirst` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:229 |
| `ui_demoStayInFolder` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:230 |
| `ui_doubleClickTime` | `500` | CVAR_ARCHIVE | q3_ui/ui_main.c:228 |
| `wolfcam_drawFollowing` | `2` | CVAR_ARCHIVE | cgame/cg_main.c:2222 |
| `wolfcam_drawFollowingOnlyName` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2223 |
| `wolfcam_firstPersonSwitchSoundStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2063 |
| `wolfcam_fixedViewAngles` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2084 |
| `wolfcam_hoverTime` | `2000` | CVAR_ARCHIVE | cgame/cg_main.c:2060 |
| `wolfcam_painHealth` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2064 |
| `wolfcam_painHealthAlpha` | `255` | CVAR_ARCHIVE | cgame/cg_main.c:2066 |
| `wolfcam_painHealthColor` | `0xff00ff` | CVAR_ARCHIVE | cgame/cg_main.c:2065 |
| `wolfcam_painHealthFade` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2067 |
| `wolfcam_painHealthFadeTime` | `4000` | CVAR_ARCHIVE | cgame/cg_main.c:2068 |
| `wolfcam_painHealthStyle` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2070 |
| `wolfcam_painHealthValidTime` | `5000` | CVAR_ARCHIVE | cgame/cg_main.c:2069 |
| `wolfcam_switchMode` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:2061 |

*Count:* **1065**

---

## C. Cvars — inherited from Q3/ioquake3

Name appears in the ioquake3 baseline. Default value / flags may still differ from upstream.

| Name | Default | Flags | Source |
|------|---------|-------|--------|
| `activeAction` | `""` | CVAR_TEMP | client/cl_main.c:6963 |
| `bot_aasoptimize` | `0` | 0 | server/sv_bot.c:495 |
| `bot_challenge` | `0` | 0 | game/ai_dmq3.c:5435 |
| `bot_challenge` | `0` | 0 | server/sv_bot.c:509 |
| `bot_debug` | `0` | 0 | server/sv_bot.c:104 |
| `bot_debug` | `0` | CVAR_CHEAT | server/sv_bot.c:487 |
| `bot_developer` | `0` | CVAR_CHEAT | game/ai_main.c:1680 |
| `bot_developer` | `0` | CVAR_CHEAT | server/sv_bot.c:486 |
| `bot_enable` | `1` | 0 | server/sv_bot.c:485 |
| `bot_enable` | `1` | CVAR_LATCH | server/sv_game.c:934 |
| `bot_fastchat` | `0` | 0 | game/ai_dmq3.c:5432 |
| `bot_fastchat` | `0` | 0 | server/sv_bot.c:503 |
| `bot_forceclustering` | `0` | 0 | server/sv_bot.c:492 |
| `bot_forcereachability` | `0` | 0 | server/sv_bot.c:493 |
| `bot_forcewrite` | `0` | 0 | server/sv_bot.c:494 |
| `bot_grapple` | `0` | 0 | game/ai_dmq3.c:5431 |
| `bot_grapple` | `0` | 0 | server/sv_bot.c:507 |
| `bot_groundonly` | `1` | 0 | server/sv_bot.c:110 |
| `bot_groundonly` | `1` | 0 | server/sv_bot.c:489 |
| `bot_highlightarea` | `0` | 0 | server/sv_bot.c:112 |
| `bot_interbreedbots` | `10` | 0 | game/ai_main.c:1682 |
| `bot_interbreedbots` | `10` | CVAR_CHEAT | server/sv_bot.c:512 |
| `bot_interbreedchar` | `""` | 0 | game/ai_main.c:1681 |
| `bot_interbreedchar` | `""` | CVAR_CHEAT | server/sv_bot.c:511 |
| `bot_interbreedcycle` | `20` | 0 | game/ai_main.c:1683 |
| `bot_interbreedcycle` | `20` | CVAR_CHEAT | server/sv_bot.c:513 |
| `bot_interbreedwrite` | `""` | 0 | game/ai_main.c:1684 |
| `bot_interbreedwrite` | `""` | CVAR_CHEAT | server/sv_bot.c:514 |
| `bot_maxdebugpolys` | `2` | 0 | server/sv_bot.c:488 |
| `bot_memorydump` | `0` | CVAR_CHEAT | game/ai_main.c:1674 |
| `bot_minplayers` | `0` | CVAR_SERVERINFO | game/g_bot.c:1019 |
| `bot_minplayers` | `0` | 0 | server/sv_bot.c:510 |
| `bot_nochat` | `0` | 0 | game/ai_dmq3.c:5433 |
| `bot_nochat` | `0` | 0 | server/sv_bot.c:504 |
| `bot_pause` | `0` | CVAR_CHEAT | game/ai_main.c:1676 |
| `bot_pause` | `0` | CVAR_CHEAT | server/sv_bot.c:505 |
| `bot_predictobstacles` | `1` | 0 | game/ai_dmq3.c:5436 |
| `bot_reachability` | `0` | 0 | server/sv_bot.c:108 |
| `bot_reachability` | `0` | 0 | server/sv_bot.c:490 |
| `bot_reloadcharacters` | `0` | 0 | server/sv_bot.c:498 |
| `bot_report` | `0` | CVAR_CHEAT | game/ai_main.c:1677 |
| `bot_report` | `0` | CVAR_CHEAT | server/sv_bot.c:506 |
| `bot_rocketjump` | `1` | 0 | game/ai_dmq3.c:5430 |
| `bot_rocketjump` | `1` | 0 | server/sv_bot.c:508 |
| `bot_saveroutingcache` | `0` | CVAR_CHEAT | game/ai_main.c:1675 |
| `bot_saveroutingcache` | `0` | 0 | server/sv_bot.c:496 |
| `bot_testclusters` | `0` | CVAR_CHEAT | game/ai_main.c:1679 |
| `bot_testclusters` | `0` | CVAR_CHEAT | server/sv_bot.c:502 |
| `bot_testichat` | `0` | 0 | server/sv_bot.c:499 |
| `bot_testrchat` | `0` | 0 | game/ai_dmq3.c:5434 |
| `bot_testrchat` | `0` | 0 | server/sv_bot.c:500 |
| `bot_testsolid` | `0` | CVAR_CHEAT | game/ai_main.c:1678 |
| `bot_testsolid` | `0` | CVAR_CHEAT | server/sv_bot.c:501 |
| `bot_thinktime` | `100` | CVAR_CHEAT | game/ai_main.c:1673 |
| `bot_thinktime` | `100` | CVAR_CHEAT | server/sv_bot.c:497 |
| `bot_visualizejumppads` | `0` | CVAR_CHEAT | server/sv_bot.c:491 |
| `capturelimit` | `8` | CVAR_SERVERINFO \| CVAR_ARCHIVE \| CVAR_NORESTART | ui/ui_main.c:5875 |
| `cg_animspeed` | `1` | CVAR_CHEAT | cgame/cg_main.c:1646 |
| `cg_autoswitch` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1371 |
| `cg_autoswitch` | `0` | CVAR_ARCHIVE | client/cl_main.c:7024 |
| `cg_bobpitch` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1643 |
| `cg_bobroll` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1644 |
| `cg_bobup` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1642 |
| `cg_brassTime` | `2500` | CVAR_ARCHIVE | cgame/cg_main.c:1592 |
| `cg_brassTime` | `2500` | CVAR_ARCHIVE | q3_ui/ui_main.c:202 |
| `cg_brassTime` | `2500` | CVAR_ARCHIVE | ui/ui_main.c:5789 |
| `cg_cameraOrbit` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1789 |
| `cg_cameraOrbitDelay` | `50` | CVAR_ARCHIVE | cgame/cg_main.c:1790 |
| `cg_crosshairHealth` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1583 |
| `cg_crosshairSize` | `32` | CVAR_ARCHIVE | cgame/cg_main.c:1580 |
| `cg_crosshairX` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1587 |
| `cg_crosshairY` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1588 |
| `cg_currentSelectedPlayer` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1778 |
| `cg_currentSelectedPlayerName` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1779 |
| `cg_debuganim` | `0` | CVAR_CHEAT | cgame/cg_main.c:1647 |
| `cg_debugevents` | `0` | CVAR_CHEAT | cgame/cg_main.c:1649 |
| `cg_debugposition` | `0` | CVAR_CHEAT | cgame/cg_main.c:1648 |
| `cg_deferPlayers` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1688 |
| `cg_deferPlayers` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1690 |
| `cg_draw3dIcons` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1476 |
| `cg_drawAmmoWarning` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1479 |
| `cg_drawAttacker` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1512 |
| `cg_drawCrosshair` | `5` | CVAR_ARCHIVE | cgame/cg_main.c:1528 |
| `cg_drawCrosshair` | `5` | CVAR_ARCHIVE | q3_ui/ui_main.c:203 |
| `cg_drawCrosshair` | `4` | CVAR_ARCHIVE | ui/ui_main.c:5790 |
| `cg_drawCrosshairNames` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1531 |
| `cg_drawCrosshairNames` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:204 |
| `cg_drawCrosshairNames` | `1` | CVAR_ARCHIVE | ui/ui_main.c:5791 |
| `cg_drawFPS` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1448 |
| `cg_drawFriend` | `3` | CVAR_ARCHIVE | cgame/cg_main.c:1747 |
| `cg_drawGun` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1372 |
| `cg_drawIcons` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1477 |
| `cg_drawRewards` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1561 |
| `cg_drawSnapshot` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1464 |
| `cg_drawStatus` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1419 |
| `cg_drawTeamOverlay` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1692 |
| `cg_drawTimer` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1421 |
| `cg_errordecay` | `100` | 0 | cgame/cg_main.c:1651 |
| `cg_footsteps` | `1` | CVAR_CHEAT | cgame/cg_main.c:1655 |
| `cg_forceModel` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1683 |
| `cg_gibs` | `15` | CVAR_ARCHIVE | cgame/cg_main.c:1387 |
| `cg_gunX` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1636 |
| `cg_gunY` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1637 |
| `cg_gunZ` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1638 |
| `cg_hudFiles` | `ui/hud.txt` | CVAR_ARCHIVE | cgame/cg_main.c:1787 |
| `cg_hudFiles` | `ui/hud.txt` | CVAR_ARCHIVE | ui/ui_main.c:5871 |
| `cg_ignore` | `0` | 0 | cgame/cg_main.c:1370 |
| `cg_lagometer` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1605 |
| `cg_marks` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1600 |
| `cg_marks` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:205 |
| `cg_marks` | `1` | CVAR_ARCHIVE | ui/ui_main.c:5792 |
| `cg_noplayeranims` | `0` | CVAR_CHEAT | cgame/cg_main.c:1653 |
| `cg_nopredict` | `0` | 0 | cgame/cg_main.c:1652 |
| `cg_noProjectileTrail` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1834 |
| `cg_noTaunt` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1832 |
| `cg_noVoiceChats` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1765 |
| `cg_noVoiceText` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1766 |
| `cg_oldRocket` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1837 |
| `cg_predictItems` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1686 |
| `cg_predictItems` | `1` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7085 |
| `cg_railTrailTime` | `400` | CVAR_ARCHIVE | cgame/cg_main.c:1624 |
| `cg_scorePlums` | `1` | CVAR_USERINFO \| CVAR_ARCHIVE | cgame/cg_main.c:1794 |
| `cg_selectedPlayer` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5840 |
| `cg_selectedPlayerName` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5841 |
| `cg_shadows` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1385 |
| `cg_showmiss` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1654 |
| `cg_simpleItems` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1593 |
| `cg_smoothClients` | `0` | CVAR_USERINFO \| CVAR_ARCHIVE | cgame/cg_main.c:1811 |
| `cg_stats` | `0` | 0 | cgame/cg_main.c:1746 |
| `cg_stereoSeparation` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1384 |
| `cg_stereoSeparation` | `0` | CVAR_ROM | client/cl_main.c:7117 |
| `cg_swingSpeed` | `0.3` | CVAR_CHEAT | cgame/cg_main.c:1645 |
| `cg_teamChatHeight` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1682 |
| `cg_teamChatsOnly` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1763 |
| `cg_teamChatTime` | `3000` | CVAR_ARCHIVE | cgame/cg_main.c:1681 |
| `cg_thirdPerson` | `0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1677 |
| `cg_thirdPersonAngle` | `0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1661 |
| `cg_thirdPersonRange` | `80` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1660 |
| `cg_timescaleFadeEnd` | `1` | 0 | cgame/cg_main.c:1791 |
| `cg_timescaleFadeSpeed` | `0` | 0 | cgame/cg_main.c:1792 |
| `cg_trueLightning` | `1.0` | CVAR_ARCHIVE | cgame/cg_main.c:1840 |
| `cg_viewsize` | `100` | CVAR_ARCHIVE | cgame/cg_main.c:1383 |
| `cg_viewsize` | `100` | CVAR_ARCHIVE | client/cl_main.c:7115 |
| `cl_allowDownload` | `0` | CVAR_ARCHIVE | client/cl_main.c:7008 |
| `cl_anglespeedkey` | `1.5` | 0 | client/cl_main.c:6988 |
| `cl_anonymous` | `0` | CVAR_INIT\|CVAR_SYSTEMINFO | client/cl_main.c:3929 |
| `cl_anonymous` | `0` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7082 |
| `cl_autoRecordDemo` | `0` | CVAR_ARCHIVE | client/cl_main.c:6967 |
| `cl_aviFrameRate` | `50` | CVAR_ARCHIVE | client/cl_main.c:6968 |
| `cl_consoleKeys` | `~ ` 0x7e 0x60` | CVAR_ARCHIVE | client/cl_main.c:7065 |
| `cl_conXOffset` | `0` | 0 | client/cl_main.c:7010 |
| `cl_debugMove` | `0` | 0 | client/cl_input.c:1022 |
| `cl_forceavidemo` | `0` | 0 | client/cl_main.c:6982 |
| `cl_freelook` | `1` | CVAR_ARCHIVE | client/cl_main.c:6996 |
| `cl_freezeDemo` | `0` | CVAR_TEMP | client/cl_main.c:6961 |
| `cl_guid` | `""` | CVAR_USERINFO \| CVAR_ROM | client/cl_main.c:7205 |
| `cl_guidServerUniq` | `1` | CVAR_ARCHIVE | client/cl_main.c:7061 |
| `cl_lanForcePackets` | `1` | CVAR_ARCHIVE | client/cl_main.c:7059 |
| `cl_maxpackets` | `30` | CVAR_ARCHIVE | client/cl_main.c:6990 |
| `cl_maxPing` | `800` | CVAR_ARCHIVE | client/cl_main.c:7057 |
| `cl_motd` | `1` | 0 | client/cl_main.c:6952 |
| `cl_motdString` | `""` | CVAR_ROM | client/cl_main.c:7055 |
| `cl_mouseAccel` | `0` | CVAR_ARCHIVE | client/cl_main.c:6995 |
| `cl_mouseAccelOffset` | `5` | CVAR_ARCHIVE | client/cl_main.c:7003 |
| `cl_mouseAccelStyle` | `0` | CVAR_ARCHIVE | client/cl_main.c:7000 |
| `cl_mumbleScale` | `0.0254` | CVAR_ARCHIVE | client/cl_main.c:7089 |
| `cl_nodelta` | `0` | 0 | client/cl_input.c:1021 |
| `cl_noprint` | `0` | 0 | client/cl_main.c:6950 |
| `cl_packetdelay` | `0` | CVAR_CHEAT | qcommon/common.c:3099 |
| `cl_packetdup` | `1` | CVAR_ARCHIVE | client/cl_main.c:6991 |
| `cl_paused` | `0` | CVAR_ROM | cgame/cg_main.c:1771 |
| `cl_paused` | `0` | CVAR_ROM | qcommon/common.c:3097 |
| `cl_pitchspeed` | `140` | CVAR_ARCHIVE | client/cl_main.c:6987 |
| `cl_renderer` | `opengl1` | CVAR_ARCHIVE \| CVAR_LATCH | client/cl_main.c:5951 |
| `cl_run` | `1` | CVAR_ARCHIVE | client/cl_main.c:6993 |
| `cl_running` | `0` | CVAR_ROM | qcommon/common.c:3102 |
| `cl_serverStatusResendTime` | `750` | 0 | client/cl_main.c:7020 |
| `cl_showmouserate` | `0` | 0 | client/cl_main.c:7006 |
| `cl_shownet` | `0` | CVAR_TEMP | client/cl_main.c:6958 |
| `cl_shownet` | `0` | CVAR_TEMP | null/null_client.c:33 |
| `cl_showSend` | `0` | CVAR_TEMP | client/cl_main.c:6959 |
| `cl_showTimeDelta` | `0` | CVAR_TEMP | client/cl_main.c:6960 |
| `cl_timedemoLog` | `""` | CVAR_ARCHIVE | client/cl_main.c:6966 |
| `cl_timeNudge` | `0` | CVAR_TEMP | client/cl_main.c:6957 |
| `cl_timeout` | `200` | 0 | client/cl_main.c:6955 |
| `cl_useMumble` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | client/cl_main.c:7088 |
| `cl_voip` | `1` | CVAR_ARCHIVE | client/cl_main.c:7101 |
| `cl_voipCaptureMult` | `2.0` | CVAR_ARCHIVE | client/cl_main.c:7096 |
| `cl_voipGainDuringCapture` | `0.2` | CVAR_ARCHIVE | client/cl_main.c:7095 |
| `cl_voipSend` | `0` | 0 | client/cl_main.c:7093 |
| `cl_voipSendTarget` | `spatial` | 0 | client/cl_main.c:7094 |
| `cl_voipShowMeter` | `1` | CVAR_ARCHIVE | client/cl_main.c:7099 |
| `cl_voipUseVAD` | `0` | CVAR_ARCHIVE | client/cl_main.c:7097 |
| `cl_voipVADThreshold` | `0.25` | CVAR_ARCHIVE | client/cl_main.c:7098 |
| `cl_yawspeed` | `140` | CVAR_ARCHIVE | client/cl_main.c:6986 |
| `cm_debugSize` | `2` | 0 | qcommon/cm_patch.c:1642 |
| `cm_noAreas` | `0` | CVAR_CHEAT | qcommon/cm_load.c:595 |
| `cm_noCurves` | `0` | CVAR_CHEAT | qcommon/cm_load.c:596 |
| `cm_playerCurveClip` | `1` | CVAR_ARCHIVE\|CVAR_CHEAT | qcommon/cm_load.c:597 |
| `color1` | `4` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7077 |
| `color2` | `5` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7078 |
| `com_abnormalExit` | `0` | CVAR_ROM | qcommon/common.c:3110 |
| `com_altivec` | `1` | CVAR_ARCHIVE | qcommon/common.c:3076 |
| `com_ansiColor` | `1` | CVAR_ARCHIVE | qcommon/common.c:3104 |
| `com_blood` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1772 |
| `com_blood` | `1` | CVAR_ARCHIVE | qcommon/common.c:3085 |
| `com_buildScript` | `0` | 0 | cgame/cg_main.c:1770 |
| `com_buildScript` | `0` | 0 | qcommon/common.c:3103 |
| `com_cameraMode` | `0` | CVAR_CHEAT | cgame/cg_main.c:1812 |
| `com_cameraMode` | `0` | CVAR_CHEAT | qcommon/common.c:3095 |
| `com_errorMessage` | `""` | CVAR_ROM \| CVAR_NORESTART | qcommon/common.c:3112 |
| `com_homepath` | `""` | CVAR_INIT\|CVAR_PROTECTED | qcommon/common.c:3039 |
| `com_introplayed` | `1` | CVAR_ARCHIVE | qcommon/common.c:3115 |
| `com_maxfps` | `0` | CVAR_ARCHIVE | qcommon/common.c:3081 |
| `com_maxfps` | `125` | CVAR_ARCHIVE | qcommon/common.c:3083 |
| `com_maxfpsMinimized` | `0` | CVAR_ARCHIVE | qcommon/common.c:3109 |
| `com_maxfpsUnfocused` | `0` | CVAR_ARCHIVE | qcommon/common.c:3107 |
| `com_minimized` | `0` | CVAR_ROM | qcommon/common.c:3108 |
| `com_pipefile` | `""` | CVAR_ARCHIVE\|CVAR_LATCH | qcommon/common.c:3211 |
| `com_showtrace` | `0` | CVAR_CHEAT | qcommon/common.c:3092 |
| `com_speeds` | `0` | 0 | qcommon/common.c:3093 |
| `com_standalone` | `0` | CVAR_ROM | qcommon/common.c:3037 |
| `com_unfocused` | `0` | CVAR_ROM | qcommon/common.c:3106 |
| `con_autoclear` | `1` | CVAR_ARCHIVE | client/cl_console.c:500 |
| `con_notifylines` | `3` | CVAR_ARCHIVE | client/cl_console.c:497 |
| `con_notifytime` | `3` | CVAR_ARCHIVE | client/cl_console.c:496 |
| `con_scale` | `1.0` | CVAR_ARCHIVE | client/cl_console.c:504 |
| `debuggraph` | `0` | CVAR_CHEAT | client/cl_scrn.c:526 |
| `dedicated` | `1` | CVAR_INIT | qcommon/common.c:3060 |
| `dedicated` | `0` | CVAR_LATCH | qcommon/common.c:3063 |
| `dedicated` | `0` | 0 | qcommon/common.c:3637 |
| `developer` | `0` | CVAR_TEMP | qcommon/common.c:3032 |
| `dmflags` | `0` | CVAR_SERVERINFO | server/sv_init.c:633 |
| `fixedtime` | `0` | CVAR_CHEAT | qcommon/common.c:3091 |
| `fraglimit` | `20` | CVAR_SERVERINFO | server/sv_init.c:634 |
| `fs_basegame` | `""` | CVAR_INIT | qcommon/files.c:3657 |
| `fs_debug` | `0` | 0 | qcommon/files.c:3655 |
| `fs_game` | `wolfcam-ql` | CVAR_INIT\|CVAR_SYSTEMINFO | qcommon/files.c:3665 |
| `fs_homepath` | `""` | CVAR_INIT\|CVAR_PROTECTED | qcommon/files.c:3638 |
| `g_arenasFile` | `""` | CVAR_INIT\|CVAR_ROM | game/g_bot.c:163 |
| `g_arenasFile` | `""` | CVAR_INIT\|CVAR_ROM | q3_ui/ui_gameinfo.c:182 |
| `g_arenasFile` | `""` | CVAR_INIT\|CVAR_ROM | q3_ui/ui_main.c:183 |
| `g_arenasFile` | `""` | CVAR_INIT\|CVAR_ROM | ui/ui_gameinfo.c:146 |
| `g_arenasFile` | `""` | CVAR_INIT\|CVAR_ROM | ui/ui_main.c:5771 |
| `g_botsFile` | `""` | CVAR_INIT\|CVAR_ROM | game/g_bot.c:947 |
| `g_botsFile` | `""` | CVAR_INIT\|CVAR_ROM | q3_ui/ui_gameinfo.c:369 |
| `g_botsFile` | `""` | CVAR_INIT\|CVAR_ROM | q3_ui/ui_main.c:184 |
| `g_botsFile` | `""` | CVAR_INIT\|CVAR_ROM | ui/ui_gameinfo.c:269 |
| `g_botsFile` | `""` | CVAR_INIT\|CVAR_ROM | ui/ui_main.c:5772 |
| `g_enableBreath` | `0` | CVAR_SERVERINFO | cgame/cg_main.c:1782 |
| `g_enableDust` | `0` | CVAR_SERVERINFO | cgame/cg_main.c:1781 |
| `g_gametype` | `0` | CVAR_SERVERINFO \| CVAR_USERINFO \| CVAR_LATCH | server/sv_ccmds.c:223 |
| `g_gametype` | `0` | CVAR_SERVERINFO \| CVAR_LATCH | server/sv_init.c:636 |
| `g_obeliskRespawnDelay` | `10` | CVAR_SERVERINFO | cgame/cg_main.c:1786 |
| `g_spAwards` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:190 |
| `g_spAwards` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5778 |
| `g_spScores1` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:185 |
| `g_spScores1` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5773 |
| `g_spScores2` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:186 |
| `g_spScores2` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5774 |
| `g_spScores3` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:187 |
| `g_spScores3` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5775 |
| `g_spScores4` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:188 |
| `g_spScores4` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5776 |
| `g_spScores5` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:189 |
| `g_spScores5` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5777 |
| `g_spSkill` | `2` | 0 | game/ai_dmq3.c:5437 |
| `g_spSkill` | `2` | CVAR_ARCHIVE \| CVAR_LATCH | q3_ui/ui_main.c:192 |
| `g_spSkill` | `2` | CVAR_ARCHIVE | ui/ui_main.c:5780 |
| `g_spVideos` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:191 |
| `g_spVideos` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5779 |
| `g_synchronousClients` | `0` | CVAR_SYSTEMINFO | cgame/cg_main.c:1774 |
| `g_warmup` | `20` | CVAR_ARCHIVE | ui/ui_main.c:5874 |
| `graphheight` | `32` | CVAR_CHEAT | client/cl_scrn.c:527 |
| `graphscale` | `1` | CVAR_CHEAT | client/cl_scrn.c:528 |
| `graphshift` | `0` | CVAR_CHEAT | client/cl_scrn.c:529 |
| `handicap` | `100` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7079 |
| `headmodel` | `sarge` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7072 |
| `in_availableJoysticks` | `""` | CVAR_ROM | sdl/sdl_input.c:518 |
| `in_joystick` | `0` | CVAR_ARCHIVE\|CVAR_LATCH | sdl/sdl_input.c:1335 |
| `in_joystickNo` | `0` | CVAR_ARCHIVE | sdl/sdl_input.c:529 |
| `in_joystickUseAnalog` | `0` | CVAR_ARCHIVE | sdl/sdl_input.c:533 |
| `in_keyboardDebug` | `0` | CVAR_ARCHIVE | sdl/sdl_input.c:1328 |
| `in_mouse` | `1` | CVAR_ARCHIVE | sdl/sdl_input.c:1331 |
| `in_nograb` | `0` | CVAR_ARCHIVE | sdl/sdl_input.c:1332 |
| `j_forward` | `-0.25` | CVAR_ARCHIVE | client/cl_main.c:7039 |
| `j_forward_axis` | `1` | CVAR_ARCHIVE | client/cl_main.c:7045 |
| `j_pitch` | `0.022` | CVAR_ARCHIVE | client/cl_main.c:7037 |
| `j_pitch_axis` | `3` | CVAR_ARCHIVE | client/cl_main.c:7043 |
| `j_side` | `0.25` | CVAR_ARCHIVE | client/cl_main.c:7040 |
| `j_side_axis` | `0` | CVAR_ARCHIVE | client/cl_main.c:7046 |
| `j_up` | `0` | CVAR_ARCHIVE | client/cl_main.c:7041 |
| `j_up_axis` | `4` | CVAR_ARCHIVE | client/cl_main.c:7047 |
| `j_yaw` | `-0.022` | CVAR_ARCHIVE | client/cl_main.c:7038 |
| `j_yaw_axis` | `2` | CVAR_ARCHIVE | client/cl_main.c:7044 |
| `journal` | `0` | CVAR_INIT | qcommon/common.c:2227 |
| `joy_threshold` | `0.15` | CVAR_ARCHIVE | sdl/sdl_input.c:1336 |
| `logfile` | `0` | CVAR_TEMP | qcommon/common.c:3087 |
| `m_filter` | `1` | CVAR_ARCHIVE | client/cl_main.c:7032 |
| `m_filter` | `0` | CVAR_ARCHIVE | client/cl_main.c:7034 |
| `m_forward` | `0.25` | CVAR_ARCHIVE | client/cl_main.c:7028 |
| `m_pitch` | `0.022` | CVAR_ARCHIVE | client/cl_main.c:7026 |
| `m_side` | `0.25` | CVAR_ARCHIVE | client/cl_main.c:7029 |
| `m_yaw` | `0.022` | CVAR_ARCHIVE | client/cl_main.c:7027 |
| `mapname` | `""` | CVAR_SERVERINFO \| CVAR_ROM | game/ai_main.c:1383 |
| `mapname` | `nomap` | CVAR_SERVERINFO \| CVAR_ROM | server/sv_init.c:638 |
| `model` | `sarge` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7071 |
| `name` | `UnnamedPlayer` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7068 |
| `net_dropsim` | `""` | CVAR_TEMP | qcommon/net_ip.c:1488 |
| `net_enabled` | `1` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1430 |
| `net_enabled` | `3` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1434 |
| `net_ip` | `0.0.0.0` | CVAR_LATCH | qcommon/net_ip.c:1439 |
| `net_ip6` | `::` | CVAR_LATCH | qcommon/net_ip.c:1443 |
| `net_mcast6iface` | `0` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1461 |
| `net_mcast6iface` | `""` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1463 |
| `net_socksEnabled` | `0` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1468 |
| `net_socksPassword` | `""` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1484 |
| `net_socksPort` | `1080` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1476 |
| `net_socksServer` | `""` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1472 |
| `net_socksUsername` | `""` | CVAR_LATCH \| CVAR_ARCHIVE | qcommon/net_ip.c:1480 |
| `nextmap` | `""` | CVAR_TEMP | server/sv_init.c:670 |
| `password` | `""` | CVAR_USERINFO | client/cl_main.c:7084 |
| `pmove_fixed` | `0` | CVAR_SYSTEMINFO | cgame/cg_main.c:1814 |
| `pmove_msec` | `8` | CVAR_SYSTEMINFO | cgame/cg_main.c:1815 |
| `r_allowResize` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_glimp.c:1339 |
| `r_allowSoftwareGL` | `0` | CVAR_LATCH | sdl/sdl_glimp.c:1335 |
| `r_availableModes` | `""` | CVAR_ROM | sdl/sdl_glimp.c:1430 |
| `r_centerWindow` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_glimp.c:1340 |
| `r_debugSurface` | `0` | 0 | qcommon/cm_patch.c:1626 |
| `r_debugSurfaceUpdate` | `1` | 0 | qcommon/cm_patch.c:1288 |
| `r_debugSurfaceUpdate` | `1` | 0 | qcommon/cm_patch.c:1475 |
| `r_inGameVideo` | `0` | CVAR_ARCHIVE | client/cl_main.c:7013 |
| `r_inGameVideo` | `1` | CVAR_ARCHIVE | client/cl_main.c:7015 |
| `r_preferOpenGLES` | `-1` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_glimp.c:1341 |
| `r_sdlDriver` | `""` | CVAR_ROM | sdl/sdl_glimp.c:1338 |
| `rate` | `25000` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7069 |
| `rconAddress` | `""` | 0 | client/cl_main.c:6984 |
| `rconPassword` | `""` | CVAR_TEMP | client/cl_main.c:6962 |
| `rconPassword` | `""` | CVAR_TEMP | server/sv_init.c:665 |
| `s_sdlBits` | `16` | CVAR_ARCHIVE | sdl/sdl_snd.c:217 |
| `s_sdlCapture` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | sdl/sdl_snd.c:312 |
| `s_sdlChannels` | `2` | CVAR_ARCHIVE | sdl/sdl_snd.c:219 |
| `s_sdlDevSamps` | `0` | CVAR_ARCHIVE | sdl/sdl_snd.c:220 |
| `s_sdlMixSamps` | `0` | CVAR_ARCHIVE | sdl/sdl_snd.c:221 |
| `s_sdlSpeed` | `0` | CVAR_ARCHIVE | sdl/sdl_snd.c:218 |
| `sensitivity` | `5` | CVAR_ARCHIVE | client/cl_main.c:6994 |
| `server1` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:207 |
| `server1` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5794 |
| `server10` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:216 |
| `server10` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5803 |
| `server11` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:217 |
| `server11` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5804 |
| `server12` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:218 |
| `server12` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5805 |
| `server13` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:219 |
| `server13` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5806 |
| `server14` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:220 |
| `server14` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5807 |
| `server15` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:221 |
| `server15` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5808 |
| `server16` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:222 |
| `server16` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5809 |
| `server2` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:208 |
| `server2` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5795 |
| `server3` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:209 |
| `server3` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5796 |
| `server4` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:210 |
| `server4` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5797 |
| `server5` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:211 |
| `server5` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5798 |
| `server6` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:212 |
| `server6` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5799 |
| `server7` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:213 |
| `server7` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5800 |
| `server8` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:214 |
| `server8` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5801 |
| `server9` | `""` | CVAR_ARCHIVE | q3_ui/ui_main.c:215 |
| `server9` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5802 |
| `sex` | `male` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7081 |
| `showdrop` | `0` | CVAR_TEMP | qcommon/net_chan.c:75 |
| `showpackets` | `0` | CVAR_TEMP | qcommon/net_chan.c:74 |
| `snaps` | `20` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7070 |
| `sv_allowDownload` | `0` | CVAR_SERVERINFO | server/sv_init.c:672 |
| `sv_banFile` | `serverbans.dat` | CVAR_ARCHIVE | server/sv_init.c:689 |
| `sv_cheats` | `1` | CVAR_ROM \| CVAR_SYSTEMINFO | qcommon/cvar.c:1634 |
| `sv_cheats` | `1` | CVAR_SYSTEMINFO \| CVAR_ROM | server/sv_init.c:651 |
| `sv_dlRate` | `100` | CVAR_ARCHIVE \| CVAR_SERVERINFO | server/sv_init.c:645 |
| `sv_dlURL` | `""` | CVAR_SERVERINFO \| CVAR_ARCHIVE | server/sv_init.c:673 |
| `sv_floodProtect` | `1` | CVAR_ARCHIVE \| CVAR_SERVERINFO | server/sv_init.c:648 |
| `sv_fps` | `20` | CVAR_TEMP | server/sv_init.c:667 |
| `sv_hostname` | `noname` | CVAR_SERVERINFO \| CVAR_ARCHIVE | server/sv_init.c:640 |
| `sv_keywords` | `""` | CVAR_SERVERINFO | server/sv_init.c:637 |
| `sv_killserver` | `0` | 0 | server/sv_init.c:683 |
| `sv_lanForceRate` | `1` | CVAR_ARCHIVE | server/sv_init.c:685 |
| `sv_mapChecksum` | `""` | CVAR_ROM | server/sv_init.c:684 |
| `sv_master2` | `directory.ioquake3.org` | 0 | server/sv_init.c:676 |
| `sv_maxclients` | `8` | 0 | server/sv_init.c:244 |
| `sv_maxclients` | `8` | CVAR_SERVERINFO \| CVAR_LATCH | server/sv_init.c:641 |
| `sv_maxPing` | `0` | CVAR_ARCHIVE \| CVAR_SERVERINFO | server/sv_init.c:647 |
| `sv_maxRate` | `0` | CVAR_ARCHIVE \| CVAR_SERVERINFO | server/sv_init.c:644 |
| `sv_minPing` | `0` | CVAR_ARCHIVE \| CVAR_SERVERINFO | server/sv_init.c:646 |
| `sv_minRate` | `0` | CVAR_ARCHIVE \| CVAR_SERVERINFO | server/sv_init.c:643 |
| `sv_packetdelay` | `0` | CVAR_CHEAT | qcommon/common.c:3100 |
| `sv_padPackets` | `0` | 0 | server/sv_init.c:682 |
| `sv_pakNames` | `""` | CVAR_SYSTEMINFO \| CVAR_ROM | server/sv_init.c:660 |
| `sv_paks` | `""` | CVAR_SYSTEMINFO \| CVAR_ROM | server/sv_init.c:659 |
| `sv_paused` | `0` | CVAR_ROM | qcommon/common.c:3098 |
| `sv_privateClients` | `0` | CVAR_SERVERINFO | server/sv_init.c:639 |
| `sv_privatePassword` | `""` | CVAR_TEMP | server/sv_init.c:666 |
| `sv_pure` | `0` | CVAR_SYSTEMINFO | server/sv_init.c:653 |
| `sv_reconnectlimit` | `3` | 0 | server/sv_init.c:680 |
| `sv_referencedPakNames` | `""` | CVAR_SYSTEMINFO \| CVAR_ROM | server/sv_init.c:662 |
| `sv_referencedPaks` | `""` | CVAR_SYSTEMINFO \| CVAR_ROM | server/sv_init.c:661 |
| `sv_running` | `0` | CVAR_ROM | qcommon/common.c:3101 |
| `sv_serverid` | `0` | CVAR_SYSTEMINFO \| CVAR_ROM | server/sv_init.c:652 |
| `sv_showloss` | `0` | 0 | server/sv_init.c:681 |
| `sv_strictAuth` | `0` | CVAR_ARCHIVE | server/sv_init.c:687 |
| `sv_timeout` | `200` | CVAR_TEMP | server/sv_init.c:668 |
| `sv_voip` | `1` | CVAR_LATCH | server/sv_init.c:655 |
| `sv_zombietime` | `2` | CVAR_TEMP | server/sv_init.c:669 |
| `team_headmodel` | `*james` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7074 |
| `team_model` | `james` | CVAR_USERINFO \| CVAR_ARCHIVE | client/cl_main.c:7073 |
| `teamoverlay` | `1` | CVAR_ROM \| CVAR_USERINFO | cgame/cg_main.c:1695 |
| `teamtask` | `0` | CVAR_USERINFO | client/cl_main.c:7080 |
| `timedemo` | `0` | 0 | client/cl_main.c:6965 |
| `timedemo` | `0` | CVAR_CHEAT | qcommon/common.c:3094 |
| `timegraph` | `0` | CVAR_CHEAT | client/cl_scrn.c:525 |
| `timelimit` | `0` | CVAR_SERVERINFO | server/sv_init.c:635 |
| `timescale` | `1` | 0 | cgame/cg_main.c:1793 |
| `timescale` | `1` | CVAR_CHEAT \| CVAR_SYSTEMINFO | qcommon/common.c:3089 |
| `ui_actualNetGametype` | `3` | CVAR_ARCHIVE | ui/ui_main.c:5822 |
| `ui_bigFont` | `0.4` | CVAR_ARCHIVE | cgame/cg_main.c:1831 |
| `ui_bigFont` | `0.4` | CVAR_ARCHIVE | ui/ui_main.c:5868 |
| `ui_blueteam1` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5828 |
| `ui_blueteam2` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5829 |
| `ui_blueteam3` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5830 |
| `ui_blueteam4` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5831 |
| `ui_blueteam5` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5832 |
| `ui_browserGameType` | `0` | CVAR_ARCHIVE | q3_ui/ui_main.c:197 |
| `ui_browserGameType` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5785 |
| `ui_browserMaster` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:196 |
| `ui_browserMaster` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5784 |
| `ui_browserShowEmpty` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:200 |
| `ui_browserShowEmpty` | `1` | CVAR_ARCHIVE | ui/ui_main.c:5787 |
| `ui_browserShowFull` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:199 |
| `ui_browserShowFull` | `1` | CVAR_ARCHIVE | ui/ui_main.c:5786 |
| `ui_browserSortKey` | `4` | CVAR_ARCHIVE | q3_ui/ui_main.c:198 |
| `ui_captureLimit` | `5` | 0 | ui/ui_main.c:5866 |
| `ui_cdkeychecked` | `0` | CVAR_ROM | q3_ui/ui_main.c:224 |
| `ui_cdkeychecked` | `0` | CVAR_ROM | ui/ui_main.c:5810 |
| `ui_ctf_capturelimit` | `8` | CVAR_ARCHIVE | q3_ui/ui_main.c:179 |
| `ui_ctf_capturelimit` | `8` | CVAR_ARCHIVE | ui/ui_main.c:5767 |
| `ui_ctf_friendly` | `0` | CVAR_ARCHIVE | q3_ui/ui_main.c:181 |
| `ui_ctf_friendly` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5769 |
| `ui_ctf_timelimit` | `30` | CVAR_ARCHIVE | q3_ui/ui_main.c:180 |
| `ui_ctf_timelimit` | `30` | CVAR_ARCHIVE | ui/ui_main.c:5768 |
| `ui_currentMap` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5836 |
| `ui_currentNetMap` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5837 |
| `ui_currentOpponent` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5839 |
| `ui_currentTier` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5835 |
| `ui_debug` | `0` | CVAR_TEMP | ui/ui_main.c:5812 |
| `ui_dedicated` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5818 |
| `ui_ffa_fraglimit` | `20` | CVAR_ARCHIVE | q3_ui/ui_main.c:169 |
| `ui_ffa_fraglimit` | `20` | CVAR_ARCHIVE | ui/ui_main.c:5757 |
| `ui_ffa_timelimit` | `0` | CVAR_ARCHIVE | q3_ui/ui_main.c:170 |
| `ui_ffa_timelimit` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5758 |
| `ui_findPlayer` | `Sarge` | CVAR_ARCHIVE | ui/ui_main.c:5869 |
| `ui_fragLimit` | `10` | 0 | ui/ui_main.c:5865 |
| `ui_gametype` | `3` | CVAR_ARCHIVE | ui/ui_main.c:5819 |
| `ui_initialized` | `0` | CVAR_TEMP | ui/ui_main.c:5813 |
| `ui_ioq3` | `1` | CVAR_ROM | q3_ui/ui_main.c:225 |
| `ui_joinGametype` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5820 |
| `ui_lastServerRefresh_0` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5842 |
| `ui_lastServerRefresh_1` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5843 |
| `ui_lastServerRefresh_2` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5844 |
| `ui_lastServerRefresh_3` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5845 |
| `ui_lastServerRefresh_4` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5846 |
| `ui_lastServerRefresh_5` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5847 |
| `ui_lastServerRefresh_6` | `""` | CVAR_ARCHIVE | ui/ui_main.c:5848 |
| `ui_mapIndex` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5838 |
| `ui_menuFiles` | `ui/menus.txt` | CVAR_ARCHIVE | ui/ui_main.c:5834 |
| `ui_netGametype` | `3` | CVAR_ARCHIVE | ui/ui_main.c:5821 |
| `ui_netSource` | `1` | CVAR_ARCHIVE | ui/ui_main.c:5833 |
| `ui_new` | `0` | CVAR_TEMP | ui/ui_main.c:5811 |
| `ui_q3model` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5870 |
| `ui_recordSPDemo` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1784 |
| `ui_recordSPDemo` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5872 |
| `ui_recordSPDemoName` | `""` | CVAR_ARCHIVE | cgame/cg_main.c:1785 |
| `ui_redteam1` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5823 |
| `ui_redteam2` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5824 |
| `ui_redteam3` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5825 |
| `ui_redteam4` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5826 |
| `ui_redteam5` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5827 |
| `ui_scoreAccuracy` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5850 |
| `ui_scoreAssists` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5855 |
| `ui_scoreBase` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5860 |
| `ui_scoreCaptures` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5853 |
| `ui_scoreDefends` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5854 |
| `ui_scoreExcellents` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5852 |
| `ui_scoreGauntlets` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5856 |
| `ui_scoreImpressives` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5851 |
| `ui_scorePerfect` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5858 |
| `ui_scoreScore` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5857 |
| `ui_scoreShutoutBonus` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5864 |
| `ui_scoreSkillBonus` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5863 |
| `ui_scoreTeam` | `0 to 0` | CVAR_ARCHIVE | ui/ui_main.c:5859 |
| `ui_scoreTime` | `00:00` | CVAR_ARCHIVE | ui/ui_main.c:5861 |
| `ui_scoreTimeBonus` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5862 |
| `ui_serverStatusTimeOut` | `7000` | CVAR_ARCHIVE | ui/ui_main.c:5876 |
| `ui_singlePlayerActive` | `0` | CVAR_USERINFO | cgame/cg_main.c:1780 |
| `ui_singlePlayerActive` | `0` | CVAR_USERINFO | cgame/cg_main.c:1783 |
| `ui_singlePlayerActive` | `0` | 0 | ui/ui_main.c:5849 |
| `ui_smallFont` | `0.25` | CVAR_ARCHIVE | cgame/cg_main.c:1830 |
| `ui_smallFont` | `0.25` | CVAR_ARCHIVE | ui/ui_main.c:5867 |
| `ui_spSelection` | `""` | CVAR_ROM | q3_ui/ui_main.c:194 |
| `ui_spSelection` | `""` | CVAR_ROM | ui/ui_main.c:5782 |
| `ui_team_fraglimit` | `0` | CVAR_ARCHIVE | q3_ui/ui_main.c:175 |
| `ui_team_fraglimit` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5763 |
| `ui_team_friendly` | `1` | CVAR_ARCHIVE | q3_ui/ui_main.c:177 |
| `ui_team_friendly` | `1` | CVAR_ARCHIVE | ui/ui_main.c:5765 |
| `ui_team_timelimit` | `20` | CVAR_ARCHIVE | q3_ui/ui_main.c:176 |
| `ui_team_timelimit` | `20` | CVAR_ARCHIVE | ui/ui_main.c:5764 |
| `ui_teamArenaFirstRun` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5873 |
| `ui_tourney_fraglimit` | `0` | CVAR_ARCHIVE | q3_ui/ui_main.c:172 |
| `ui_tourney_fraglimit` | `0` | CVAR_ARCHIVE | ui/ui_main.c:5760 |
| `ui_tourney_timelimit` | `15` | CVAR_ARCHIVE | q3_ui/ui_main.c:173 |
| `ui_tourney_timelimit` | `15` | CVAR_ARCHIVE | ui/ui_main.c:5761 |
| `vm_cgame` | `0` | CVAR_ARCHIVE | qcommon/vm.c:73 |
| `vm_game` | `0` | CVAR_ARCHIVE | qcommon/vm.c:74 |
| `vm_ui` | `0` | CVAR_ARCHIVE | qcommon/vm.c:75 |

*Count:* **530**

---

## D. Cvars — renderer / capture (tr_init.c, cl_avi.c, snd_*)

Renderer GL and AVI-capture cvars live in `renderergl1/tr_init.c`, `renderergl2/tr_init.c`, `client/cl_avi.c`, and `client/snd_*.c`.

| Name | Default | Flags | Source |
|------|---------|-------|--------|
| `cg_shadows` | `1` | 0 | renderergl1/tr_init.c:1949 |
| `cg_shadows` | `1` | 0 | renderergl2/tr_init.c:2138 |
| `com_altivec` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1789 |
| `com_altivec` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:1910 |
| `r_allowExtensions` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1795 |
| `r_allowExtensions` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1916 |
| `r_ambientScale` | `10` | CVAR_ARCHIVE | renderergl1/tr_init.c:1889 |
| `r_ambientScale` | `0.6` | CVAR_ARCHIVE | renderergl2/tr_init.c:2081 |
| `r_anaglyph2d` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1894 |
| `r_anaglyph2d` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2085 |
| `r_anaglyphMode` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1892 |
| `r_anaglyphMode` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2084 |
| `r_arb_seamless_cube_map` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1925 |
| `r_arb_vertex_array_object` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1926 |
| `r_autoExposure` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:1978 |
| `r_baseGloss` | `0.3` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2002 |
| `r_baseNormalX` | `1.0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1998 |
| `r_baseNormalY` | `1.0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1999 |
| `r_baseParallax` | `0.05` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2000 |
| `r_baseSpecular` | `0.04` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2001 |
| `r_BloomBlurFalloff` | `0.75` | CVAR_ARCHIVE | renderergl1/tr_init.c:1963 |
| `r_BloomBlurFalloff` | `0.75` | CVAR_ARCHIVE | renderergl2/tr_init.c:2156 |
| `r_BloomBlurRadius` | `5` | CVAR_ARCHIVE | renderergl1/tr_init.c:1964 |
| `r_BloomBlurRadius` | `5` | CVAR_ARCHIVE | renderergl2/tr_init.c:2157 |
| `r_BloomBlurScale` | `1.0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1962 |
| `r_BloomBlurScale` | `1.0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2155 |
| `r_BloomBrightThreshold` | `0.125` | CVAR_ARCHIVE | renderergl1/tr_init.c:1970 |
| `r_BloomBrightThreshold` | `0.125` | CVAR_ARCHIVE | renderergl2/tr_init.c:2163 |
| `r_BloomDebug` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1972 |
| `r_BloomDebug` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2165 |
| `r_BloomIntensity` | `0.750` | CVAR_ARCHIVE | renderergl1/tr_init.c:1968 |
| `r_BloomIntensity` | `0.750` | CVAR_ARCHIVE | renderergl2/tr_init.c:2161 |
| `r_BloomPasses` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1965 |
| `r_BloomPasses` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2158 |
| `r_BloomSaturation` | `0.800` | CVAR_ARCHIVE | renderergl1/tr_init.c:1969 |
| `r_BloomSaturation` | `0.800` | CVAR_ARCHIVE | renderergl2/tr_init.c:2162 |
| `r_BloomSceneIntensity` | `1.000` | CVAR_ARCHIVE | renderergl1/tr_init.c:1966 |
| `r_BloomSceneIntensity` | `1.000` | CVAR_ARCHIVE | renderergl2/tr_init.c:2159 |
| `r_BloomSceneSaturation` | `1.000` | CVAR_ARCHIVE | renderergl1/tr_init.c:1967 |
| `r_BloomSceneSaturation` | `1.000` | CVAR_ARCHIVE | renderergl2/tr_init.c:2160 |
| `r_BloomTextureScale` | `0.5` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl1/tr_init.c:1971 |
| `r_BloomTextureScale` | `0.5` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl2/tr_init.c:2164 |
| `r_cameraExposure` | `1` | CVAR_CHEAT | renderergl2/tr_init.c:1983 |
| `r_clear` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1941 |
| `r_clear` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2131 |
| `r_clearColor` | `""` | CVAR_ARCHIVE | renderergl1/tr_init.c:1942 |
| `r_clearColor` | `""` | CVAR_ARCHIVE | renderergl2/tr_init.c:2132 |
| `r_cloudHeight` | `""` | CVAR_ARCHIVE | renderergl1/tr_init.c:1870 |
| `r_cloudHeight` | `""` | CVAR_ARCHIVE | renderergl2/tr_init.c:2057 |
| `r_colorbits` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1813 |
| `r_colorbits` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1941 |
| `r_colorMipLevels` | `0` | CVAR_LATCH | renderergl1/tr_init.c:1809 |
| `r_colorMipLevels` | `0` | CVAR_LATCH | renderergl2/tr_init.c:1937 |
| `r_contrast` | `1.0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1960 |
| `r_contrast` | `1.0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2152 |
| `r_cubeMapping` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1994 |
| `r_cubemapSize` | `128` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1995 |
| `r_customheight` | `1024` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1825 |
| `r_customheight` | `1024` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1953 |
| `r_customPixelAspect` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1826 |
| `r_customPixelAspect` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1954 |
| `r_customwidth` | `1600` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1824 |
| `r_customwidth` | `1600` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1952 |
| `r_darknessThreshold` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1916 |
| `r_darknessThreshold` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2106 |
| `r_debugFonts` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1905 |
| `r_debugFonts` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2096 |
| `r_debuglight` | `0` | CVAR_TEMP | renderergl1/tr_init.c:1901 |
| `r_debuglight` | `0` | CVAR_TEMP | renderergl2/tr_init.c:2092 |
| `r_debugMarkSurface` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1977 |
| `r_debugMarkSurface` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2170 |
| `r_debugScaledImages` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1981 |
| `r_debugScaledImages` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2174 |
| `r_debugSort` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1902 |
| `r_debugSort` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2093 |
| `r_debugSurface` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1936 |
| `r_debugSurface` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2126 |
| `r_defaultMSFontFallbacks` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1907 |
| `r_defaultMSFontFallbacks` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2098 |
| `r_defaultQlFontFallbacks` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1906 |
| `r_defaultQlFontFallbacks` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2097 |
| `r_defaultSystemFontFallbacks` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1908 |
| `r_defaultSystemFontFallbacks` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2099 |
| `r_defaultUnifontFallbacks` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1909 |
| `r_defaultUnifontFallbacks` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2100 |
| `r_deluxeMapping` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1990 |
| `r_deluxeSpecular` | `0.3` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1996 |
| `r_depthbits` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1815 |
| `r_depthbits` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1943 |
| `r_depthPrepass` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:1985 |
| `r_detailtextures` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1811 |
| `r_detailtextures` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1939 |
| `r_directedScale` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1890 |
| `r_directedScale` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2082 |
| `r_displayRefresh` | `0` | CVAR_LATCH | renderergl1/tr_init.c:1843 |
| `r_displayRefresh` | `0` | CVAR_LATCH | renderergl2/tr_init.c:2033 |
| `r_dlightBacks` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1875 |
| `r_dlightBacks` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2062 |
| `r_dlightMode` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2004 |
| `r_drawBuffer` | `GL_BACK` | CVAR_CHEAT | renderergl1/tr_init.c:1946 |
| `r_drawBuffer` | `GL_BACK` | CVAR_CHEAT | renderergl2/tr_init.c:2135 |
| `r_drawentities` | `1` | CVAR_CHEAT | renderergl1/tr_init.c:1928 |
| `r_drawentities` | `1` | CVAR_CHEAT | renderergl2/tr_init.c:2118 |
| `r_drawSkyFloor` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1869 |
| `r_drawSkyFloor` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2056 |
| `r_drawSun` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1873 |
| `r_drawSun` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2060 |
| `r_drawSunRays` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2015 |
| `r_drawworld` | `1` | CVAR_CHEAT | renderergl1/tr_init.c:1912 |
| `r_drawworld` | `1` | CVAR_CHEAT | renderergl2/tr_init.c:2103 |
| `r_dynamiclight` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1874 |
| `r_dynamiclight` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2061 |
| `r_enableBloom` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1961 |
| `r_enableBloom` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2154 |
| `r_enableColorCorrect` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1959 |
| `r_enableColorCorrect` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2150 |
| `r_enablePostProcess` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1958 |
| `r_enablePostProcess` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2149 |
| `r_ext_compiled_vertex_array` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1798 |
| `r_ext_compiled_vertex_array` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1919 |
| `r_ext_compressed_textures` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1796 |
| `r_ext_compressed_textures` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1917 |
| `r_ext_direct_state_access` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1927 |
| `r_ext_framebuffer_multisample` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1924 |
| `r_ext_framebuffer_object` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1922 |
| `r_ext_max_anisotropy` | `2` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1803 |
| `r_ext_max_anisotropy` | `2` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1931 |
| `r_ext_multisample` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1816 |
| `r_ext_multisample` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1944 |
| `r_ext_multitexture` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1797 |
| `r_ext_multitexture` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1918 |
| `r_ext_texture_env_add` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1799 |
| `r_ext_texture_env_add` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1920 |
| `r_ext_texture_float` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1923 |
| `r_externalGLSL` | `0` | CVAR_LATCH | renderergl2/tr_init.c:1966 |
| `r_facePlaneCull` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1881 |
| `r_facePlaneCull` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2075 |
| `r_fastsky` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1867 |
| `r_fastsky` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2054 |
| `r_fastSkyColor` | `""` | CVAR_ARCHIVE | renderergl1/tr_init.c:1868 |
| `r_fastSkyColor` | `""` | CVAR_ARCHIVE | renderergl2/tr_init.c:2055 |
| `r_fboAntiAlias` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1975 |
| `r_finish` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1876 |
| `r_finish` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2063 |
| `r_flareFade` | `7` | CVAR_CHEAT | renderergl1/tr_init.c:1920 |
| `r_flareFade` | `7` | CVAR_CHEAT | renderergl2/tr_init.c:2110 |
| `r_flares` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1861 |
| `r_flares` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2048 |
| `r_flareSize` | `40` | CVAR_CHEAT | renderergl1/tr_init.c:1919 |
| `r_flareSize` | `40` | CVAR_CHEAT | renderergl2/tr_init.c:2109 |
| `r_floatLightmap` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1969 |
| `r_fog` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1979 |
| `r_fog` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2172 |
| `r_forceAutoExposure` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:1979 |
| `r_forceAutoExposureMax` | `2.0` | CVAR_CHEAT | renderergl2/tr_init.c:1981 |
| `r_forceAutoExposureMin` | `-2.0` | CVAR_CHEAT | renderergl2/tr_init.c:1980 |
| `r_forceMap` | `""` | CVAR_ARCHIVE | renderergl1/tr_init.c:1957 |
| `r_forceMap` | `""` | CVAR_ARCHIVE | renderergl2/tr_init.c:2148 |
| `r_forceSky` | `""` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl1/tr_init.c:1871 |
| `r_forceSky` | `""` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl2/tr_init.c:2058 |
| `r_forceSun` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2012 |
| `r_forceSunAmbientScale` | `0.5` | CVAR_CHEAT | renderergl2/tr_init.c:2014 |
| `r_forceSunLightScale` | `1.0` | CVAR_CHEAT | renderergl2/tr_init.c:2013 |
| `r_forceToneMap` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:1973 |
| `r_forceToneMapAvg` | `-2.0` | CVAR_CHEAT | renderergl2/tr_init.c:1975 |
| `r_forceToneMapMax` | `0.0` | CVAR_CHEAT | renderergl2/tr_init.c:1976 |
| `r_forceToneMapMin` | `-8.0` | CVAR_CHEAT | renderergl2/tr_init.c:1974 |
| `r_fullbright` | `0` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl1/tr_init.c:1846 |
| `r_fullbright` | `0` | CVAR_LATCH\|CVAR_CHEAT | renderergl2/tr_init.c:2035 |
| `r_fullscreen` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1822 |
| `r_fullscreen` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:1950 |
| `r_gamma` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1880 |
| `r_gamma` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2074 |
| `r_genNormalMaps` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2010 |
| `r_glossType` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2003 |
| `r_greyscale` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1833 |
| `r_greyscale` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1960 |
| `r_greyscaleValue` | `1.0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1835 |
| `r_greyscaleValue` | `1.0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1961 |
| `r_hdr` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1968 |
| `r_ignore` | `1` | CVAR_CHEAT | renderergl1/tr_init.c:1929 |
| `r_ignore` | `1` | CVAR_CHEAT | renderergl2/tr_init.c:2119 |
| `r_ignoreDstAlpha` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2025 |
| `r_ignoreEntityMergable` | `2` | CVAR_ARCHIVE | renderergl1/tr_init.c:1980 |
| `r_ignoreEntityMergable` | `2` | CVAR_ARCHIVE | renderergl2/tr_init.c:2173 |
| `r_ignoreFastPath` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1832 |
| `r_ignoreGLErrors` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1866 |
| `r_ignoreGLErrors` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2053 |
| `r_ignorehwgamma` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1820 |
| `r_ignorehwgamma` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1948 |
| `r_ignoreNoMarks` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1978 |
| `r_ignoreNoMarks` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2171 |
| `r_ignoreShaderNoMipMaps` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1806 |
| `r_ignoreShaderNoMipMaps` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1934 |
| `r_ignoreShaderNoPicMip` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1807 |
| `r_ignoreShaderNoPicMip` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1935 |
| `r_imageUpsample` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2007 |
| `r_imageUpsampleMaxSize` | `1024` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2008 |
| `r_imageUpsampleType` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2009 |
| `r_inGameVideo` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1872 |
| `r_inGameVideo` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2059 |
| `r_intensity` | `1` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl1/tr_init.c:1852 |
| `r_intensity` | `1` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl2/tr_init.c:2039 |
| `r_jpegCompressionQuality` | `90` | CVAR_ARCHIVE | renderergl1/tr_init.c:1955 |
| `r_jpegCompressionQuality` | `90` | CVAR_ARCHIVE | renderergl2/tr_init.c:2146 |
| `r_lightmap` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1914 |
| `r_lightmap` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2104 |
| `r_lightmapColor` | `""` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1915 |
| `r_lightmapColor` | `""` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2105 |
| `r_lockpvs` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1947 |
| `r_lockpvs` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2136 |
| `r_lodbias` | `-2` | CVAR_ARCHIVE | renderergl1/tr_init.c:1860 |
| `r_lodbias` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2047 |
| `r_lodCurveError` | `250` | CVAR_ARCHIVE | renderergl1/tr_init.c:1859 |
| `r_lodCurveError` | `250` | CVAR_ARCHIVE | renderergl2/tr_init.c:2046 |
| `r_lodscale` | `5` | CVAR_CHEAT | renderergl1/tr_init.c:1926 |
| `r_lodscale` | `5` | CVAR_CHEAT | renderergl2/tr_init.c:2116 |
| `r_logFile` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1935 |
| `r_logFile` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2125 |
| `r_mapGreyScale` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1836 |
| `r_mapGreyScale` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1963 |
| `r_mapOverBrightBits` | `2` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl1/tr_init.c:1847 |
| `r_mapOverBrightBits` | `2` | CVAR_LATCH | renderergl2/tr_init.c:2036 |
| `r_mapOverBrightBitsCap` | `255` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl1/tr_init.c:1849 |
| `r_mapOverBrightBitsCap` | `255` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl2/tr_init.c:2038 |
| `r_mapOverBrightBitsValue` | `1.0` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl1/tr_init.c:1848 |
| `r_mapOverBrightBitsValue` | `1.0` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl2/tr_init.c:2037 |
| `r_marksOnTriangleMeshes` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1951 |
| `r_marksOnTriangleMeshes` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2140 |
| `r_measureOverdraw` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1925 |
| `r_measureOverdraw` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2115 |
| `r_mergeLightmaps` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2006 |
| `r_mode` | `11` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1821 |
| `r_mode` | `11` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1949 |
| `r_nobind` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1937 |
| `r_nobind` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2127 |
| `r_noborder` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1823 |
| `r_noborder` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1951 |
| `r_nocull` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1930 |
| `r_nocull` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2120 |
| `r_nocurves` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1911 |
| `r_nocurves` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2102 |
| `r_noportals` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1948 |
| `r_noportals` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2137 |
| `r_norefresh` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1927 |
| `r_norefresh` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2117 |
| `r_normalMapping` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1988 |
| `r_novis` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1931 |
| `r_novis` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2121 |
| `r_offsetfactor` | `-1` | CVAR_CHEAT | renderergl1/tr_init.c:1943 |
| `r_offsetfactor` | `-1` | CVAR_CHEAT | renderergl2/tr_init.c:2133 |
| `r_offsetunits` | `-2` | CVAR_CHEAT | renderergl1/tr_init.c:1944 |
| `r_offsetunits` | `-2` | CVAR_CHEAT | renderergl2/tr_init.c:2134 |
| `r_opengl2_overbright` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2167 |
| `r_overBrightBits` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1818 |
| `r_overBrightBits` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1946 |
| `r_overBrightBitsValue` | `1.0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1819 |
| `r_overBrightBitsValue` | `1.0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1947 |
| `r_parallaxMapOffset` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1992 |
| `r_parallaxMapping` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1991 |
| `r_parallaxMapShadows` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1993 |
| `r_pbr` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1997 |
| `r_picmip` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1805 |
| `r_picmip` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1933 |
| `r_picmipGreyScale` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1837 |
| `r_picmipGreyScale` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1964 |
| `r_picmipGreyScaleValue` | `0.5` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1838 |
| `r_picmipGreyScaleValue` | `0.5` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1965 |
| `r_pngZlibCompression` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1956 |
| `r_pngZlibCompression` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2147 |
| `r_polygonFill` | `1` | CVAR_CHEAT | renderergl1/tr_init.c:1945 |
| `r_portalBobbing` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1973 |
| `r_portalBobbing` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2027 |
| `r_portalOnly` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1917 |
| `r_portalOnly` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2107 |
| `r_postProcess` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:1970 |
| `r_primitives` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1887 |
| `r_printShaders` | `0` | 0 | renderergl1/tr_init.c:1903 |
| `r_printShaders` | `0` | 0 | renderergl2/tr_init.c:2094 |
| `r_pshadowDist` | `128` | CVAR_ARCHIVE | renderergl2/tr_init.c:2005 |
| `r_railCoreWidth` | `6` | CVAR_ARCHIVE | renderergl1/tr_init.c:1884 |
| `r_railCoreWidth` | `6` | CVAR_ARCHIVE | renderergl2/tr_init.c:2078 |
| `r_railSegmentLength` | `32` | CVAR_ARCHIVE | renderergl1/tr_init.c:1885 |
| `r_railSegmentLength` | `32` | CVAR_ARCHIVE | renderergl2/tr_init.c:2079 |
| `r_railWidth` | `16` | CVAR_ARCHIVE | renderergl1/tr_init.c:1883 |
| `r_railWidth` | `16` | CVAR_ARCHIVE | renderergl2/tr_init.c:2077 |
| `r_roundImagesDown` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1808 |
| `r_roundImagesDown` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1936 |
| `r_saveFontData` | `0` | 0 | renderergl1/tr_init.c:1904 |
| `r_saveFontData` | `0` | 0 | renderergl2/tr_init.c:2095 |
| `r_scaleImagesPowerOfTwo` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1982 |
| `r_scaleImagesPowerOfTwo` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2175 |
| `r_screenMapTextureSize` | `128` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1983 |
| `r_screenMapTextureSize` | `128` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2176 |
| `r_shadowBlur` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2020 |
| `r_shadowCascadeZBias` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2024 |
| `r_shadowCascadeZFar` | `1024` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2023 |
| `r_shadowCascadeZNear` | `8` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2022 |
| `r_shadowFilter` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2019 |
| `r_shadowMapSize` | `1024` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2021 |
| `r_showcluster` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1932 |
| `r_showcluster` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2122 |
| `r_showImages` | `0` | CVAR_TEMP | renderergl1/tr_init.c:1899 |
| `r_showImages` | `0` | CVAR_TEMP | renderergl2/tr_init.c:2090 |
| `r_shownormals` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1940 |
| `r_shownormals` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2130 |
| `r_showsky` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1939 |
| `r_showsky` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2129 |
| `r_showtris` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1938 |
| `r_showtris` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2128 |
| `r_simpleMipMaps` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1827 |
| `r_simpleMipMaps` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1955 |
| `r_singleShader` | `0` | CVAR_ARCHIVE | renderergl1/tr_init.c:1853 |
| `r_singleShader` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2040 |
| `r_singleShaderName` | `""` | CVAR_ARCHIVE | renderergl1/tr_init.c:1854 |
| `r_singleShaderName` | `""` | CVAR_ARCHIVE | renderergl2/tr_init.c:2041 |
| `r_skipBackEnd` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1923 |
| `r_skipBackEnd` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2113 |
| `r_specularMapping` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1989 |
| `r_speeds` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1933 |
| `r_speeds` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2123 |
| `r_ssao` | `0` | CVAR_LATCH \| CVAR_ARCHIVE | renderergl2/tr_init.c:1986 |
| `r_stencilbits` | `8` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1814 |
| `r_stencilbits` | `8` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1942 |
| `r_stereoEnabled` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1831 |
| `r_stereoEnabled` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1959 |
| `r_stereoSeparation` | `64` | CVAR_ARCHIVE | renderergl1/tr_init.c:1865 |
| `r_stereoSeparation` | `64` | CVAR_ARCHIVE | renderergl2/tr_init.c:2052 |
| `r_subdivisions` | `4` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1830 |
| `r_subdivisions` | `4` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1958 |
| `r_sunlightMode` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2016 |
| `r_sunShadows` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2018 |
| `r_teleporterFlash` | `1` | CVAR_ARCHIVE | renderergl1/tr_init.c:1976 |
| `r_teleporterFlash` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:2169 |
| `r_texturebits` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1812 |
| `r_texturebits` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1940 |
| `r_textureMode` | `GL_LINEAR_MIPMAP_LINEAR` | CVAR_ARCHIVE | renderergl1/tr_init.c:1877 |
| `r_textureMode` | `GL_LINEAR_MIPMAP_LINEAR` | CVAR_ARCHIVE | renderergl2/tr_init.c:2064 |
| `r_toneMap` | `1` | CVAR_ARCHIVE | renderergl2/tr_init.c:1972 |
| `r_uiFullScreen` | `0` | 0 | renderergl1/tr_init.c:1829 |
| `r_uifullscreen` | `0` | 0 | renderergl2/tr_init.c:1957 |
| `r_useFbo` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1974 |
| `r_useFbo` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2028 |
| `r_vaoCache` | `0` | CVAR_ARCHIVE | renderergl2/tr_init.c:2142 |
| `r_verbose` | `0` | CVAR_CHEAT | renderergl1/tr_init.c:1934 |
| `r_verbose` | `0` | CVAR_CHEAT | renderergl2/tr_init.c:2124 |
| `r_vertexLight` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1828 |
| `r_vertexLight` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:1956 |
| `r_weather` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl1/tr_init.c:1984 |
| `r_weather` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | renderergl2/tr_init.c:2177 |
| `r_znear` | `4` | CVAR_CHEAT | renderergl1/tr_init.c:1862 |
| `r_znear` | `4` | CVAR_CHEAT | renderergl2/tr_init.c:2049 |
| `r_zproj` | `64` | CVAR_ARCHIVE | renderergl1/tr_init.c:1864 |
| `r_zproj` | `64` | CVAR_ARCHIVE | renderergl2/tr_init.c:2051 |
| `s_alCapture` | `1` | CVAR_ARCHIVE \| CVAR_LATCH | client/snd_openal.c:2670 |
| `s_alDevice` | `""` | CVAR_ARCHIVE \| CVAR_LATCH | client/snd_openal.c:2556 |
| `s_alDopplerFactor` | `1.0` | CVAR_ARCHIVE | client/snd_openal.c:2546 |
| `s_alDopplerSpeed` | `9000` | CVAR_ARCHIVE | client/snd_openal.c:2547 |
| `s_alGain` | `1.0` | CVAR_ARCHIVE | client/snd_openal.c:2544 |
| `s_alGraceDistance` | `512` | CVAR_CHEAT | client/snd_openal.c:2551 |
| `s_alInputDevice` | `""` | CVAR_ARCHIVE \| CVAR_LATCH | client/snd_openal.c:2555 |
| `s_alMaxDistance` | `1024` | CVAR_CHEAT | client/snd_openal.c:2549 |
| `s_alMinDistance` | `120` | CVAR_CHEAT | client/snd_openal.c:2548 |
| `s_alPrecache` | `1` | CVAR_ARCHIVE | client/snd_openal.c:2543 |
| `s_alRolloff` | `2` | CVAR_CHEAT | client/snd_openal.c:2550 |
| `s_alSources` | `96` | CVAR_ARCHIVE | client/snd_openal.c:2545 |
| `s_announcerVolume` | `1.0` | CVAR_ARCHIVE | client/snd_main.c:570 |
| `s_backend` | `base` | CVAR_ROM | client/snd_main.c:567 |
| `s_debugMissingSounds` | `0` | CVAR_ARCHIVE | client/snd_main.c:578 |
| `s_doppler` | `1` | CVAR_ARCHIVE | client/snd_main.c:566 |
| `s_forceScale` | `0.0` | CVAR_ARCHIVE | client/snd_main.c:573 |
| `s_initsound` | `1` | 0 | client/snd_main.c:580 |
| `s_killBeepVolume` | `1.0` | CVAR_ARCHIVE | client/snd_main.c:571 |
| `s_maxSoundInstances` | `96` | CVAR_ARCHIVE | client/snd_main.c:576 |
| `s_maxSoundRepeatTime` | `0` | CVAR_ARCHIVE | client/snd_main.c:575 |
| `s_mixahead` | `0.2` | CVAR_ARCHIVE | client/snd_dma.c:1782 |
| `s_mixPreStep` | `0.05` | CVAR_ARCHIVE | client/snd_dma.c:1783 |
| `s_musicvolume` | `0` | CVAR_ARCHIVE | client/snd_main.c:564 |
| `s_muted` | `0` | CVAR_ROM | client/snd_main.c:565 |
| `s_muteWhenMinimized` | `0` | CVAR_ARCHIVE | client/snd_main.c:568 |
| `s_muteWhenUnfocused` | `0` | CVAR_ARCHIVE | client/snd_main.c:569 |
| `s_qlAttenuate` | `1` | CVAR_ARCHIVE | client/snd_main.c:577 |
| `s_show` | `0` | CVAR_CHEAT | client/snd_dma.c:1784 |
| `s_showMiss` | `0` | CVAR_ARCHIVE | client/snd_main.c:574 |
| `s_testsound` | `0` | CVAR_CHEAT | client/snd_dma.c:1785 |
| `s_useOpenAL` | `0` | CVAR_ARCHIVE \| CVAR_LATCH | client/snd_main.c:594 |
| `s_useTimescale` | `0` | CVAR_ARCHIVE | client/snd_main.c:572 |
| `s_volume` | `0.8` | CVAR_ARCHIVE | client/snd_main.c:563 |

*Count:* **388**

---

## E. Summary

- Total console commands (all sites): **449**
- Total cvar registrations (all sites): **1983**
  - wolfcam-specific (heuristic): **1065**
  - inherited from ioq3: **530**
  - renderer / capture / sound: **388**

### Top 20 most fragmovie-relevant wolfcam cvars (judgment pick)

| Name | Default | Flags | Source | Why it matters |
|------|---------|-------|--------|----------------|
| `cg_freecam_noclip` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1966 | freecam passes through geometry |
| `cg_freecam_speed` | `400` | CVAR_ARCHIVE | cgame/cg_main.c:1970 | flight speed for freecam |
| `cl_freezeDemo` | `0` | CVAR_TEMP | client/cl_main.c:6961 | pauses demo playback — used between cuts |
| `cl_aviFrameRate` | `50` | CVAR_ARCHIVE | client/cl_main.c:6968 | AVI capture fps when `video` command is active |
| `timescale` | `1` | 0 | cgame/cg_main.c:1793 | global time multiplier — slow-mo / fast-forward |
| `cl_forceavidemo` | `0` | 0 | client/cl_main.c:6982 | force frame-locked AVI capture |
| `cg_thirdPerson` | `0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1677 | third-person view toggle |
| `cg_thirdPersonRange` | `80` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1660 | distance behind player in 3rd-person |
| `cg_thirdPersonAngle` | `0` | CVAR_CHEAT \| CVAR_ARCHIVE | cgame/cg_main.c:1661 | yaw offset behind player in 3rd-person |
| `cg_cameraOrbit` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1789 | orbit-cam speed |
| `cg_cameraOrbitDelay` | `50` | CVAR_ARCHIVE | cgame/cg_main.c:1790 | delay between orbit updates |
| `cg_draw2D` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1418 | 2D HUD master switch — turn OFF before capture |
| `cg_drawGun` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1372 | weapon model visibility |
| `cg_drawFPS` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:1448 | fps counter — disable for capture |
| `cg_autoChaseMissile` | `0` | CVAR_ARCHIVE | cgame/cg_main.c:1679 | (camera/demo-navigation related) |
| `cg_autoChaseMissileFilter` | `gl rl pg bfg gh ng pl` | CVAR_ARCHIVE | cgame/cg_main.c:1680 | (camera/demo-navigation related) |
| `cg_cameraUpdateFreeCam` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2430 | (camera/demo-navigation related) |
| `cg_chaseMovementKeys` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2617 | (camera/demo-navigation related) |
| `cg_chaseThirdPerson` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2615 | (camera/demo-navigation related) |
| `cg_chaseUpdateFreeCam` | `1` | CVAR_ARCHIVE | cgame/cg_main.c:2616 | (camera/demo-navigation related) |

### Top 20 most fragmovie-relevant wolfcam COMMANDS (judgment pick)

| Command | Source | Why it matters |
|---------|--------|----------------|
| `freecam` | cgame/cg_consolecmds.c:8478 | toggle/set free cinematic camera |
| `seekclock` | cgame/cg_consolecmds.c:8482 | seek demo to wall-clock timestamp — core WolfWhisperer automation hook |
| `seek` | client/cl_main.c:7185 | seek demo to arbitrary server time |
| `seeknext` | client/cl_main.c:7187 | skip to next event/snapshot |
| `seekprev` | client/cl_main.c:7188 | skip to previous event/snapshot |
| `seekend` | client/cl_main.c:7186 | seek to end of demo |
| `fastforward` | client/cl_main.c:7183 | accelerate demo playback |
| `rewind` | client/cl_main.c:7182 | reverse demo playback |
| `pause` | client/cl_main.c:7189 | pause demo |
| `pov` | client/cl_main.c:7194 | switch POV to a specified client slot |
| `chase` | cgame/cg_consolecmds.c:8509 | chase-cam to a player |
| `video` | client/cl_main.c:7174 | begin AVI capture (starts cl_avi* pipeline) |
| `stopvideo` | client/cl_main.c:7175 | stop AVI capture |
| `addcamerapoint` | cgame/cg_consolecmds.c:8510 | add a spline knot for the camera path |
| `clearcamerapoints` | cgame/cg_consolecmds.c:8511 | reset the camera path |
| `playcamera` | cgame/cg_consolecmds.c:8512 | play back the camera path |
| `stopcamera` | cgame/cg_consolecmds.c:8513 | stop camera path playback |
| `savecamera` | cgame/cg_consolecmds.c:8514 | persist camera path to file |
| `loadcamera` | cgame/cg_consolecmds.c:8516 | load camera path from file |
| `at` | cgame/cg_consolecmds.c:8546 | schedule a console command at a demo time (WolfWhisperer automation hook) |
