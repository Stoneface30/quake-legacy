# Community post — QUAKE LEGACY

Draft to accompany `output/summary/QUAKE_LEGACY_project.mp4`. Every figure is
read from the project's own artifacts; nothing here is rounded up for effect.

No opponent names appear anywhere. The repo is public and that rule holds.

---

## Short version (forum / Discord / Reddit)

**I found a decade of my Quake Live matches sitting unreadable on disk, so I
wrote a parser that reads them properly. It recovered 214,184 kills.**

I have 6,445 `.dm_73` demos from Clan Arena, 2010 to 2013. I wanted to build
fragmovies from them automatically. The problem was that the demos read almost
empty — older ones returned 0 to 3 kills each, which I assumed meant the older
protocol eras were simply broken or different.

They were not. The bug was mine.

Quake's demo format packs several service messages into one packet. My
dispatcher read the first one and stopped, so every snapshot that happened to
follow a `serverCommand` in the same packet was silently thrown away. Nothing
errored. The demos just looked quiet.

Reading each packet through to `svc_EOF` changed the same files from 0-3 kills
to 103-296 kills. Across the corpus:

- **6,445 demo files → 4,292 unique** (2,153 were byte-identical copies)
- **4,292 parsed, 0 failures, 0 packet errors**
- **215,831 obituary events → 214,184 kills** after removing suicides and
  collapsing snapshot repeats
- The old database held **222**

So a decade of play went from invisible to indexed.

**What the parser gives you per kill:** attacker, victim, weapon, exact server
time, round, and which player is *you* — taken from the protocol's playerstate
stream rather than from your nickname, so it survives name changes, colour
codes and clan tags. On top of that it tags airshots, air rockets, rail work,
big flicks, weapon combos, multikills and quad kills, and it reconstructs clutch
rounds (last one standing, round still won).

It is written in Python, it is in the repo, and the format work is documented as
it was found.

**Where it is going:** cutting frags straight from demos instead of from clips I
hand-cut years ago; landing impacts on the beat; then third-person and camera
work driven by demo data. The goal is `pip install quake-legacy` — give it
demos, get a fragmovie.

The Q3 engine was given to us open source. This is a small piece back.

→ github.com/Stoneface30/quake-legacy

---

## Longer version (blog / README intro)

### The thing that was actually wrong

If you have written a Q3-family demo parser you will recognise this shape. A
packet is a sequence number, a length, and a Huffman-compressed payload. Inside
the payload is a stream of service messages terminated by `svc_EOF`. The
messages you care about are `svc_snapshot` (the entity deltas) and
`svc_serverCommand` (scoreboards, teammate status, chat).

My dispatcher handled one message per packet.

That is fine for a packet that holds only a snapshot, which is most of them in a
quiet moment. It is catastrophic in a busy round, because that is exactly when
the server bundles a `serverCommand` in front of the snapshot — and the kill you
wanted was in the snapshot behind it.

The failure mode is the worst kind: no exception, no warning, a perfectly
plausible number at the end. Old demos "had fewer kills". I spent real time
believing the 2010-2011 builds used a different entity-state layout before
testing the assumption that the reader was complete.

There was a second bug underneath, and it is worth naming separately because
merging the two is what cost the time: a broad `except Exception: pass` around
the dispatch call was swallowing a `NameError`. So one of my diagnostic runs
produced a confident, wrong measurement that pointed the investigation further
in the wrong direction. The handler now counts failures and records the first
one; it never silently discards.

### How it was verified rather than assumed

Recovering a big number is easy. Trusting it is the work.

- **2012 demos** carry a `tinfo` servercommand — teammate status including
  health. A teammate's health crossing >0 → 0 is an independent death signal,
  decoded by a completely different code path from the entity stream. On the
  reference demo: 47 death proxies, **47 matched to a decoded kill for the same
  victim, 0 unmatched**, lag median 600 ms.
- **2010-2011 demos do not emit `tinfo` at all.** A servercommand census proves
  it — that build sends `cs`, `scores`, `bcs*`, `print`, `rcmd`, `map_restart`
  and nothing else. It is a property of the build, not of the decoder.
- I initially claimed the 2011 `scores` command gave 100% recall as a death
  oracle. **That was wrong and I withdrew it.** Field 1 moves for several
  clients at once on every update — it is a round-result signal, not an
  individual death. It supports timing and nothing more.
- So obituary extraction is **certified for 2012** and **provisional for
  2010-2011**, with the remaining check written up as a ten-minute manual
  procedure against an independent client. Core corpus parsing — 4,292/4,292,
  zero failures, zero packet errors — is certified outright.

Stating the gap is the point. A number you cannot defend is not a result.

### What else is in the box

The parser is the foundation, but the repo is a whole pipeline:

- ranks frags, and groups them into **capture-worthy windows** rather than
  isolated kills, because a wolfcam capture records a span of time
- reconstructs **clutch rounds** — 1,746 of them where the recorder was last
  alive and still won
- analyses a music library for tempo and bar grid (1,483 tracks) and picks a
  track whose bars fit the edit's clip pacing
- renders, paces and scores the video, then **measures the output after
  encoding** — every export is checked for true peak, loudness and a clean full
  decode before it counts as finished

That last one exists because I shipped audio that clipped. Predicting loudness
from the filter graph is not the same as measuring the file.

### Where it goes next

The hand-cut archive is finished: 1,075 source clips, every one used exactly
once. But those clips were my selection from years ago. The recovered database
is the more interesting asset — it lets me go back through the whole corpus and
build highlights from material the broken parser made invisible.

Next: frags cut straight from demos, impacts landing on the beat, then camera
work driven by demo data.

→ github.com/Stoneface30/quake-legacy

---

## Posting notes

- Lead with the bug and the recovery. "I fixed a parser" is dull; "0-3 kills
  became 103-296 on the same files" is the hook.
- The withdrawn `scores` claim is worth keeping in. It is the part that makes
  the rest credible.
- Attach `QUAKE_LEGACY_project.mp4` (1:05). The career video is personal — good
  for your own channel, less so for a technical audience.
- Expect "why not UberDemoTools / QLDT?" — the honest answer is that they exist
  and are good; this is a full pipeline to fragmovie, and it was also the only
  way to be sure what every bit meant.
