# Bio, Reddit post, and where to launch

Written 2026-08-31. Everything factual here comes from the project's own
artifacts or from your public channel; nothing is invented.

**One thing I could not do:** read your existing YouTube "About" text. The
channel redirects to a cookie-consent wall and I won't accept consent banners on
your behalf. So these bios are written fresh from what I *could* verify —
channel `@Stony_`, display name **Stony**, and three hand-made videos: *Clan
Arena Tribute 1*, *Clan Arena Tribute 2*, *Quakelive Tribute part 3*. If your
current About says something you want kept, paste it and I'll merge rather than
replace.

---

## Bio

### Channel description (YouTube About, ~50 words)

> Quake Live Clan Arena, 2010–2013. I recorded nearly every match I played and
> then spent a decade not being able to do anything with it.
>
> Now I'm building the tool that reads those demos and cuts the fragmovies for
> me — and putting the whole thing out in the open.
>
> pTn.Tr4sH · Stoneface

### Short bio (Reddit / Discord / forum signature, ~30 words)

> Quake Live CA player, 2010–2013 — pTn.Tr4sH. 6,445 demos on disk. Built a
> protocol-73 parser to get the frags back out. 214,184 kills recovered, and the
> fragmovies build themselves now.

### Long bio (site / README / press)

> **Stony** — pTn.Tr4sH, sometimes Stoneface — played Quake Live Clan Arena from
> 2010 to 2013, mostly on campgrounds, asylum and overkill, and recorded almost
> all of it. 6,445 demo files. Three fragmovies came out of that decade, every
> cut placed by hand.
>
> The rest sat unusable. Demo files are not video: they are network traffic, and
> reading them well enough to find the good moments is its own problem. Existing
> tools skipped most of the older protocol eras.
>
> So he wrote the parser. **QUAKE LEGACY** reads `.dm_73` end to end — Huffman
> decode, snapshots, entity deltas — and pulls out every kill with its attacker,
> victim, weapon and exact server time, identifying the recording player from the
> protocol rather than from a nickname that changed a dozen times. Across the
> corpus that recovered **214,184 kills**, of which **34,987** are his own, plus
> **1,746 clutch rounds** where he was the last one alive and still won the round.
>
> The old database held 222.
>
> Everything past the parser is pipeline: ranking frags, grouping them into
> capture-worthy sequences, cutting and scoring the video, and measuring every
> export for loudness and true peak before it counts as finished. It is open
> source, and the format findings are documented as they are made — the Q3
> engine was given away, and this is a piece back.
>
> `github.com/Stoneface30/quake-legacy` · `youtube.com/@Stony_`

### Notes on the writing

- The hook is the **recovery**, not the tooling. "I wrote a parser" is a
  hobby; "a decade of my matches was unreadable and now it isn't" is a story.
- The **222 → 214,184** line does the heaviest lifting. Keep it wherever there
  is room.
- "Every cut placed by hand" earns the automation. It says you know what the
  work costs.
- Avoid claiming rank or skill in the bio. The numbers are verifiable; a
  self-assessment is not, and the audience will discount it.

---

## Reddit post

Two phases, as you asked. Rephrase freely — the numbers are the part that must
stay accurate.

**Suggested title:**

> I recorded a decade of Quake Live matches, then found my own parser bug was
> hiding 99.9% of them. Fixed it — 214,184 kills recovered.

**Body:**

---

I played Quake Live Clan Arena from 2010 to 2013 and recorded almost everything:
6,445 `.dm_73` demos, about 13 GB. Over the years I made three fragmovies from
it, cut entirely by hand. Everything else just sat there.

Last year I started building something to do it automatically. Two phases.

**Phase 1 — finish the footage I already had.**

I had roughly a thousand clips cut out of those demos years ago, sitting in
folders. The pipeline now takes them, packs them into ~5 minute videos, picks
music, paces the cuts, and measures the audio after encoding so nothing ships
clipped. Every clip gets used exactly once, tracked by full path, and a clip is
only marked "used" after its video passes a full decode check and a true-peak
check. If a video fails QA its clips go back in the pool.

That produced a complete archive of the hand-cut material — no leftovers, no
duplicates.

Along the way it found a source file that was 221 MB of what looked like garbage.
Turned out only the first 28 KB — the AVI header — was zeroed; the video data was
intact. Grafting a header from a sibling clip recovered it.

**Phase 2 — the part that actually matters: reading the demos.**

Demos aren't video. They're recorded network traffic: Huffman-compressed
packets, snapshots, entity deltas. To find frags you have to decode the protocol.

My parser did decode it — and returned almost nothing on older demos. 0 to 3
kills each. I assumed the 2010–2011 builds used a different entity layout and
spent real time chasing that.

The bug was mine. A packet holds *several* service messages terminated by
`svc_EOF`. My dispatcher read the first one and stopped. So any snapshot that
happened to sit behind a `serverCommand` in the same packet was silently thrown
away — which is exactly what happens in a busy round, because that's when the
server bundles messages together.

