/*
 * A .dm_73 BECOMES A SNAPSHOT FEED.
 *
 * Decoded with the engine's own msg.c and huffman.c -- the functions that fill
 * cl.snapshots inside WolfcamQL -- so a snapshot handed to cgame here is the
 * one wolfcam would hand it. Every branch has a counterpart in cl_parse.c /
 * cl_main.c / cl_cgame.c (line numbers in the comments are WolfcamQL 11.3).
 * DM73Parser in Python is the independent cross-check (gate G1).
 *
 * The reader keeps ITS OWN gamestate current as `cs` commands arrive
 * (CL_ConfigstringModified). cgame is started only at a pass's pre-roll, so
 * every configstring change before that -- joins, scores, models, the round
 * clock -- must already be in the gamestate cgame is handed.
 *
 * Where this deliberately differs from the client, it says so:
 *   - snapshot ping is 0. In playback the client computes it from
 *     cls.realtime against empty outPackets, i.e. from the wall clock, which
 *     would make two renders of one demo differ.
 *   - svc_download and svc_voip are fatal. Neither carries a length the
 *     reader could skip, and a demo with one is reported, never guessed past.
 *   - CS91_STEAM_WORKSHOP_IDS does not set com_workshopids: it only feeds
 *     workshop downloads, which PANTHEON never performs.
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/cgame/cg_public.h"
#include "pantheon_demo_feed.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* client.h: MAX_PARSE_ENTITIES (PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES) */
#define PD_MAX_PARSE_ENTITIES (PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES)

typedef struct {                        /* clSnapshot_t, the fields a demo fills */
    qboolean      valid;
    int           messageNum, deltaNum, serverTime, snapFlags, serverCommandNum;
    byte          areamask[MAX_MAP_AREA_BYTES];
    playerState_t ps;
    int           numEntities, parseEntitiesNum;
} pdSnap_t;

static struct {
    FILE         *f;
    int           messageSeq;          /* clc.serverMessageSequence */
    int           commandSeq;          /* clc.serverCommandSequence */
    int           clientNum, checksumFeed;
    gameState_t   gs;
    char          bigcs[BIG_INFO_STRING];
    entityState_t baselines[MAX_GENTITIES];
    pdSnap_t      snaps[PACKET_BACKUP];
    entityState_t parse[PD_MAX_PARSE_ENTITIES];
    int           parseNum;            /* cl.parseEntitiesNum */
    pdSnap_t      snap;                /* cl.snap */
    int           gamestates;          /* how many svc_gamestate seen */
    int           queueFrom;           /* commands with seq > this go to cgame */
} pd;

/* pantheon_cg_feed.c */
void     PANTHEON_CG_ApplyServerCommand(int seq, const char *text);
void     PANTHEON_GameState_Set(gameState_t *gs, int index, const char *value);
qboolean PANTHEON_GameState_Command(gameState_t *gs, char *bigcs, int bigcsSize,
                                    const char *text, const char **rescanned);

#define PD_ENT(base, i) (&pd.parse[((base) + (i)) & (PD_MAX_PARSE_ENTITIES - 1)])

static void PD_DeltaEntity(msg_t *msg, pdSnap_t *frame, int newnum,
                           entityState_t *old, qboolean unchanged)    /* cl_parse.c:80 */
{
    entityState_t *state = PD_ENT(pd.parseNum, 0);

    if (unchanged) *state = *old;
    else           MSG_ReadDeltaEntity(msg, old, state, newnum);
    if (state->number == MAX_GENTITIES - 1) return;   /* delta removed */
    pd.parseNum++;
    frame->numEntities++;
}

