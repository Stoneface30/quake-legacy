# Publishing Plan — QUAKE LEGACY (clips video + tool release + presentation video)

*Researched 2026-08-31. Web research: Internet Archive (web.archive.org CDX), ESReality, Plus Forward, Reddit, Discord directories. No fabricated data — every ranking number below comes from a specific archived page, URL included.*

---

## 1. Archived Rankings — What the Internet Archive Actually Holds

### 1.1 QLRanks.com (the era-correct Elo site, 2010–2015)

**18 archived snapshots of `qlranks.com/ca/player/Tr4sH` exist**, spanning 2012-02-26 to 2015-01-12. All were verified live via the CDX API and the pages fetched; headline numbers extracted verbatim.

Snapshot URL pattern: `https://web.archive.org/web/<TIMESTAMP>/http://www.qlranks.com/ca/player/Tr4sH`

| Snapshot date | World rank (CA) | CA Elo | Ladder | Games tracked | Win % | Country rank |
|---|---|---|---|---|---|---|
| 2012-02-26 | #225 | 1683 | Gold | 145 | 63% | France #9 |
| 2012-04-27 | #547 | 1681 | Gold | 384 | 56% | — |
| 2013-01-24 | #109 | 2052 | Gold | 855 | 56% | — |
| 2013-04-21 | #223 | 2078 | Gold | 1,082 | 57% | France #8 |
| 2013-06-20 | #69 | 2182 | Master | 1,431 | 56% | — |
| 2013-07-30 | #116 | 2257 | Master | 1,933 | 58% | — |
| 2013-08-24 | **#39** | 2270 | Master | 1,960 | 58% | — |
| 2013-10-28 | #45 | **2326** | Master | 2,370 | 58% | — |
| 2013-12-29 | #88 | 2305 | Master | 2,559 | 57% | **France #3** |
| 2014-02-27 | #225 | 2241 | Master | 2,785 | 57% | — |
| 2014-04-30 | #283 | 2250 | Master | 2,848 | 56% | — |
| 2014-07-05 | #427 | 2221 | Master | 2,856 | 56% | — |
| 2014-08-01 | #434 | 2221 | Master | 2,856 | 56% | — |
| 2014-09-05 | #441 | 2221 | Master | 2,856 | 56% | — |
| 2014-10-23 | #472 | 2221 | Master | 2,856 | 56% | — |
| 2015-01-12 | #573 | 2214 | Master | 2,858 | 56% | France #19 |

**Headline claims that are archive-backed (safe to publish):**
- Peak archived world rank: **#39 in Clan Arena worldwide** (2013-08-24 snapshot).
- Peak archived Elo: **2326, Master ladder** (2013-10-28 snapshot); the 30-day graph on the 2013-12-29 snapshot shows an in-window peak of 2367.
- **Top-3 Clan Arena player in France** (2013-12-29 snapshot).
- ~2,858 CA games tracked by QLRanks by 2015.
- The 2012-02-26 snapshot's embedded Elo graph shows the climb from ~866 to 1683 in one month — genuine "grind arc" material for the presentation video.

Key snapshot URLs:
- Peak world rank: `https://web.archive.org/web/20130824190007/http://qlranks.com/ca/player/Tr4sH`
- Peak Elo: `https://web.archive.org/web/20131028153309/http://www.qlranks.com/ca/player/Tr4sH`
- France #3: `https://web.archive.org/web/20131229010343/http://www.qlranks.com/ca/player/Tr4sH`
- Earliest: `https://web.archive.org/web/20120226211058/http://qlranks.com/ca/player/Tr4sH`
- Full list: `https://web.archive.org/web/*/qlranks.com/ca/player/Tr4sH`

**Ambiguity note:** the archived pages tag the player as France. This is the only "Tr4sH" with a CA page archived on QLRanks (no duel/TDM pages archived under that name), and the ESReality cross-reference below ties the name to clan Pantheon (pTn), so the identity match is strong — but state on publish that these are *your* pages so nobody assumes a name collision.

### 1.2 ESReality — the smoking gun

Two archived threads found via CDX; the first is also **still live on esreality.com**:

- **`https://www.esreality.com/post/2174150/tr4sh-fragmovie/`** — posted 2011-10-28 by Kapiter (Paris): *"Fragmovie edited by and featuring Tr4sh of Pantheon. Frags are all from CA pubs and cw."* Rated 4.5/10 by 11 voters; comments called the encode "cheap VHS porno from around 1976" and CA "boring". Archived copy: `https://web.archive.org/web/20130122033130/http://esreality.com/post/2174150/tr4sh-fragmovie/`
- Reply thread archived: `https://web.archive.org/web/20121101104646/http://esreality.com/post/2177250/re-tr4sh-fragmovie/`