No exception. No warning. Just a believable, wrong number.

Reading each packet through to `svc_EOF`:

- **6,445 demo files → 4,292 unique** (2,153 were byte-identical copies)
- **4,292 parsed, 0 failures, 0 packet errors**
- **214,184 kills**, of which **34,987** are mine
- **1,746 clutch rounds won** — last one alive, round still won
- The old database had **222**

The same demos that read 0–3 kills now read 103–296.

**Verifying it, because a big number is easy and trusting it is the work:**

2012-era demos carry a `tinfo` servercommand with teammate health. A teammate's
health crossing >0 → 0 is an independent death signal decoded by a completely
different code path. On the reference demo: 47 death signals, 47 matched to a
decoded kill for the same victim, 0 unmatched.

2010–2011 demos don't emit `tinfo` at all — I confirmed that with a command
census rather than assuming. I initially claimed the `scores` command gave me
100% recall there, then measured it properly: the score field moves for several
players at once, so it's a round-result signal, not an individual death. I
withdrew the claim. That era is certified as "decodes coherently" but not
independently verified, and I'd rather say that than round it up.

**What it does with the data:** ranks frags by type (airshot, air rocket, rail,
flick, weapon combo, multikill), groups them into windows worth capturing rather
than isolated kills, and reconstructs clutch rounds. It knows which player is
*me* from the protocol's playerstate stream, so it survives every nickname
change.

**Where it's going:** cutting frags straight from the demos instead of from
clips I cut by hand years ago, landing impacts on the beat, then camera work
driven by demo data. Eventually `pip install quake-legacy` — point it at demos,
get a fragmovie.

Python, open source, and I'm documenting the format work as I go. The Q3 engine
was given to us. This is a small piece back.

github.com/Stoneface30/quake-legacy

---

### Posting notes

- Lead with the bug. The self-inflicted-bug angle is what makes this a story
  rather than a release announcement, and technical readers reward it.
- Keep the withdrawn `scores` claim in. It is the single most credibility-
  building paragraph in the post.
- Expect **"why not UberDemoTools / QLDT?"** — answer honestly: they exist,
  they're good, this is a full pipeline to finished video, and writing the
  parser was the only way to be certain what every bit meant.
- Expect **"post the videos"**. Have two or three of your top 10 ready as
  direct links.
- Don't post the career-stats video to a technical subreddit. It's personal;
  it belongs on your channel.

---

## Where to post

Ranked by how likely this is to land, not by size.

| Platform | Fit | Angle |
|---|---|---|
| **r/Quake** | Very high | The fragmovies *and* the recovery story. Your home audience. |
| **r/QuakeLive** | Very high | Smaller but exactly the right people; CA players will know the maps. |
| **ESR (esreality.com)** | Very high | Where Quake movie culture actually lives. Post the movies, mention the tool. |
| **r/dataisbeautiful** | High | The career-stats video, framed as "a decade of my own matches, recovered from a parser bug". Needs the visual to lead. |
| **r/programming** | High | The `svc_EOF` bug alone. Title it as the bug, not the project. |
| **r/reverseengineering** | High | Protocol-73 decoding, the entity-delta ordinal work, the tinfo cross-check. |
| **r/gamedev** | Medium | The pipeline: automated editing, audio safety, coverage invariants. |
| **Hacker News** | Medium | "Show HN". Bimodal — either it resonates or it vanishes. The bug story is the only viable hook. |
| **YouTube** | — | Home for the videos. The stats video is a good channel trailer. |
| **quakeworld / Quake Discords** | Medium | Slow burn, but the people there will actually use the tool. |

**Sequencing that works:** ESR and r/Quake first, with the movies — that
audience gives you the credibility. Then r/programming and
r/reverseengineering with the bug story, linking the project. Then
r/dataisbeautiful with the stats video once there's something to point at.

Don't post everywhere in one day. A thread that gets replies is worth more than
five that don't, and you'll want to answer the "why not UDT" question properly
the first time.

---

## Technical section — the part to share with builders

Full document: [`docs/technical-overview.md`](technical-overview.md). It is
written to be linked directly when someone asks "how does it work" or "why not
just use Wolfcam", and it carries the end-to-end diagrams.

**What to paste when someone asks the Wolfcam question:**

> WolfcamQL is a demo *player* — it renders `.dm_73` and gives you camera
> control, and this project uses it for capture. What it cannot do is decide
> anything: you watch the demo, find the frag, note the timestamp, set up the
> camera, cut. A decade of demos means a decade of watching.
>
> QUAKE LEGACY *reads* the demo instead of playing it. It decodes protocol-73
> directly — no engine involved — and gets every kill with attacker, victim,
> weapon and server time, identifies the recording player from the playerstate
> stream so nickname changes don't matter, ranks the moments, and cuts and
> scores the video with audio safety gates. It replaces the person who was
> watching everything to find the timestamps, not Wolfcam's renderer.

**What to paste when someone asks about UberDemoTools:**