static void PD_ParsePacketEntities(msg_t *msg, const pdSnap_t *oldframe,
                                   pdSnap_t *newframe)               /* cl_parse.c:108 */
{
    int            newnum, oldindex = 0, oldnum;
    entityState_t *oldstate = NULL;

    newframe->parseEntitiesNum = pd.parseNum;
    newframe->numEntities = 0;
    if (!oldframe || oldindex >= oldframe->numEntities) oldnum = 99999;
    else { oldstate = PD_ENT(oldframe->parseEntitiesNum, oldindex); oldnum = oldstate->number; }

#define PD_NEXT_OLD() do { oldindex++; \
        if (oldindex >= oldframe->numEntities) oldnum = 99999; \
        else { oldstate = PD_ENT(oldframe->parseEntitiesNum, oldindex); \
               oldnum = oldstate->number; } \
    } while (0)

    for (;;) {
        newnum = MSG_ReadBits(msg, GENTITYNUM_BITS);
        if (newnum == MAX_GENTITIES - 1) break;
        if (msg->readcount > msg->cursize)
            Com_Error(ERR_DROP, "PANTHEON demo: packet entities past end of message "
                                "(%d > %d, entity %d)", msg->readcount, msg->cursize, newnum);
        while (oldnum < newnum) {              /* unchanged from the old frame */
            PD_DeltaEntity(msg, newframe, oldnum, oldstate, qtrue);
            PD_NEXT_OLD();
        }
        if (oldnum == newnum) {                /* delta from the old frame */
            PD_DeltaEntity(msg, newframe, newnum, oldstate, qfalse);
            PD_NEXT_OLD();
            continue;
        }
        if (oldnum > newnum)                   /* delta from the baseline */
            PD_DeltaEntity(msg, newframe, newnum, &pd.baselines[newnum], qfalse);
    }
    while (oldnum != 99999) {                  /* the rest of the old frame */
        PD_DeltaEntity(msg, newframe, oldnum, oldstate, qtrue);
        PD_NEXT_OLD();
    }
#undef PD_NEXT_OLD
}

static void PD_ParseSnapshot(msg_t *msg)                             /* cl_parse.c:383 */
{
    pdSnap_t  ns, *old;
    int       deltaNum, len, oldMessageNum;

    memset(&ns, 0, sizeof(ns));
    ns.serverCommandNum = pd.commandSeq;       /* commands read before svc_snapshot */
    ns.serverTime = MSG_ReadLong(msg);
    ns.messageNum = pd.messageSeq;
    deltaNum = MSG_ReadByte(msg);
    ns.deltaNum = deltaNum ? ns.messageNum - deltaNum : -1;
    ns.snapFlags = MSG_ReadByte(msg);

    if (ns.deltaNum <= 0) {
        ns.valid = qtrue;                      /* uncompressed frame */
        old = NULL;
    } else {
        if (deltaNum >= PACKET_BACKUP)
            Com_Printf("PANTHEON demo: deltaNum %d invalid\n", deltaNum);
        old = &pd.snaps[ns.deltaNum & PACKET_MASK];
        if (!old->valid) {
            Com_Printf("PANTHEON demo: delta from invalid frame %d -> %d\n",
                       ns.deltaNum, pd.messageSeq);
            ns.valid = qfalse;
        } else if (old->messageNum != ns.deltaNum) {
            Com_Printf("PANTHEON demo: delta frame too old\n");
            ns.valid = qfalse;
        } else {
            /* :464 -- parseEntitiesNum too old is accepted while a demo plays */
            ns.valid = qtrue;
        }
    }

    len = MSG_ReadByte(msg);
    if (len > (int)sizeof(ns.areamask))
        Com_Error(ERR_DROP, "PANTHEON demo: invalid areamask size %d", len);
    MSG_ReadData(msg, &ns.areamask, len);
    MSG_ReadDeltaPlayerstate(msg, old ? &old->ps : NULL, &ns.ps);
    PD_ParsePacketEntities(msg, old, &ns);

    if (!ns.valid) return;                     /* read fully, then dropped */

    /* :519 -- invalidate the frames between the last good one and this one,
     * so a dropped packet cannot look like a valid delta source later. */
    oldMessageNum = pd.snap.messageNum + 1;
    if (ns.messageNum - oldMessageNum >= PACKET_BACKUP)
        oldMessageNum = ns.messageNum - (PACKET_BACKUP - 1);
    for (; oldMessageNum < ns.messageNum; oldMessageNum++)
        pd.snaps[oldMessageNum & PACKET_MASK].valid = qfalse;

    pd.snap = ns;                              /* :529; ping: see header */
    pd.snaps[ns.messageNum & PACKET_MASK] = ns;   /* :591 */
}

