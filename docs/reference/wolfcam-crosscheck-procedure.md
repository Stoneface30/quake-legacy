# WolfcamQL cross-check — supervised procedure (D4)

This is the one certification item that cannot be closed unattended. Driving a
GUI Quake client from an automated session risks orphaning a process that holds
demo-file locks and hangs the desktop, which is exactly what Rule CS-4 exists to
prevent. So it is written as a short manual procedure instead, to be run while
someone is watching.

It should take about ten minutes.

## What is being checked

Whether an independent Quake Live client agrees with our parser about **who
killed whom, with what**, at three specific moments in one 2011 demo. Not that
Wolfcam can play the demo — that proves nothing about our decoding.

## The three probe events

Demo: `demos/CA-hearth-2011_08_02-18_48_01.dm_73`
Roster: client 0 `s73rn` (RED) · client 1 `Tr4sH` (SPECTATOR) · client 2
`NaikoMarie` (BLUE) — a 1v1 with a spectator, which is why every kill has
exactly one of victim/attacker equal to 0.

| # | server time | seek to | parser victim | parser attacker | parser MOD |
|---|---:|---|---|---|---|
| 1 | 70500 ms | `1:10` | 2 `NaikoMarie` | 0 `s73rn` | 11 LIGHTNING |
| 2 | 100050 ms | `1:40` | 0 `s73rn` | 2 `NaikoMarie` | 10 RAILGUN |
| 3 | 119600 ms | `1:59` | 0 `s73rn` | 2 `NaikoMarie` | 11 LIGHTNING |

Server time is milliseconds from the demo's own clock. Wolfcam's `seekclock`
takes `m:ss`, so the seek targets above are rounded down; step forward a second
or two to catch the kill feed.

## Procedure

1. Copy the demo where Wolfcam can see it:

```bash
cp "demos/CA-hearth-2011_08_02-18_48_01.dm_73" "engine/wolfcam/WolfcamQL/wolfcam-ql/demos/"
```

2. Launch the client with an isolated home path so nothing writes into the
   repo:

```bash
"engine/engines/ghidra/binaries/wolfcamql-11.3.exe" +set fs_homepath "G:/QUAKE_LEGACY/creative_suite/storage/wolfcam_capture" +set sv_pure 0 +demo CA-hearth-2011_08_02-18_48_01
```

3. For each probe, in the console:

```
seekclock 1:10
```

   then let it run a few seconds and read the kill feed at the top of the
   screen. Repeat with `1:40` and `1:59`.

4. Record what the client shows in the table below. `condump` writes the
   console to a file if that is easier than reading it live:

```
condump probe1.txt
```

5. Close the client normally (`quit` in the console). Do not leave it running —
   it holds a lock on the demo file.

## Result table — fill in from the client

| event | parser victim | Wolfcam victim | parser attacker | Wolfcam attacker | parser MOD | Wolfcam MOD |
|---|---|---|---|---|---|---|
| 1 @ 1:10 | NaikoMarie | | s73rn | | LIGHTNING | |
| 2 @ 1:40 | s73rn | | NaikoMarie | | RAILGUN | |
| 3 @ 1:59 | s73rn | | NaikoMarie | | LIGHTNING | |

## Interpreting it

- All three agree on victim and attacker → **`WOLFCAMQL CROSS-CHECK = PASS`**,
  and obituary certification can be upgraded.
- The kill feed shows the weapon icon rather than a MOD number. If the icon is
  unambiguous, record it; if the client does not expose the means of death in a
  readable form, write `not exposed` and treat MOD as **unavailable** rather
  than as a disagreement. A client that cannot show a field cannot disagree
  about it, and that must not become a permanent blocker.
- One event disagreeing → investigate **that event only**. Two or more
  disagreeing → the obituary decode is in question and certification stays at
  core-parsing level.

## Why these three

They are the same events used for the D3 probes, so the comparison is against
evidence already recorded in `output/probe_2011_obituaries.json`: raw eType 71 →
base 71 → normalized event 58, with ordinals `[1,2,5,12,14,19]` on probe 1 and
`[1,2,5,12,14,31]` on probes 2 and 3.

They also matter because 2011 is the era where the independent oracle is
weakest. That build emits no `tinfo` at all, and its `scores` signal turns out
to be **team/round-level** — field 1 moves for several clients at once, so it
cannot establish an individual death. Wolfcam is therefore the strongest
independent check available for this era, which is why the item is worth
completing rather than dropping.