> UDT is real, good, and has existed for years — it parses demos and cuts them.
> The difference is scope: UDT is a demo-processing toolkit, this is an
> end-to-end pipeline that ends in a finished, music-scored, loudness-compliant
> video. I wrote the parser from scratch because being certain what every bit
> meant was the point, and because the format work is meant to be published.

**The three findings worth leading with technically:**

1. The `svc_EOF` bug — one packet holds several messages; stopping at the first
   silently discards snapshots in exactly the busy rounds you care about. 222
   kills became 214,184.
2. `areamask` is `areamaskLen + 1` bytes. Reading the documented length
   desynchronises the stream and drops ~74% of every demo, with no error.
3. The withdrawn `scores` claim. Measured properly, the field moves for several
   players at once, so it is a round-result signal and not a death oracle. That
   era is certified "decodes coherently" and explicitly not verified.

Number 3 is the most credibility-building thing in the whole kit. Lead with it
whenever the audience is technical.

---

## Sharing the tools

**What is public and what is not.** The repository is public. The demo corpus,
the rendered AVIs, the databases and every `.env` are not, and are gitignored —
demos carry opponent nicknames in the HUD, and none of that belongs in a public
repo. Anonymisation is a hard rule in the codebase, not a habit.

**What someone else can actually run today.** The parser and the render pipeline
run from the repository; the packaged CLI does not exist yet. Say that plainly —
"clone it and here is the entry point" sets the right expectation, "pip install"
does not.

**Licensing to state up front.** The vendored protocol code (`msg.c`,
`huffman.c`, `common.c`) comes from wolfcamql under GPL-2.0 with headers
preserved. Anyone forking this needs to know that before they build on it.

**If someone offers demos.** The interesting response is a corpus that is not
yours — different era, different protocol, different players. That is how the
2010–2011 verification gap actually gets closed. Ask for a handful, not a
drive.

---

## Presentation

**Order of the story, every time:**

1. A decade of recordings that could not be read.
2. The tool that was supposed to fix it returned believable, wrong numbers.
3. The bug was mine, and it was one line of control flow.
4. 222 → 214,184.
5. Here is what it builds now.

The recovery is the story. The pipeline is the payoff, not the hook.

**What to show, in order of how well it lands:**

| Asset | Where it works | Why |
|---|---|---|
| A finished Part (2–3 min excerpt) | Quake audiences, YouTube | Proof it produces something watchable |
| The 222 → 214,184 line | Everywhere | Single most compelling fact |
| Career-stats video | Your channel, r/dataisbeautiful | Personal; wrong tone for r/programming |
| The `svc_EOF` diagram | r/programming, HN, ESR | The bug is the hook |
| End-to-end pipeline diagram | Anyone asking "how" | Answers ten questions at once |

**Tone.** Do not claim rank or skill — the numbers are verifiable, a
self-assessment is not, and a technical audience discounts it instantly. Do not
oversell the automation either: say it cuts the video and gates the audio, not
that it "understands" the game.

**Have ready before posting:** two or three top-10 videos as direct links, the
technical overview link, and an honest answer to "what does it get wrong"
(A/V sync drift, and the unverified 2010–2011 era — both are in the doc).

---

## Production usage — the actual procedure

This is the runbook, in the order it is really done.

**1. Build the queue.** Every source clip is registered by full path with its
duration and tier. A clip is used exactly once across the whole series, tracked
by path, so nothing is silently duplicated or lost.

**2. Scan the corpus once.** Game-event detection is the expensive step, so it
is cached and reused: the same scan feeds the end-trim table *and* the music
selection. Never rescan the whole corpus for a taxonomy change.

```bash
python -m creative_suite.engine.tail_trim
```

**3. Launch the series.** The orchestrator packs a Part, picks its music,
renders, runs QA, and commits. It resumes from committed manifests, so it is
safe to interrupt.

```bash
python -u hl_series.py
```

**4. Leave it alone.** Duration, music choice and packing are *not* failure
conditions — only a hard failure justifies stopping a run: renderer crash,
unsafe audio, decode failure, duplicate consumption, missing source, a second
writer, disk-full risk, or manifest corruption. Interrupting an approved run to
retune pacing costs more than it saves.

**5. Let the supervisor handle stalls.** A hung renderer stays alive and holds
the lock — it looks healthy to every naive check. The supervisor watches for log
silence instead, and recovers by killing the tree and relaunching from the last
committed Part.

**6. Review, then regenerate.** Review is per-Part and specific ("the clip at
4:15 is cut short"), which turns into a measured fix rather than a taste
adjustment. Regeneration writes to its own directory (`QL_SERIES_DIR`,
`QL_WORK_DIR`, `QL_MANIFEST_DIR`, `QL_LOCK`) so a finished series is never
touched by a rerun.

**Rules that exist because breaking them cost a night:**

- Never trim the start of a clip. A clip that starts late has lost a frag.
- Music holds one fixed level. Match the action to the music, never the music
  to the action.
- Beat-sync moves seams and slow-mo strength — never clip duration.
- A Part is committed only after decode and true-peak both pass.