This is a gift: the 2011 movie got roasted for encode quality — the 2026 release is the 15-years-later redemption, rendered by a custom parser + automated pipeline. Use it.

### 1.3 QLStats.net — nothing recoverable by name (honest result)

CDX domain-wide searches for `tr4sh`, `stoneface` on `qlstats.net` return **zero URLs**. Expected: QLStats used numeric player IDs (`qlstats.net/player/<id>`) keyed to Steam IDs, was teamplay/glicko focused, and covered the 2015–2022 Steam era — after the user's active period. Without the numeric ID, no player page can be located. **Do not claim any QLStats ranking.**

### 1.4 "Stoneface" — nothing recoverable (honest result)

No `stoneface` URLs on qlranks.com or qlstats.net in the archive. The alias exists only as the user's own attestation; don't cite rankings for it.

---

## 2. Platform Matrix

| Platform | Audience (est.) | Alive? | Self-promo stance | Best framing |
|---|---|---|---|---|
| **Plus Forward** (plusforward.net) | Core Quake scene; the ESR successor for news; has dedicated `/movies/` and `/quake/movies/` sections, fragmovie posts as recent as 2026 | Yes — active daily, 2026 LAN coverage | Fragmovie posts are *the content* — self-posting your own movie is the norm | News-style post: movie + the archive-mining story + open-source tool |
| **ESReality** (esreality.com) | Old-guard EU competitive crowd; smaller than its 2010 peak but forums active into 2026, `?a=movies` section still used | Yes | Fragmovie posts traditional and welcomed; brutal-but-honest comment culture | The redemption angle writes itself: link the 2011 thread (4.5/10) in the new post |
| **r/QuakeLive** | ~10–15k members (unverified — Reddit blocked automated checks; confirm sidebar count before posting), low volume, nostalgic | Yes, slow | Small-sub norms: genuine community content fine; check sidebar rules on post day | Nostalgia/archive: "13 GB of 2010–2013 CA demos, mined with a custom parser" |
| **r/quake** | ~80–90k (unverified) — largest Quake sub, mixed Q1/Q3/QL/QC | Yes | 10:1-style Reddit norms; OC videos with a story do well | Engineering + nostalgia crosspost after r/QuakeLive |
| **r/QuakeChampions** | ~30k (unverified) | Yes | Off-topic-ish for QL content | Skip or crosspost only the presentation video |
| **YouTube** | Long-tail; QL fragmovie uploads continue through 2025–26 (e.g. isevendeuce's midair series, "Fragged by sm4ll" 2010–2014 footage) | Yes | N/A — it's the hosting layer | Title convention: `<Name> — Quake Live CA Fragmovie (2010–2013)`; tags: quake live, fragmovie, clan arena, ql, frag highlights, quakecon |
| **Discord — House of Quake** | ~2,100 members, EU TDM/CTF pickups, running 2025 seasons; houseofquake.com | Yes | Share in media/clips channels; don't spam invites | Casual drop of the video + "tool is open source" |
| **Discord — QL Hub / pickup servers** | Findable via disdex.io/servers/quake-live and discord.me tag `quake live`; several CA/CTF pickup servers | Yes | Per-server rules; lurk first | Same as above |
| **Twitter/X** | Quake scene present but diffuse (casters, QC pros, plusforward account) | Yes | N/A | Thread: 3–4 clips + archive screenshots; tag @Plusforward |
| **GitHub Releases** | Devs + tinkerers; discoverability via topics `quake`, `quake-live`, `demo-parser`, `dm_73` | Yes | N/A — the distribution channel for the tool | Tag `v1.0`, ship README with sample output video embedded, binaries + pip instructions |
| **Church of Quake** (churchofquake.com) | Small fragmovie-reposting blog, posts QC/QL fragmovies | Yes | Reposts community movies — submit/notify | Send them the video link |

Audience numbers marked *unverified* could not be confirmed programmatically (Reddit blocks bots); verify the sidebar count when posting.

---

## 3. Launch Sequence

**Phase 0 — Prep (before anything goes public)**
1. Upload the initial clips video to YouTube as *unlisted*; finalize title/thumbnail/description (description links the GitHub repo and the archive.org ranking snapshots).
2. Repo hygiene: privacy sweep (no player names, no .dm_73/.avi/.db per repo rules), README with a 10-second GIF, LICENSE, sample demo fixture.

**Phase 1 — Initial clips video (Week 1)**
1. YouTube video → public.
2. **r/QuakeLive** post (draft A below) — the friendliest room; nostalgia angle.
3. **Plus Forward** movie post (draft B below) — same day or next.
4. **ESReality** movie post — link the 2011 thread for the redemption arc.
5. Discord drops (House of Quake media channel, pickup servers) — casual, 2 lines.
6. X thread with 2–3 best clips.

**Phase 2 — Tool release (Week 2–3, after the video has proven interest)**
1. GitHub Release v1.0 (`quake-legacy`): binaries, `pip install`, README embedding the clips video.
2. Follow-up posts on r/QuakeLive + Plus Forward: "the parser that made the video is now open source" — technical angle this time; crosspost r/quake for the engineering audience.
3. ESR forum thread for the old-guard demo hoarders ("you all have folders like this").

**Phase 3 — Presentation/tutorial video (Week 4+)**
1. YouTube: project walkthrough (parser → mining → WolfcamQL capture → render pipeline), using the qlranks archive screenshots as the cold open.
2. Post to r/quake + Plus Forward + link from the GitHub README.
3. Church of Quake / fragmovie curators: submit the movie for reshare.

Rationale for the order: the clips video is the proof-of-quality that makes the tool release credible; the tool release creates the audience that watches the presentation video; each phase gives the previous one a second wave.

---

## 4. Post Drafts

### Draft A — r/QuakeLive (initial clips video)

**Title:** `I kept 13 GB of Quake Live demos from 2010–2013. This year I wrote a parser to mine all 4,292 of them — here are the best CA frags.`

**Body:**

> Back in the pTn days (2010–2013, EU Clan Arena) I recorded everything. The demos sat on a drive for over a decade — 13 GB of `.dm_73` files no modern tool would touch end-to-end.
>
> So I built one: a custom dm_73 parser that reads every snapshot, finds the obituary events, scores the frags (airshots, multikills in a round, rail chains), and drives WolfcamQL to re-capture the best moments at 1080p60. 4,292 demos in, this video out.
>
> [YouTube link]
>
> For the receipts: my old QLRanks CA page survives on the Wayback Machine — peaked at #39 world / 2326 Elo on the Master ladder in 2013 (https://web.archive.org/web/20131028153309/http://www.qlranks.com/ca/player/Tr4sH).
>
> The whole toolchain is going open source in a couple of weeks — if you have a demo folder from back then, you'll be able to point it at yours. Happy to answer anything about the dm_73 format; it fought back.

### Draft B — Plus Forward (movie post)

**Title:** `Tr4sH — Quake Live CA (2010–2013): 13 GB of demos, mined 13 years later`

**Body:**

> In 2011 I posted a CA fragmovie on ESR. It got a 4.5/10 and someone compared the encode to a 1976 VHS. Fair.
>
> The demos never stopped existing, though. This year I wrote a custom `.dm_73` parser and an automated pipeline: it scanned all 4,292 demos from my 2010–2013 pTn Clan Arena years, scored every frag, and re-captured the best of them through WolfcamQL at 1080p60.
>
> ▶ [YouTube link]
>
> Era check, via the Wayback Machine's copies of QLRanks: #39 world CA / 2326 Elo Master in late 2013 (https://web.archive.org/web/*/qlranks.com/ca/player/Tr4sH).
>
> The parser + pipeline goes open source shortly (`pip install quake-legacy`) — anyone with a dm_73 archive will be able to do this to their own folder. Original 2011 thread, for the historians: https://www.esreality.com/post/2174150/tr4sh-fragmovie/

*(Numbers to lock before posting: "4,292 demos mined" is the task-brief figure; repo inventory counts 6,465 dm_73 files on disk — use whichever number the final mining run actually processed, and keep it consistent across posts.)*

---

## 5. Privacy Guardrails for Publishing

- The user publishes his own identity (Tr4sH / pTn / Stoneface) — that's his call and archive-backed.
- Cite only *the user's own* archived rankings. The archived leaderboards contain other players' names/Elo; don't reproduce those tables (the one adjacent name in a snapshot's country table is not to be quoted in posts).
- Videos: opponent names appear in QL's HUD/obituary feed — that's normal fragmovie content, but keep repo screenshots below the HUD line per the existing visual-record rule.
- The GitHub repo continues to ship zero demos, zero player-name strings, statistical analysis only.

---

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
