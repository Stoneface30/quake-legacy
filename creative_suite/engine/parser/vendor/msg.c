/*
===========================================================================
Copyright (C) 1999-2005 Id Software, Inc.

This file is part of Quake III Arena source code.

Quake III Arena source code is free software; you can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Quake III Arena source code is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Quake III Arena source code; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
===========================================================================
*/

/*
 * vendor/msg.c — STUB PLACEHOLDER
 *
 * Real source:
 *   engine/engines/_canonical/code/qcommon/msg.c  (GPL-2.0)
 *   (wolfcamql-extended version with protocol-73 delta encoding)
 *
 * Required by: dm73_reader.cpp (FT-1 alpha)
 * Purpose:     MSG_Init, MSG_ReadBits, MSG_ReadByte, MSG_ReadShort,
 *              MSG_ReadLong, MSG_ReadString, MSG_ReadDeltaEntity —
 *              the bit-stream decoder that unpacks compressed demo frames.
 *
 * To populate this stub:
 *   cp engine/engines/_canonical/code/qcommon/msg.c \
 *      creative_suite/engine/parser/vendor/msg.c
 *
 * Then ensure q_shared.h and qcommon.h stubs/headers are also present.
 * GPL-2.0 header above must be preserved verbatim.
 *
 * FT-1 status: STUB — file intentionally empty to allow CMake configure step
 *              to succeed without the real source.  add_library(dm73 STATIC)
 *              will fail at compile time if this remains a stub — that is
 *              by design to force the copy step before building.
 */

/* Intentionally empty — replace with real msg.c before building */
