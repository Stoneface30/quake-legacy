# q3mme — Client/Server Split

q3mme keeps ioquake3's **full** client/server split intact, unlike wolfcamql which
gutted the server. This has implications for the port.

## Live code

- **Client side:** full ioquake3 client + q3mme demo extensions in cgame
- **Server side:** full Q3 server, runs as local loopback when playing demos
- **VMs:** cgame, game, ui — all three live, typically run as .qvm (bytecode)

## Demo playback flow (involves both sides)

Unlike wolfcam's "client-only, no simulation" approach:

1. `CL_PlayDemo_f` kicks off playback
2. Client sends a loopback `connect` request; local server accepts
3. Client reads demo messages and feeds them to the server side via
   `Sys_EnterLoopback` — server THINKS it's receiving packets from a network client
4. Server state machine runs, game VM simulates (but nothing happens because demo
   packets are authoritative)
5. Server generates snapshots that client then renders

Why this matters: q3mme supports **live spectator joins** on a playback session —
you can load a demo AND have other players connect to watch with you. Wolfcam can't.

## Implications for the port

Good news: proto-73 patches go into `qcommon/` which is shared. Both sides get them
automatically. The server side will happily accept proto-73 messages.

Bad news: some proto-73 server-side semantics may conflict with Q3's game VM:
- QL's hit registration is server-side, but q3mme's game VM won't simulate it
- QL scoring updates come through configstrings; game VM won't update scoreboard
  on its own — but that's fine because cgame handles scoreboard from configstrings

Net: **the server side runs but is mostly dormant during proto-73 demo playback**.
No changes needed there for basic playback. If we want live spectators with
proto-73 demos, that's a Phase 3.5 stretch goal.

## Where NOT to apply wolfcam hacks

Wolfcam forced `com_dedicated 0`, skipped botlib, stubbed `SV_Frame`. **Do NOT
port these into q3mme.** q3mme's server loop is fine as-is.

## Botlib

- q3mme keeps botlib live (unlike wolfcam)
- Not used during demo playback but used if we want to play vs bots in edit mode
- For our use case (pure fragmovie) botlib can be left alone — no changes

## VM vs native cgame

q3mme ships VM cgame by default. Wolfcam prefers native.

For the port, we have two options:
- **Option A — keep VM cgame:** compile wolfcam's cgame with q3lcc into a .qvm.
  Pros: stays a q3mme-compatible fork. Cons: q3lcc + wolfcam cgame may have
  compilation issues (wolfcam cgame was probably never built as VM).
- **Option B — native cgame:** build cgame as shared library. Pros: works guaranteed.
  Cons: diverges from q3mme upstream. Platform-specific .so/.dll handling.

**Decision:** start with Option B for speed; migrate to Option A if we plan to
upstream the patches to q3mme.

## Shared files affected by proto-73 port

- `qcommon/msg.c` — parses messages on BOTH sides
- `qcommon/q_shared.h` — constants seen by server, game VM, client, cgame, ui
- `qcommon/net_chan.c` — framing, shared

The game and ui VMs don't care about proto-73 directly (they see structs post-parse),
but their **struct layouts** (entityState_t, playerState_t) must match the patched
`q_shared.h`. If the VMs are built from the patched headers, we're fine.

If they're built from stock q3mme headers, there will be **silent memory corruption**:
the engine writes 64 clients' worth of state into a 32-client array. This is the
single biggest porting risk — **rebuild ALL VMs from patched headers**.
