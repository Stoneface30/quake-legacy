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
 * vendor/common.c — STUB PLACEHOLDER
 *
 * Real source:
 *   engine/engines/_canonical/code/qcommon/common.c  (GPL-2.0)
 *
 * Required by: msg.c (Com_Printf, Com_Error, Com_Memset/Memcpy shims)
 * Purpose:     Minimal Q3A "common" utilities — error/print routing and
 *              memory helpers used by the bit-stream decoder.
 *
 * NOTE: The full common.c brings in substantial engine machinery not needed
 * for a standalone parser.  At FT-1 alpha, consider replacing this with a
 * minimal shim (vendor/common_shim.c) that provides only the symbols that
 * msg.c / huffman.c actually import, avoiding conflicts with the C++ stdlib.
 *
 * To populate this stub:
 *   cp engine/engines/_canonical/code/qcommon/common.c \
 *      creative_suite/engine/parser/vendor/common.c
 *
 * GPL-2.0 header above must be preserved verbatim.
 *
 * FT-1 status: STUB — intentionally empty.
 */

/* Intentionally empty — replace with real common.c (or a shim) before building */