static void PD_ParseGamestate(msg_t *msg)                            /* cl_parse.c:830 */
{
    entityState_t nullstate;
    int           cmd, i, len, newnum, p;
    const char   *value;
    char         *s;

    /* :849 CL_ClearState -- everything parsed under the old gamestate goes */
    memset(&pd.gs, 0, sizeof(pd.gs));
    memset(pd.baselines, 0, sizeof(pd.baselines));
    memset(pd.snaps, 0, sizeof(pd.snaps));
    memset(&pd.snap, 0, sizeof(pd.snap));
    pd.parseNum = 0;
    pd.bigcs[0] = 0;
    pd.gamestates++;

    pd.commandSeq = MSG_ReadLong(msg);         /* :852 */
    pd.gs.dataCount = 1;
    for (;;) {
        cmd = MSG_ReadByte(msg);
        if (cmd == svc_EOF) break;
        if (cmd == svc_configstring) {
            i = MSG_ReadShort(msg);
            if (i < 0 || i >= MAX_CONFIGSTRINGS)
                Com_Error(ERR_DROP, "PANTHEON demo: configstring %d out of range", i);
            s = MSG_ReadBigString(msg);
            len = strlen(s);
            if (len + 1 + pd.gs.dataCount > MAX_GAMESTATE_CHARS)
                Com_Error(ERR_DROP, "PANTHEON demo: MAX_GAMESTATE_CHARS exceeded");
            if (i == 0) {                      /* :885 -- msg.c picks field tables from this */
                value = Info_ValueForKey(s, "protocol");
                p = atoi(value);
                Com_Printf("PANTHEON demo: gamestate protocol %d\n", p);
                Cvar_Set("real_protocol", value);
                if (p >= 66 && p <= 71)       Cvar_Set("protocol", va("%d", PROTOCOL_Q3));
                else if (p == 73)             Cvar_Set("protocol", "73");
                else if (p == 90)             Cvar_Set("protocol", "90");
                else if (p == PROTOCOL_QL)    Cvar_Set("protocol", va("%d", PROTOCOL_QL));
                else if (strlen(value) == 0)  Cvar_Set("protocol", va("%d", PROTOCOL_QL));
                else {
                    Com_Printf("PANTHEON demo: unknown protocol %d, trying %d\n", p, PROTOCOL_QL);
                    Cvar_Set("protocol", va("%d", PROTOCOL_QL));
                }
                value = Info_ValueForKey(s, "com_protocol");   /* :913 */
                p = atoi(value);
                if (p >= 66 && p <= 71) {
                    Cvar_Set("real_protocol", value);
                    Cvar_Set("protocol", va("%d", PROTOCOL_Q3));
                }
            }
            pd.gs.stringOffsets[i] = pd.gs.dataCount;
            memcpy(pd.gs.stringData + pd.gs.dataCount, s, len + 1);
            pd.gs.dataCount += len + 1;
        } else if (cmd == svc_baseline) {
            newnum = MSG_ReadBits(msg, GENTITYNUM_BITS);
            if (newnum < 0 || newnum >= MAX_GENTITIES)
                Com_Error(ERR_DROP, "PANTHEON demo: baseline %d out of range", newnum);
            memset(&nullstate, 0, sizeof(nullstate));
            MSG_ReadDeltaEntity(msg, &nullstate, &pd.baselines[newnum], newnum);
        } else {
            Com_Error(ERR_DROP, "PANTHEON demo: bad gamestate command byte %d", cmd);
        }
    }
    pd.clientNum = MSG_ReadLong(msg);          /* :961 */
    pd.checksumFeed = MSG_ReadLong(msg);
}

static void PD_ServerCommand(msg_t *msg)                             /* cl_parse.c:1338 */
{
    int         seq = MSG_ReadLong(msg);
    char       *s = MSG_ReadString(msg);
    char        text[BIG_INFO_STRING];
    const char *rescanned;

    if (pd.commandSeq >= seq) return;          /* already stored */
    pd.commandSeq = seq;
    Q_strncpyz(text, s, sizeof(text));         /* s is msg.c's static buffer */

    /* Keep the reader's gamestate current whether or not cgame is running --
     * the same rule cgame's copy is updated with (pantheon_cg_feed.c). */
    Cmd_TokenizeString(text);
    PANTHEON_GameState_Command(&pd.gs, pd.bigcs, sizeof(pd.bigcs), text, &rescanned);

    /* cgame exists for this pass: it executes the command itself, from ITS
     * copy of the gamestate, exactly as CL_GetServerCommand would. */
    if (seq > pd.queueFrom) PANTHEON_CG_ApplyServerCommand(seq, text);
}

static void PD_ParseServerMessage(msg_t *msg)                        /* cl_parse.c:1703 */
{
    int cmd;

    MSG_Bitstream(msg);
    (void)MSG_ReadLong(msg);                   /* reliableAcknowledge */
    for (;;) {
        if (msg->readcount > msg->cursize)
            Com_Error(ERR_DROP, "PANTHEON demo: read past end of server message");
        cmd = MSG_ReadByte(msg);
        if (cmd == svc_EOF && MSG_LookaheadByte(msg) == svc_extension) {
            MSG_ReadByte(msg);                 /* the svc_extension byte */
            cmd = MSG_ReadByte(msg);
            if (cmd == -1) cmd = svc_EOF;      /* dangling huffman bits */
        }
        if (cmd == svc_EOF) break;
        switch (cmd) {
        case svc_nop:           break;
        case svc_serverCommand: PD_ServerCommand(msg); break;
        case svc_gamestate:     PD_ParseGamestate(msg); break;
        case svc_snapshot:      PD_ParseSnapshot(msg); break;
        default:                               /* svc_download, svc_voip, garbage */
            Com_Error(ERR_DROP, "PANTHEON demo: unsupported server message %d", cmd);
        }
    }
}

/* ---- the reader's public surface: pantheon_demo_feed.h ----------------- */

qboolean PANTHEON_Demo_Open(const char *path)
{
    PANTHEON_Demo_Close();
    memset(&pd, 0, sizeof(pd));
    pd.queueFrom = 0x7fffffff;                 /* nothing to cgame until a pass starts */
    pd.f = fopen(path, "rb");
    return pd.f != NULL;
}

/* CL_ReadDemoMessage (cl_main.c:1063). qfalse at the end of the demo. */
qboolean PANTHEON_Demo_ReadMessage(void)
{
    static byte data[MAX_MSGLEN];
    msg_t buf;
    int   seq, len;

    if (!pd.f || fread(&seq, 4, 1, pd.f) != 1) return qfalse;
    pd.messageSeq = LittleLong(seq);
    MSG_Init(&buf, data, sizeof(data));
    if (fread(&len, 4, 1, pd.f) != 1) return qfalse;
    len = LittleLong(len);
    if (len == -1) return qfalse;              /* the demo's end marker */
    if (len < 0 || len > buf.maxsize)
        Com_Error(ERR_DROP, "PANTHEON demo: message length %d > MAX_MSGLEN (%d)",
                  len, buf.maxsize);
    if ((int)fread(buf.data, 1, len, pd.f) != len) {
        Com_Printf("PANTHEON demo: file was truncated\n");
        return qfalse;
    }
    buf.cursize = len;
    buf.readcount = 0;
    PD_ParseServerMessage(&buf);
    return qtrue;
}

/* CL_GetSnapshot (cl_cgame.c:140) for the latest snapshot, with its checks. */
qboolean PANTHEON_Demo_Latest(snapshot_t *out)
{
    int i, count;

    if (!pd.snap.valid) return qfalse;
    if (pd.parseNum - pd.snap.parseEntitiesNum >= PD_MAX_PARSE_ENTITIES) return qfalse;  /* :184 */
    memset(out, 0, sizeof(*out));
    out->snapFlags = pd.snap.snapFlags;
    out->serverCommandSequence = pd.snap.serverCommandNum;
    out->ping = 0;
    out->serverTime = pd.snap.serverTime;
    out->messageNum = pd.snap.messageNum;
    memcpy(out->areamask, pd.snap.areamask, sizeof(out->areamask));
    out->ps = pd.snap.ps;
    count = pd.snap.numEntities;
    if (count > MAX_ENTITIES_IN_SNAPSHOT) {
        Com_Printf("PANTHEON demo: truncated %i entities to %i\n", count, MAX_ENTITIES_IN_SNAPSHOT);
        count = MAX_ENTITIES_IN_SNAPSHOT;
    }
    out->numEntities = count;
    for (i = 0; i < count; i++) out->entities[i] = *PD_ENT(pd.snap.parseEntitiesNum, i);
    return qtrue;
}

void PANTHEON_Demo_QueueCommandsAfter(int seq)   { pd.queueFrom = seq; }
int  PANTHEON_Demo_CommandSequence(void)         { return pd.commandSeq; }
int  PANTHEON_Demo_MessageSequence(void)         { return pd.messageSeq; }
int  PANTHEON_Demo_ClientNum(void)               { return pd.clientNum; }
int  PANTHEON_Demo_ChecksumFeed(void)            { return pd.checksumFeed; }
int  PANTHEON_Demo_GamestateCount(void)          { return pd.gamestates; }
const gameState_t *PANTHEON_Demo_GameState(void) { return &pd.gs; }
void PANTHEON_Demo_Close(void) { if (pd.f) fclose(pd.f); pd.f = NULL; }
